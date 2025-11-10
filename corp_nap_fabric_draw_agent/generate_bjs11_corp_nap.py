#!/usr/bin/env python3
"""
Corp NAP Fabric Topology Generator for BJS11-11
Generates draw.io topology from GenevaBuilderDCNE .attr files
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict

def parse_attr_content(content):
    """
    Parse .attr file content and extract connections
    
    INCLUDES:
    - CUSTOMERLAG (customer connections)
    - RINGLAG (ring connections)
    - Inter-region NAP connections (PEER, FWPEER)
    
    EXCLUDES:
    - IBGPNEIGH (iBGP)
    - EBGPNEIGH (eBGP)
    - RRCLIENTNEIGH (Route reflector)
    """
    devices = set()
    connections = []
    
    # Current device from HOSTNAME
    current_device = None
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('HOSTNAME'):
            current_device = line.split()[1]
            devices.add(current_device)
    
    # Parse CUSTOMERLAG - connections to co-cor and co-agg devices
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('CUSTOMERLAG') and 'DESC' in line:
            parts = line.split()
            customer_device = parts[-1]
            devices.add(customer_device)
            if current_device:
                connections.append({
                    'source': current_device,
                    'target': customer_device,
                    'type': 'customer'
                })
    
    # Parse RINGLAG - ring connections to other np-cor devices
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('RINGLAG') and 'DESC' in line:
            parts = line.split()
            ring_device = parts[-1]
            devices.add(ring_device)
            if current_device:
                connections.append({
                    'source': current_device,
                    'target': ring_device,
                    'type': 'ring'
                })
    
    # Parse inter-region NAP connections (PEER and FWPEER)
    for line in content.split('\n'):
        line = line.strip()
        # Look for PEER keyword (but not IBGPNEIGH, EBGPNEIGH, RRCLIENTNEIGH)
        if 'PEER' in line and not line.startswith(('IBGPNEIGH', 'EBGPNEIGH', 'RRCLIENTNEIGH')):
            parts = line.split()
            if len(parts) >= 3:
                peer_device = parts[-1]
                devices.add(peer_device)
                if current_device:
                    # Determine if it's a firewall or router peer
                    conn_type = 'nap_firewall' if 'FWPEER' in line else 'nap_inter_region'
                    connections.append({
                        'source': current_device,
                        'target': peer_device,
                        'type': conn_type
                    })
    
    return list(devices), connections

def group_devices(devices):
    """Group r101 and r102 devices into r10[12]"""
    device_groups = defaultdict(list)
    
    for device in devices:
        # Extract base name (everything before r101/r102)
        if device.endswith('-r101'):
            base = device[:-5]  # Remove '-r101'
            device_groups[base].append(device)
        elif device.endswith('-r102'):
            base = device[:-5]  # Remove '-r102'
            device_groups[base].append(device)
        elif device.endswith('-r1'):
            # co-cor-r1, co-agg-r1
            base = device[:-3]  # Remove '-r1'
            device_groups[base].append(device)
        elif device.endswith('-r2'):
            # co-agg-r2
            base = device[:-3]  # Remove '-r2'
            device_groups[base].append(device)
        else:
            # Single device (like fw2)
            device_groups[device] = [device]
    
    # Create grouped device names
    grouped_devices = {}
    for base, members in device_groups.items():
        if len(members) == 2:
            # Check if it's r101/r102 or r1/r2
            if any('-r101' in m for m in members):
                grouped_name = f"{base}-r10[12]"
            else:
                grouped_name = f"{base}-r[12]"
            for member in members:
                grouped_devices[member] = grouped_name
        else:
            # Single device
            grouped_devices[members[0]] = members[0]
    
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

def get_device_color(device_name):
    """Determine device color based on type"""
    if 'np-cor' in device_name:
        return '#FFE6CC'  # Light orange for NAP core
    elif 'co-cor' in device_name:
        return '#D5E8D4'  # Light green for corp core
    elif 'co-agg' in device_name:
        return '#DAE8FC'  # Light blue for corp aggregation
    elif 'fw' in device_name:
        return '#F8CECC'  # Light red for firewall
    else:
        return '#E1D5E7'  # Light purple for other

def get_connection_color(conn_type):
    """Determine connection color based on type"""
    colors = {
        'customer': '#0066CC',           # Blue for customer connections
        'ring': '#009900',               # Green for ring
        'nap_inter_region': '#CC0000',   # Red for inter-region
        'nap_firewall': '#CC0000'        # Red for firewall
    }
    return colors.get(conn_type, '#666666')

def generate_drawio_xml(devices, connections, site):
    """Generate draw.io XML topology"""
    
    # Create XML structure
    mxfile = ET.Element('mxfile', host="app.diagrams.net", type="device")
    diagram = ET.SubElement(mxfile, 'diagram', 
                           id="corp-nap-topology",
                           name=f"{site.upper()} Corp NAP Topology")
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
        color = get_device_color(device)
        
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
    site = "bjs11-11"
    
    # Sample .attr content (in real usage, this would be fetched from code.amazon.com)
    attr_content = """TAG DEVICEOS-JUNOS-NPCOR
HOSTNAME bjs11-11-np-cor-r101
PRIMARYIP 10.191.28.4
SYSTEMASN 64998

# customer lags
CUSTOMERLAG ae40 IP 10.191.28.204
CUSTOMERLAG ae40 DESC bjs11-11-co-cor-r1
CUSTOMERLAG ae41 IP 10.191.28.234
CUSTOMERLAG ae41 DESC bjs11-11-co-agg-r1

#RING Lag Interfaces
RINGLAG ae1 METRIC 1000
RINGLAG ae1 IP 10.191.28.153
RINGLAG ae1 DESC bjs10-10-np-cor-r101

RINGLAG ae2 METRIC 1000
RINGLAG ae2 IP 10.191.28.161
RINGLAG ae2 DESC bjs12-12-np-cor-r101

RINGLAG ae3 METRIC 1000
RINGLAG ae3 IP 10.191.28.219
RINGLAG ae3 DESC bjs80-80-np-cor-r101

RINGLAG ae4 METRIC 1000
RINGLAG ae4 IP 10.191.28.103
RINGLAG ae4 DESC bjs20-20-np-cor-r101

RINGLAG ae11 METRIC 10000
RINGLAG ae11 IP 10.191.28.49
RINGLAG ae11 DESC bjs11-51-np-cor-r101

RINGLAG ae12 METRIC 10000
RINGLAG ae12 IP 10.104.43.23
RINGLAG ae12 DESC bjs11-52-np-cor-r101

# NAP CONNECTION BJS AND PEK
NAPBJSPEK PEER pek50-50-np-cor-r101
NAPBJSPEK REMOTEIP 10.104.71.86

NAPBJSPEK FWPEER pek50-50-np-cor-fw2
NAPBJSPEK FWREMOTEIP 10.191.28.246
"""
    
    print(f"Generating Corp NAP Topology for {site.upper()}")
    print("=" * 70)
    
    # Parse the .attr content
    devices, connections = parse_attr_content(attr_content)
    
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
    output_file = os.path.join(desktop_path, f"{site}_corp_nap_topology.drawio")
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