#!/usr/bin/env python3
"""
Generic UMN PROD Fabric Topology Generator
Generates draw.io topology from SwitchBuilderBrickDef-PROD brick files for any site

Usage:
    python3 umn_prod_topology_generator.py <site>
    
Example:
    python3 umn_prod_topology_generator.py bjs11-11
    python3 umn_prod_topology_generator.py iad12-12
"""

import sys
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
import re

def construct_url(site):
    """Construct brick file URL for UMN PROD"""
    region = site[:3]  # Extract first 3 letters
    REGION = region.upper()
    url = f"https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-{REGION}/blobs/mainline/--/configuration/etc/brick/PROD-{REGION}/{region}-ws-mgmt-cor.brick"
    return url

def parse_brick_content(content, site):
    """
    Parse SwitchBuilder brick JSON and extract devices and connections
    
    Returns:
        devices: List of device names
        connections: List of connection dicts with source, target, type
    """
    try:
        brick_data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        sys.exit(1)
    
    # Extract devices from DEVICE_DETAILS
    device_details = brick_data.get('DEVICE_DETAILS', {})
    all_devices = set(device_details.keys())
    
    # Extract site AZ (e.g., bjs11 from bjs11-11)
    site_az = site.split('-')[0] + '-' + site.split('-')[1]  # bjs11-11 → bjs11
    
    # Filter devices for target site
    # Include: ROOT AZ devices + Inter-AZ devices that connect to ROOT
    devices = set()
    connections = []
    
    # Parse NODES_AND_INTERFACES for connections
    nodes_and_interfaces = brick_data.get('NODES_AND_INTERFACES', {})
    
    # First pass: identify all devices that connect to ROOT AZ
    connected_devices = set()
    for source_device, interfaces in nodes_and_interfaces.items():
        for interface_name, interface_data in interfaces.items():
            target_device = interface_data.get('remote_device')
            if target_device:
                # Check if either source or target is in ROOT AZ
                if source_device.startswith(site_az) or target_device.startswith(site_az):
                    connected_devices.add(source_device)
                    connected_devices.add(target_device)
                    
                    connections.append({
                        'source': source_device,
                        'target': target_device,
                        'type': 'physical'
                    })
    
    # Include devices from ROOT AZ and connected devices
    devices = connected_devices & all_devices
    
    return list(devices), connections

def group_devices(devices):
    """Group device pairs (r1+r2 -> r[12], keep v1 separate for ROOT)"""
    device_groups = defaultdict(list)
    
    for device in devices:
        # Check if device ends with -rN or -vN pattern
        match = re.match(r'(.+)-([rv])(\d+)$', device)
        if match:
            base = match.group(1)
            suffix_type = match.group(2)  # 'r' or 'v'
            suffix_num = match.group(3)
            device_groups[base].append((device, suffix_type, suffix_num))
        else:
            # Single device (no grouping)
            device_groups[device] = [(device, None, None)]
    
    # Create grouped device names
    grouped_devices = {}
    for base, members in device_groups.items():
        if len(members) > 1:
            # Sort by suffix type and number
            members.sort(key=lambda x: (x[1], x[2]))
            
            # Group by suffix type (r or v)
            r_devices = [m for m in members if m[1] == 'r']
            v_devices = [m for m in members if m[1] == 'v']
            
            # Group r devices
            if len(r_devices) > 1:
                nums = ''.join([m[2] for m in r_devices])
                grouped_name = f"{base}-r[{nums}]"
                for member, _, _ in r_devices:
                    grouped_devices[member] = grouped_name
            elif len(r_devices) == 1:
                grouped_devices[r_devices[0][0]] = r_devices[0][0]
            
            # Keep v devices separate (don't group)
            for member, _, _ in v_devices:
                grouped_devices[member] = member
        else:
            # Single device
            grouped_devices[members[0][0]] = members[0][0]
    
    return grouped_devices

def deduplicate_connections(connections, device_groups):
    """Remove duplicate connections after grouping"""
    unique_connections = {}
    
    for conn in connections:
        src = device_groups.get(conn['source'], conn['source'])
        tgt = device_groups.get(conn['target'], conn['target'])
        
        # Skip self-connections
        if src == tgt:
            continue
        
        # Create a normalized key (alphabetically sorted)
        key = tuple(sorted([src, tgt]))
        
        if key not in unique_connections:
            unique_connections[key] = {
                'source': src,
                'target': tgt,
                'type': conn['type']
            }
    
    return list(unique_connections.values())

def get_device_color(device_name, site):
    """Determine device color based on type and location"""
    site_az = site.split('-')[0] + '-' + site.split('-')[1]  # bjs11-11 → bjs11
    site_dc = site.split('-')[1]  # bjs11-11 → 11
    
    # ROOT DC (the site we're analyzing)
    if device_name.startswith(f"{site}-ws-mgmt-cor"):
        return '#FFE6CC'  # Orange for root
    
    # Extract device AZ and DC
    match = re.match(r'([a-z]+\d+)-(\d+)-', device_name)
    if match:
        device_az = match.group(1)
        device_dc = match.group(2)
        
        # Intra-AZ (same AZ, different DC)
        if device_az == site_az and device_dc != site_dc:
            return '#D5E8D4'  # Light green
        
        # Inter-AZ (different AZ)
        if device_az != site_az:
            return '#DAE8FC'  # Light blue
    
    # Juniper devices
    if '-v1' in device_name or '-v2' in device_name:
        return '#D0D0D0'  # Gray
    
    return '#FFFFFF'  # White for other

def get_connection_color(conn_type):
    """Determine connection color based on type"""
    return '#000000'  # Black for all connections

def generate_drawio_xml(devices, connections, site):
    """Generate draw.io XML topology"""
    
    # Create XML structure
    mxfile = ET.Element('mxfile', host="app.diagrams.net", type="device")
    diagram = ET.SubElement(mxfile, 'diagram', 
                           id="umn-prod-topology",
                           name=f"{site.upper()} UMN PROD Topology")
    mxGraphModel = ET.SubElement(diagram, 'mxGraphModel',
                                 dx="1422", dy="794",
                                 grid="1", gridSize="10",
                                 guides="1", tooltips="1",
                                 connect="1", arrows="1",
                                 fold="1", page="1",
                                 pageScale="1", pageWidth="850",
                                 pageHeight="1100", math="0",
                                 shadow="0")
    root = ET.SubElement(mxGraphModel, 'root')
    
    # Add required parent cells
    ET.SubElement(root, 'mxCell', id="0")
    ET.SubElement(root, 'mxCell', id="1", parent="0")
    
    # Create device cells
    device_cells = {}
    x_pos = 100
    y_pos = 100
    cell_id = 2
    
    unique_devices = sorted(set(devices))
    
    for device in unique_devices:
        color = get_device_color(device, site)
        
        cell = ET.SubElement(root, 'mxCell',
                           id=str(cell_id),
                           value=device,
                           style=f"rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#000000;",
                           vertex="1",
                           parent="1")
        
        geometry = ET.SubElement(cell, 'mxGeometry',
                                x=str(x_pos),
                                y=str(y_pos),
                                width="200",
                                height="60",
                                **{'as': 'geometry'})
        
        device_cells[device] = str(cell_id)
        cell_id += 1
        
        # Arrange in grid
        x_pos += 250
        if x_pos > 800:
            x_pos = 100
            y_pos += 120
    
    # Create connection cells
    for conn in connections:
        src_id = device_cells.get(conn['source'])
        tgt_id = device_cells.get(conn['target'])
        
        if src_id and tgt_id:
            color = get_connection_color(conn['type'])
            
            cell = ET.SubElement(root, 'mxCell',
                               id=str(cell_id),
                               value="",
                               style=f"endArrow=none;html=1;strokeColor={color};strokeWidth=2;",
                               edge="1",
                               parent="1",
                               source=src_id,
                               target=tgt_id)
            
            geometry = ET.SubElement(cell, 'mxGeometry',
                                   relative="1",
                                   **{'as': 'geometry'})
            
            cell_id += 1
    
    # Convert to string with proper formatting
    xml_str = ET.tostring(mxfile, encoding='unicode')
    
    # Pretty print
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove extra blank lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 umn_prod_topology_generator.py <site>")
        print("Example: python3 umn_prod_topology_generator.py bjs11-11")
        sys.exit(1)
    
    site = sys.argv[1]
    
    print(f"Generating UMN PROD Topology for {site.upper()}")
    print("=" * 70)
    
    # Generate URL
    url = construct_url(site)
    print(f"\nURL: {url}")
    print("\n⚠️  Please fetch the brick file content using amzn-mcp:")
    print(f"    read_internal_website tool with URL: {url}")
    print("\nThen paste the JSON content below and press Ctrl+D:")
    print("-" * 70)
    
    # Read brick content from stdin
    brick_content = sys.stdin.read()
    
    if not brick_content.strip():
        print("\n❌ Error: No content provided")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    
    # Parse the brick content
    devices, connections = parse_brick_content(brick_content, site)
    
    print(f"\nFound {len(devices)} devices")
    print(f"Found {len(connections)} connections")
    
    # Group devices
    device_groups = group_devices(devices)
    grouped_device_names = sorted(set(device_groups.values()))
    
    print(f"\nAfter grouping: {len(grouped_device_names)} unique devices")
    
    # Show grouping examples
    group_examples = {}
    for orig, grouped in device_groups.items():
        if grouped not in group_examples:
            group_examples[grouped] = []
        group_examples[grouped].append(orig)
    
    print("\nGrouping examples:")
    for grouped, members in sorted(group_examples.items())[:5]:
        if len(members) > 1:
            print(f"  • {grouped} ← {', '.join(sorted(members))}")
    
    # Deduplicate connections
    unique_connections = deduplicate_connections(connections, device_groups)
    
    print(f"\nAfter deduplication: {len(unique_connections)} unique connections")
    
    # Generate XML
    xml_content = generate_drawio_xml(grouped_device_names, unique_connections, site)
    
    # Write to file (save to Desktop, outside project folder)
    import os
    desktop_path = os.path.expanduser("~/Desktop")
    output_file = os.path.join(desktop_path, f"{site}_umn_prod_topology.drawio")
    with open(output_file, 'w') as f:
        f.write(xml_content)
    
    print(f"\n✓ Topology saved to: {output_file}")
    print("\nDevice Summary:")
    print(f"  - Total devices: {len(devices)}")
    print(f"  - Grouped display nodes: {len(grouped_device_names)}")
    print(f"  - Connections: {len(unique_connections)}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()