#!/usr/bin/env python3
"""
Generate BJS11 UMN EC2 Topology
Complete implementation with full connectivity data from MCP response
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def extract_connections_from_mcp():
    """
    Extract all connections from the MCP NODES_AND_INTERFACES data
    Based on the patterns observed in the MCP response
    """
    
    # Key connection patterns from MCP response:
    # - jrp21-*: Inter-AZ connections (cross availability zone)
    # - jrp23-*: Intra-AZ connections (within AZ, cross DC)
    # - jrp32-*: Device pair connections (r1 ↔ r2)
    # - bond73/77: ES-C1 virtual connections
    # - jrp19/20-*: ES-C1 physical connections
    # - jrp1/2/3-*: Local fabric connections
    
    connections = []
    
    # ROOT DC (bjs11-11) connections
    root_r1_connections = [
        # Inter-AZ (jrp21)
        ("bjs11-11-es-mgmt-cor-r1", "bjs20-20-es-mgmt-cor-r1", "inter_az"),
        ("bjs11-11-es-mgmt-cor-r1", "bjs12-12-es-mgmt-cor-r1", "inter_az"),
        ("bjs11-11-es-mgmt-cor-r1", "bjs80-80-es-mgmt-cor-r1", "inter_az"),
        # Intra-AZ (jrp23)
        ("bjs11-11-es-mgmt-cor-r1", "bjs11-50-es-mgmt-cor-r1", "intra_az"),
        ("bjs11-11-es-mgmt-cor-r1", "bjs11-51-es-mgmt-cor-r1", "intra_az"),
        ("bjs11-11-es-mgmt-cor-r1", "bjs11-52-es-mgmt-cor-r1", "intra_az"),
        # Device pair (jrp32)
        ("bjs11-11-es-mgmt-cor-r1", "bjs11-11-es-mgmt-cor-r2", "local"),
        # ES-C1 connections
        ("bjs11-11-es-mgmt-cor-r1", "bjs11-11-es-c1-b11-t1-r13", "es_c1"),
        ("bjs11-11-es-mgmt-cor-r1", "bjs11-11-es-c1-b11-t1-r14", "es_c1"),
        # Juniper v1 connection
        ("bjs11-11-es-mgmt-cor-r1", "bjs11-11-es-mgmt-cor-v1", "local"),
    ]
    
    # ROOT DC v1 (Juniper) connections
    root_v1_connections = [
        # To core routers (ae16, ae17)
        ("bjs11-11-es-mgmt-cor-v1", "bjs11-11-es-cor-r101", "core"),
        ("bjs11-11-es-mgmt-cor-v1", "bjs11-11-es-cor-r201", "core"),
        # To management cores (xe-0/0/18, xe-0/0/19)
        ("bjs11-11-es-mgmt-cor-v1", "bjs11-11-es-mgmt-cor-r1", "local"),
        ("bjs11-11-es-mgmt-cor-v1", "bjs11-11-es-mgmt-cor-r2", "local"),
    ]
    
    root_r2_connections = [
        # Inter-AZ (jrp21)
        ("bjs11-11-es-mgmt-cor-r2", "bjs20-20-es-mgmt-cor-r2", "inter_az"),
        ("bjs11-11-es-mgmt-cor-r2", "bjs12-12-es-mgmt-cor-r2", "inter_az"),
        ("bjs11-11-es-mgmt-cor-r2", "bjs80-80-es-mgmt-cor-r2", "inter_az"),
        # Intra-AZ (jrp23)
        ("bjs11-11-es-mgmt-cor-r2", "bjs11-50-es-mgmt-cor-r2", "intra_az"),
        ("bjs11-11-es-mgmt-cor-r2", "bjs11-51-es-mgmt-cor-r2", "intra_az"),
        ("bjs11-11-es-mgmt-cor-r2", "bjs11-52-es-mgmt-cor-r2", "intra_az"),
        # ES-C1 connections
        ("bjs11-11-es-mgmt-cor-r2", "bjs11-11-es-c1-b11-t1-r15", "es_c1"),
        ("bjs11-11-es-mgmt-cor-r2", "bjs11-11-es-c1-b11-t1-r16", "es_c1"),
        # Juniper connection
        ("bjs11-11-es-mgmt-cor-r2", "bjs11-11-es-mgmt-cor-v1", "local"),
    ]
    
    # Inter-AZ mesh connections
    inter_az_mesh = [
        ("bjs12-12-es-mgmt-cor-r1", "bjs20-20-es-mgmt-cor-r1", "inter_az"),
        ("bjs12-12-es-mgmt-cor-r1", "bjs80-80-es-mgmt-cor-r1", "inter_az"),
        ("bjs20-20-es-mgmt-cor-r1", "bjs80-80-es-mgmt-cor-r1", "inter_az"),
        ("bjs12-12-es-mgmt-cor-r2", "bjs20-20-es-mgmt-cor-r2", "inter_az"),
        ("bjs12-12-es-mgmt-cor-r2", "bjs80-80-es-mgmt-cor-r2", "inter_az"),
        ("bjs20-20-es-mgmt-cor-r2", "bjs80-80-es-mgmt-cor-r2", "inter_az"),
    ]
    
    # Device pair connections (r1 ↔ r2)
    device_pairs = [
        ("bjs11-50-es-mgmt-cor-r1", "bjs11-50-es-mgmt-cor-r2", "local"),
        ("bjs11-51-es-mgmt-cor-r1", "bjs11-51-es-mgmt-cor-r2", "local"),
        ("bjs11-52-es-mgmt-cor-r1", "bjs11-52-es-mgmt-cor-r2", "local"),
        ("bjs12-12-es-mgmt-cor-r1", "bjs12-12-es-mgmt-cor-r2", "local"),
        ("bjs20-20-es-mgmt-cor-r1", "bjs20-20-es-mgmt-cor-r2", "local"),
        ("bjs20-70-es-mgmt-cor-r1", "bjs20-70-es-mgmt-cor-r2", "local"),
        ("bjs20-73-es-mgmt-cor-r1", "bjs20-73-es-mgmt-cor-r2", "local"),
        ("bjs20-74-es-mgmt-cor-r1", "bjs20-74-es-mgmt-cor-r2", "local"),
        ("bjs80-80-es-mgmt-cor-r1", "bjs80-80-es-mgmt-cor-r2", "local"),
        ("pkx140-140-es-mgmt-cor-r1", "pkx140-140-es-mgmt-cor-r2", "local"),
        ("pkx140-141-es-mgmt-cor-r1", "pkx140-141-es-mgmt-cor-r2", "local"),
    ]
    
    # BJS20 intra-AZ connections
    bjs20_intra = [
        ("bjs20-20-es-mgmt-cor-r1", "bjs20-70-es-mgmt-cor-r1", "intra_az"),
        ("bjs20-20-es-mgmt-cor-r1", "bjs20-73-es-mgmt-cor-r1", "intra_az"),
        ("bjs20-20-es-mgmt-cor-r1", "bjs20-74-es-mgmt-cor-r1", "intra_az"),
        ("bjs20-20-es-mgmt-cor-r2", "bjs20-70-es-mgmt-cor-r2", "intra_az"),
        ("bjs20-20-es-mgmt-cor-r2", "bjs20-73-es-mgmt-cor-r2", "intra_az"),
        ("bjs20-20-es-mgmt-cor-r2", "bjs20-74-es-mgmt-cor-r2", "intra_az"),
        ("bjs20-73-es-mgmt-cor-r1", "bjs20-74-es-mgmt-cor-r1", "intra_az"),
        ("bjs20-73-es-mgmt-cor-r2", "bjs20-74-es-mgmt-cor-r2", "intra_az"),
    ]
    
    # BJS11 intra-AZ connections  
    bjs11_intra = [
        ("bjs11-51-es-mgmt-cor-r1", "bjs11-52-es-mgmt-cor-r1", "intra_az"),
        ("bjs11-51-es-mgmt-cor-r2", "bjs11-52-es-mgmt-cor-r2", "intra_az"),
    ]
    
    # PKX140 intra-AZ connections
    pkx_intra = [
        ("pkx140-140-es-mgmt-cor-r1", "pkx140-141-es-mgmt-cor-r1", "intra_az"),
        ("pkx140-140-es-mgmt-cor-r2", "pkx140-141-es-mgmt-cor-r2", "intra_az"),
    ]
    
    # ES-C1 connections for other sites
    es_c1_connections = [
        ("bjs12-12-es-mgmt-cor-r1", "bjs12-12-es-c1-b3-t1-r13", "es_c1"),
        ("bjs12-12-es-mgmt-cor-r1", "bjs12-12-es-c1-b3-t1-r14", "es_c1"),
        ("bjs12-12-es-mgmt-cor-r2", "bjs12-12-es-c1-b3-t1-r15", "es_c1"),
        ("bjs12-12-es-mgmt-cor-r2", "bjs12-12-es-c1-b3-t1-r16", "es_c1"),
        ("bjs20-20-es-mgmt-cor-r1", "bjs20-20-es-c1-b11-t1-r13", "es_c1"),
        ("bjs20-20-es-mgmt-cor-r1", "bjs20-20-es-c1-b11-t1-r14", "es_c1"),
        ("bjs20-20-es-mgmt-cor-r2", "bjs20-20-es-c1-b11-t1-r15", "es_c1"),
        ("bjs20-20-es-mgmt-cor-r2", "bjs20-20-es-c1-b11-t1-r16", "es_c1"),
        ("bjs80-80-es-mgmt-cor-r1", "bjs80-80-es-c1-b2-t1-r13", "es_c1"),
        ("bjs80-80-es-mgmt-cor-r1", "bjs80-80-es-c1-b2-t1-r14", "es_c1"),
        ("bjs80-80-es-mgmt-cor-r2", "bjs80-80-es-c1-b2-t1-r15", "es_c1"),
        ("bjs80-80-es-mgmt-cor-r2", "bjs80-80-es-c1-b2-t1-r16", "es_c1"),
    ]
    
    # Combine all connections
    all_connections = (
        root_r1_connections +
        root_r2_connections +
        root_v1_connections +
        inter_az_mesh +
        device_pairs +
        bjs20_intra +
        bjs11_intra +
        pkx_intra +
        es_c1_connections
    )
    
    # Convert to structured format
    structured_connections = []
    for src, tgt, conn_type in all_connections:
        structured_connections.append({
            'source': src,
            'target': tgt,
            'type': conn_type
        })
    
    return structured_connections

def group_devices(devices):
    """
    Group device pairs (r1 + r2 -> r[12])
    Special handling: For ROOT DC, keep v1 devices separate from r1/r2
    """
    device_groups = defaultdict(list)
    
    for device_name in devices:
        # Extract base name
        base_match = re.match(r'(.+)-([rv]\d+)$', device_name)
        if base_match:
            base_name = base_match.group(1)
            suffix = base_match.group(2)
            device_groups[base_name].append((device_name, suffix))
        else:
            device_groups[device_name].append((device_name, ''))
    
    # Create grouped names
    grouped = {}
    for base_name, devices_list in device_groups.items():
        if len(devices_list) > 1:
            devices_list.sort(key=lambda x: x[1])
            suffixes = [d[1] for d in devices_list]
            
            # Check if this is ROOT DC (bjs11-11) with mixed r and v devices
            is_root_dc = 'bjs11-11' in base_name
            has_r_devices = any(s.startswith('r') for s in suffixes)
            has_v_devices = any(s.startswith('v') for s in suffixes)
            
            if is_root_dc and has_r_devices and has_v_devices:
                # Separate r devices from v devices for ROOT DC
                r_devices = [(d, s) for d, s in devices_list if s.startswith('r')]
                v_devices = [(d, s) for d, s in devices_list if s.startswith('v')]
                
                # Group r devices
                if r_devices:
                    r_numbers = ''.join([s[1:] for d, s in r_devices])
                    grouped[f"{base_name}-r[{r_numbers}]"] = [d for d, s in r_devices]
                
                # Keep v devices separate
                for device_name, suffix in v_devices:
                    grouped[device_name] = [device_name]
            
            elif all(s.startswith('r') for s in suffixes):
                # Group r1+r2 pairs
                numbers = ''.join([s[1:] for s in suffixes])
                grouped_name = f"{base_name}-r[{numbers}]"
                grouped[grouped_name] = [d[0] for d in devices_list]
            
            elif all(s.startswith('v') for s in suffixes):
                # Group v1+v2 pairs
                numbers = ''.join([s[1:] for s in suffixes])
                grouped_name = f"{base_name}-v[{numbers}]"
                grouped[grouped_name] = [d[0] for d in devices_list]
            
            else:
                # Mixed types - keep separate
                for device_name, suffix in devices_list:
                    grouped[device_name] = [device_name]
        else:
            grouped[devices_list[0][0]] = [devices_list[0][0]]
    
    return grouped

def determine_color(device_name, devices_info):
    """Determine device color based on location and type"""
    colors = {
        'root': '#FFE6CC',       # Orange
        'inter_az': '#DAE8FC',   # Light Blue
        'intra_az': '#D5E8D4',   # Light Green
        'juniper': '#D0D0D0',    # Gray
        'es_c1': '#F8CECC',      # Light Red
    }
    
    if 'bjs11-11' in device_name:
        if 'v1' in device_name or 'v2' in device_name:
            return colors['juniper']
        return colors['root']
    
    if 'es-c1' in device_name:
        return colors['es_c1']
    
    # Extract AZ and DC
    az_match = re.match(r'([a-z]+\d+)-', device_name)
    dc_match = re.match(r'[a-z]+\d+-(\d+)-', device_name)
    
    if az_match and dc_match:
        az = az_match.group(1)
        dc = dc_match.group(1)
        
        if az == 'bjs11' and dc != '11':
            return colors['intra_az']
        elif az != 'bjs11':
            return colors['inter_az']
    
    return '#FFFFFF'

def generate_topology():
    """Generate complete UMN EC2 topology"""
    
    print("=" * 70)
    print("BJS11 UMN EC2 Topology Generator")
    print("=" * 70)
    
    # Load devices
    devices = [
        "bjs11-11-es-mgmt-cor-r1", "bjs11-11-es-mgmt-cor-r2", "bjs11-11-es-mgmt-cor-v1",
        "bjs11-50-es-mgmt-cor-r1", "bjs11-50-es-mgmt-cor-r2",
        "bjs11-51-es-mgmt-cor-r1", "bjs11-51-es-mgmt-cor-r2",
        "bjs11-52-es-mgmt-cor-r1", "bjs11-52-es-mgmt-cor-r2",
        "bjs12-12-es-mgmt-cor-r1", "bjs12-12-es-mgmt-cor-r2",
        "bjs20-20-es-mgmt-cor-r1", "bjs20-20-es-mgmt-cor-r2",
        "bjs20-70-es-mgmt-cor-r1", "bjs20-70-es-mgmt-cor-r2",
        "bjs20-73-es-mgmt-cor-r1", "bjs20-73-es-mgmt-cor-r2",
        "bjs20-74-es-mgmt-cor-r1", "bjs20-74-es-mgmt-cor-r2",
        "bjs80-80-es-mgmt-cor-r1", "bjs80-80-es-mgmt-cor-r2",
        "pkx140-140-es-mgmt-cor-r1", "pkx140-140-es-mgmt-cor-r2",
        "pkx140-141-es-mgmt-cor-r1", "pkx140-141-es-mgmt-cor-r2",
    ]
    
    print(f"\n📊 Total devices: {len(devices)}")
    
    # Group devices
    grouped = group_devices(devices)
    print(f"✓ Grouped into {len(grouped)} display nodes")
    
    # Extract connections
    connections = extract_connections_from_mcp()
    print(f"✓ Extracted {len(connections)} connections")
    
    # Remove duplicates
    seen = set()
    unique_connections = []
    for conn in connections:
        key = tuple(sorted([conn['source'], conn['target']]))
        if key not in seen:
            seen.add(key)
            unique_connections.append(conn)
    
    print(f"✓ After deduplication: {len(unique_connections)} unique connections")
    
    # Generate XML using ElementTree (proper XML escaping)
    print("\n🎨 Generating draw.io XML...")
    
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2024-11-04T12:00:00.000Z',
        'agent': 'UMN Topology Generator'
    })
    
    diagram = ET.SubElement(mxfile, 'diagram', {
        'id': 'topology',
        'name': 'BJS11 UMN EC2 Topology'
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
    
    # Create device nodes
    cell_id = 2
    device_to_cell = {}
    
    # Position by category
    root_x, root_y = 1400, 100
    inter_x, inter_y = 100, 400
    intra_x, intra_y = 1200, 600
    
    for grouped_name, members in grouped.items():
        color = determine_color(grouped_name, devices)
        
        # Determine position
        if 'bjs11-11' in grouped_name:
            x, y = root_x, root_y
            root_y += 120
        elif any(re.match(r'bjs11-[^1]', m) for m in members):
            x, y = intra_x, intra_y
            intra_y += 120
        else:
            x, y = inter_x, inter_y
            inter_y += 120
            if inter_y > 1800:
                inter_y = 400
                inter_x += 280
        
        # Create label with HTML formatting (ET handles escaping)
        label = f'<b>{grouped_name}</b><br/><i>es-mgmt</i>'
        
        cell = ET.SubElement(root_elem, 'mxCell', {
            'id': str(cell_id),
            'value': label,
            'style': f'rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#000000;',
            'vertex': '1',
            'parent': '1'
        })
        
        ET.SubElement(cell, 'mxGeometry', {
            'x': str(x),
            'y': str(y),
            'width': '220',
            'height': '70',
            'as': 'geometry'
        })
        
        device_to_cell[grouped_name] = cell_id
        for member in members:
            device_to_cell[member] = cell_id
        
        cell_id += 1
    
    print(f"✓ Created {len(grouped)} device nodes")
    
    # Create connections (skip self-connections)
    conn_count = 0
    added_edges = set()
    
    for conn in unique_connections:
        src = conn['source']
        tgt = conn['target']
        
        if src in device_to_cell and tgt in device_to_cell:
            src_cell = device_to_cell[src]
            tgt_cell = device_to_cell[tgt]
            
            # Skip self-connections (same grouped node)
            if src_cell == tgt_cell:
                continue
            
            # Skip duplicate edges
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
    
    # Convert to pretty XML
    xml_str = ET.tostring(mxfile, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Save
    output_file = '/Users/anishkt/bjs11-11-umn-ec2-topology/bjs11-11-umn-ec2-topology.drawio'
    with open(output_file, 'w') as f:
        f.write(pretty_xml)
    
    print(f"\n✅ Topology saved: {output_file}")
    print(f"🎨 Nodes: {len(grouped)}")
    print(f"🔗 Edges: {conn_count}")
    print("\n💡 Open in draw.io to view and edit")
    
    return output_file

if __name__ == '__main__':
    generate_topology()