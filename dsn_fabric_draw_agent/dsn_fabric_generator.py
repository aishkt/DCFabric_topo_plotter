#!/usr/bin/env python3
"""
Generic DSN Fabric Topology Generator
Generates draw.io topology from GenevaBuilderDCNE .attr files for any site

Usage:
    python3 dsn_fabric_generator.py <site>
    
Example:
    python3 dsn_fabric_generator.py bjs11-11
    python3 dsn_fabric_generator.py nrt55-55
"""

import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
import re

def construct_urls(site):
    """Construct URLs with fallback strategy (r3 -> r1 -> r2)"""
    region = site[:3]  # Extract first 3 letters
    urls = [
        # Try r3 first (common for BJS)
        f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r3/dsn.attr",
        
        # Try r1 next (common for NRT)
        f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r1/dsn.attr",
        
        # Try r2 as last resort
        f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r2/dsn.attr"
    ]
    return urls

def parse_dsn_content(content, site):
    """
    Parse DSN .attr file content and extract connections
    
    Extracts:
    - PARENT-CHILD-INTF connections (physical links)
    - IBGP-NEIGH connections (BGP peers)
    """
    devices = set()
    connections = []
    
    # Add the source device (the co-agg-r device)
    source_device = f"{site}-co-agg-r"
    devices.add(source_device)
    
    # Parse PARENT-CHILD-INTF connections
    for line in content.split('\n'):
        line = line.strip()
        if 'DSN PARENT-CHILD-INTF' in line and '<-->' in line:
            # Extract target device from DESC field
            match = re.search(r'<-->\s+([a-z0-9-]+)', line)
            if match:
                target = match.group(1)
                devices.add(target)
                connections.append({
                    'source': source_device,
                    'target': target,
                    'type': 'physical'
                })
    
    # Parse IBGP-NEIGH connections
    for line in content.split('\n'):
        line = line.strip()
        if 'IBGP-NEIGH' in line and 'IP' in line:
            # Extract peer device
            match = re.search(r'IBGP-NEIGH\s+([a-z0-9-]+)', line)
            if match:
                peer = match.group(1)
                devices.add(peer)
                connections.append({
                    'source': source_device,
                    'target': peer,
                    'type': 'bgp'
                })
    
    # Parse SWITCH connections
    for line in content.split('\n'):
        line = line.strip()
        if 'DSN NAME' in line and 'SWITCH INTF' in line and '-->' in line:
            # Extract switch device
            match = re.search(r'-->\s+([a-z0-9-]+)', line)
            if match:
                switch = match.group(1)
                devices.add(switch)
                connections.append({
                    'source': source_device,
                    'target': switch,
                    'type': 'switch'
                })
    
    return list(devices), connections

def group_devices(devices):
    """Group device pairs (r1+r2 -> r[12], r3+r4 -> r[34])"""
    device_groups = defaultdict(list)
    
    for device in devices:
        # Check if device ends with -rN pattern
        match = re.match(r'(.+)-r(\d+)$', device)
        if match:
            base = match.group(1)
            num = match.group(2)
            device_groups[base].append((device, num))
        else:
            # Single device (no grouping)
            device_groups[device] = [(device, None)]
    
    # Create grouped device names
    grouped_devices = {}
    for base, members in device_groups.items():
        if len(members) > 1:
            # Sort by device number
            members.sort(key=lambda x: x[1])
            nums = ''.join([m[1] for m in members])
            grouped_name = f"{base}-r[{nums}]"
            for member, _ in members:
                grouped_devices[member] = grouped_name
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
        key = tuple(sorted([src, tgt])) + (conn['type'],)
        
        if key not in unique_connections:
            unique_connections[key] = {
                'source': src,
                'target': tgt,
                'type': conn['type']
            }
    
    return list(unique_connections.values())

def get_device_color(device_name, site):
    """Determine device color based on type"""
    if device_name == f"{site}-co-agg-r" or f"{site}-co-agg-r[" in device_name:
        return '#FFE6CC'  # Light orange for root device
    elif 'co-agg' in device_name or 'co-cor' in device_name:
        return '#D5E8D4'  # Light green for intra-AZ
    else:
        return '#DAE8FC'  # Light blue for inter-AZ

def get_connection_color(conn_type):
    """Determine connection color based on type"""
    colors = {
        'physical': '#0066CC',    # Blue for physical connections
        'bgp': '#009900',         # Green for BGP
        'switch': '#CC6600'       # Orange for switch connections
    }
    return colors.get(conn_type, '#666666')

def generate_drawio_xml(devices, connections, site):
    """Generate draw.io XML topology"""
    
    # Create XML structure
    mxfile = ET.Element('mxfile', host="app.diagrams.net", type="device")
    diagram = ET.SubElement(mxfile, 'diagram', 
                           id="dsn-topology",
                           name=f"{site.upper()} DSN Topology")
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
                                width="160",
                                height="60",
                                **{'as': 'geometry'})
        
        device_cells[device] = str(cell_id)
        cell_id += 1
        
        # Arrange in grid
        x_pos += 200
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
                               value=conn['type'],
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
        print("Usage: python3 dsn_fabric_generator.py <site>")
        print("Example: python3 dsn_fabric_generator.py bjs11-11")
        sys.exit(1)
    
    site = sys.argv[1]
    
    print(f"Generating DSN Topology for {site.upper()}")
    print("=" * 70)
    
    # Generate URLs with fallback
    urls = construct_urls(site)
    print(f"\nTry these URLs in order (r3 -> r1 -> r2):")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    
    print("\n⚠️  Please fetch the .attr file content using builder-mcp:")
    print("    ReadInternalWebsites tool with one of the URLs above")
    print("    (Try r3 first, then r1, then r2 if needed)")
    print("\nThen paste the content below and press Ctrl+D:")
    print("-" * 70)
    
    # Read .attr content from stdin
    dsn_content = sys.stdin.read()
    
    if not dsn_content.strip():
        print("\n❌ Error: No content provided")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    
    # Parse the DSN content
    devices, connections = parse_dsn_content(dsn_content, site)
    
    print(f"\nFound {len(devices)} devices")
    print(f"Found {len(connections)} connections")
    
    # Group devices
    device_groups = group_devices(devices)
    grouped_device_names = sorted(set(device_groups.values()))
    
    print(f"\nAfter grouping: {len(grouped_device_names)} unique devices")
    
    # Deduplicate connections
    unique_connections = deduplicate_connections(connections, device_groups)
    
    print(f"After deduplication: {len(unique_connections)} unique connections")
    
    # Generate XML
    xml_content = generate_drawio_xml(grouped_device_names, unique_connections, site)
    
    # Write to file (save to Desktop, outside project folder)
    import os
    desktop_path = os.path.expanduser("~/Desktop")
    output_file = os.path.join(desktop_path, f"{site}_dsn_topology.drawio")
    with open(output_file, 'w') as f:
        f.write(xml_content)
    
    print(f"\n✓ Topology saved to: {output_file}")
    print("\nConnection Summary:")
    conn_types = {}
    for conn in unique_connections:
        conn_type = conn['type']
        conn_types[conn_type] = conn_types.get(conn_type, 0) + 1
    
    for conn_type, count in sorted(conn_types.items()):
        print(f"  - {conn_type}: {count}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()