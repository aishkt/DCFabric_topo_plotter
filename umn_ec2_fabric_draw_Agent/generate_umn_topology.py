#!/usr/bin/env python3
"""
Generic UMN EC2 Topology Generator
Works for ANY AWS site - just provide site identifier and MCP brick data
"""

import json
import sys
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict

def extract_az_dc(device_name):
    """Extract AZ and DC from device name"""
    match = re.match(r'([a-z]+\d+)-(\d+)-', device_name)
    if match:
        return match.group(1), match.group(2)
    return None, None

def extract_connections_from_nodes_and_interfaces(nodes_data, root_site):
    """Extract all es-mgmt-cor to es-mgmt-cor connections"""
    connections = []
    
    for source_device, interfaces in nodes_data.items():
        # Only process es-mgmt-cor devices
        if 'es-mgmt-cor' not in source_device:
            continue
            
        for interface_name, interface_data in interfaces.items():
            target_device = interface_data.get('remote_device')
            
            # Only include es-mgmt-cor to es-mgmt-cor connections
            if target_device and 'es-mgmt-cor' in target_device:
                connections.append({
                    'source': source_device,
                    'target': target_device,
                    'interface': interface_name,
                    'type': 'mgmt_core'
                })
    
    return connections

def filter_for_root_az(devices, connections, root_site):
    """Filter to show only ROOT AZ devices and their inter-AZ connections"""
    root_az, root_dc = extract_az_dc(root_site + '-x')
    
    # Devices to include
    included_devices = set()
    
    # 1. Include all devices in ROOT AZ
    for device in devices:
        az, dc = extract_az_dc(device)
        if az == root_az:
            included_devices.add(device)
    
    # 2. Include inter-AZ devices that connect to ROOT AZ
    for conn in connections:
        src_az, _ = extract_az_dc(conn['source'])
        tgt_az, _ = extract_az_dc(conn['target'])
        
        # If one end is in ROOT AZ and other is different AZ
        if src_az == root_az and tgt_az != root_az:
            included_devices.add(conn['target'])
        elif tgt_az == root_az and src_az != root_az:
            included_devices.add(conn['source'])
    
    # Filter connections to only those involving included devices
    filtered_connections = [
        conn for conn in connections
        if conn['source'] in included_devices and conn['target'] in included_devices
    ]
    
    return list(included_devices), filtered_connections

def group_devices(devices, root_site):
    """Group r1+r2 pairs, keep v1 separate for ROOT DC"""
    device_groups = defaultdict(list)
    
    for device_name in devices:
        base_match = re.match(r'(.+)-([rv]\d+)$', device_name)
        if base_match:
            base_name = base_match.group(1)
            suffix = base_match.group(2)
            device_groups[base_name].append((device_name, suffix))
        else:
            device_groups[device_name].append((device_name, ''))
    
    grouped = {}
    for base_name, devices_list in device_groups.items():
        if len(devices_list) > 1:
            devices_list.sort(key=lambda x: x[1])
            suffixes = [d[1] for d in devices_list]
            
            # Check if ROOT DC with mixed r and v
            is_root = root_site in base_name
            has_r = any(s.startswith('r') for s in suffixes)
            has_v = any(s.startswith('v') for s in suffixes)
            
            if is_root and has_r and has_v:
                # Separate r from v for ROOT DC
                r_devices = [(d, s) for d, s in devices_list if s.startswith('r')]
                v_devices = [(d, s) for d, s in devices_list if s.startswith('v')]
                
                if r_devices:
                    r_nums = ''.join([s[1:] for d, s in r_devices])
                    grouped[f"{base_name}-r[{r_nums}]"] = [d for d, s in r_devices]
                
                for device_name, suffix in v_devices:
                    grouped[device_name] = [device_name]
            
            elif all(s.startswith('r') for s in suffixes):
                numbers = ''.join([s[1:] for s in suffixes])
                grouped[f"{base_name}-r[{numbers}]"] = [d[0] for d in devices_list]
            
            else:
                for device_name, suffix in devices_list:
                    grouped[device_name] = [device_name]
        else:
            grouped[devices_list[0][0]] = [devices_list[0][0]]
    
    return grouped

def determine_color(device_name, root_site):
    """Determine device color"""
    colors = {
        'root': '#FFE6CC',
        'intra_az': '#D5E8D4',
        'inter_az': '#DAE8FC',
        'juniper': '#D0D0D0'
    }
    
    if root_site in device_name:
        if 'v1' in device_name or 'v2' in device_name:
            return colors['juniper']
        return colors['root']
    
    root_az, _ = extract_az_dc(root_site + '-x')
    dev_az, _ = extract_az_dc(device_name)
    
    if dev_az == root_az:
        return colors['intra_az']
    else:
        return colors['inter_az']

def generate_topology(brick_data_json, root_site, output_file):
    """Generate topology from brick data"""
    
    print("=" * 70)
    print(f"UMN EC2 Topology Generator - {root_site.upper()}")
    print("=" * 70)
    
    # Parse brick data
    brick_data = json.loads(brick_data_json)
    
    all_devices = list(brick_data['DEVICE_DETAILS'].keys())
    print(f"\n📊 Total devices in brick: {len(all_devices)}")
    
    # Extract connections
    nodes_and_interfaces = brick_data.get('NODES_AND_INTERFACES', {})
    all_connections = extract_connections_from_nodes_and_interfaces(nodes_and_interfaces, root_site)
    print(f"✓ Extracted {len(all_connections)} raw connections")
    
    # Filter for ROOT AZ + inter-AZ
    filtered_devices, filtered_connections = filter_for_root_az(all_devices, all_connections, root_site)
    print(f"✓ Filtered to {len(filtered_devices)} devices (ROOT AZ + inter-AZ)")
    print(f"✓ Filtered to {len(filtered_connections)} connections")
    
    # Remove duplicates
    seen = set()
    unique_connections = []
    for conn in filtered_connections:
        key = tuple(sorted([conn['source'], conn['target']]))
        if key not in seen:
            seen.add(key)
            unique_connections.append(conn)
    
    print(f"✓ After deduplication: {len(unique_connections)} unique connections")
    
    # Group devices
    grouped = group_devices(filtered_devices, root_site)
    print(f"✓ Grouped into {len(grouped)} display nodes")
    
    # Generate XML
    print("\n🎨 Generating draw.io XML...")
    
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2024-11-04T13:00:00.000Z'
    })
    
    diagram = ET.SubElement(mxfile, 'diagram', {
        'id': 'topology',
        'name': f'{root_site.upper()} UMN EC2 Topology'
    })
    
    model = ET.SubElement(diagram, 'mxGraphModel', {
        'dx': '1422', 'dy': '794', 'grid': '1', 'gridSize': '10',
        'guides': '1', 'tooltips': '1', 'connect': '1', 'arrows': '1',
        'fold': '1', 'page': '1', 'pageScale': '1',
        'pageWidth': '3000', 'pageHeight': '2000'
    })
    
    root_elem = ET.SubElement(model, 'root')
    ET.SubElement(root_elem, 'mxCell', {'id': '0'})
    ET.SubElement(root_elem, 'mxCell', {'id': '1', 'parent': '0'})
    
    # Create nodes
    cell_id = 2
    device_to_cell = {}
    
    root_x, root_y = 1400, 100
    intra_x, intra_y = 1200, 600
    inter_x, inter_y = 100, 400
    
    for grouped_name, members in grouped.items():
        color = determine_color(grouped_name, root_site)
        
        # Position
        if root_site in grouped_name:
            x, y = root_x, root_y
            root_y += 120
        elif extract_az_dc(grouped_name)[0] == extract_az_dc(root_site + '-x')[0]:
            x, y = intra_x, intra_y
            intra_y += 120
        else:
            x, y = inter_x, inter_y
            inter_y += 120
            if inter_y > 1800:
                inter_y = 400
                inter_x += 280
        
        label = f'<b>{grouped_name}</b><br/><i>es-mgmt</i>'
        
        cell = ET.SubElement(root_elem, 'mxCell', {
            'id': str(cell_id),
            'value': label,
            'style': f'rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#000000;',
            'vertex': '1',
            'parent': '1'
        })
        
        ET.SubElement(cell, 'mxGeometry', {
            'x': str(x), 'y': str(y),
            'width': '220', 'height': '70',
            'as': 'geometry'
        })
        
        device_to_cell[grouped_name] = cell_id
        for member in members:
            device_to_cell[member] = cell_id
        
        cell_id += 1
    
    print(f"✓ Created {len(grouped)} device nodes")
    
    # Create connections
    conn_count = 0
    added_edges = set()
    
    for conn in unique_connections:
        src = conn['source']
        tgt = conn['target']
        
        if src in device_to_cell and tgt in device_to_cell:
            src_cell = device_to_cell[src]
            tgt_cell = device_to_cell[tgt]
            
            if src_cell == tgt_cell:
                continue
            
            edge_key = tuple(sorted([src_cell, tgt_cell]))
            if edge_key in added_edges:
                continue
            added_edges.add(edge_key)
            
            edge = ET.SubElement(root_elem, 'mxCell', {
                'id': str(cell_id),
                'value': '',
                'style': 'endArrow=none;html=1;strokeColor=#000000;',
                'edge': '1',
                'parent': '1',
                'source': str(src_cell),
                'target': str(tgt_cell)
            })
            
            ET.SubElement(edge, 'mxGeometry', {
                'relative': '1',
                'as': 'geometry'
            })
            
            cell_id += 1
            conn_count += 1
    
    print(f"✓ Created {conn_count} connection edges")
    
    # Save
    xml_str = ET.tostring(mxfile, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    with open(output_file, 'w') as f:
        f.write(pretty_xml)
    
    print(f"\n✅ Topology saved: {output_file}")
    print(f"🎨 Nodes: {len(grouped)}")
    print(f"🔗 Edges: {conn_count}")
    
    return output_file

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 generate_umn_topology.py <site> <brick_data_json_string>")
        print("\nExample:")
        print("  python3 generate_umn_topology.py nrt55-55 '{...brick data...}'")
        sys.exit(1)
    
    root_site = sys.argv[1]
    brick_data_json = sys.argv[2]
    output_file = f"/Users/anishkt/{root_site}-umn-ec2-topology/{root_site}-umn-ec2-topology.drawio"
    
    generate_topology(brick_data_json, root_site, output_file)