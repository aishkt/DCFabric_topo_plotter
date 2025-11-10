#!/usr/bin/env python3
"""
UMN EC2 Fabric Topology Generator - Complete Implementation
Generates draw.io topology diagrams from SwitchBuilder brick definition files
"""

import json
import os
import sys
import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class UMNTopologyGenerator:
    """Generate UMN EC2 fabric topology from brick definitions"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.devices = {}
        self.connections = []
        self.grouped_devices = {}
        self.brick_data = None
        
        # Color scheme for device types
        self.colors = {
            'mgmt_cor_root': '#FFE6CC',      # Orange - ROOT DC (bjs11-11)
            'mgmt_cor_inter_az': '#DAE8FC',  # Light Blue - Inter-AZ
            'mgmt_cor_intra_az': '#D5E8D4',  # Light Green - Intra-AZ
            'es_c1': '#F8CECC',              # Light Red - ES-C1 fabric
            'es_e1': '#E1D5E7',              # Light Purple - ES-E1 (OneFabric)
            'es_x1': '#FFF4E6',              # Light Yellow - ES-X1
            'juniper': '#D0D0D0',            # Gray - Juniper devices
            'other': '#FFFFFF'               # White - Other devices
        }
    
    def load_brick_data_from_mcp(self, mcp_content: str):
        """Load brick data from MCP response content"""
        print(f"\n📂 Loading brick data from MCP response")
        
        try:
            # Parse the JSON content
            self.brick_data = json.loads(mcp_content)
            
            device_count = len(self.brick_data.get('DEVICE_DETAILS', {}))
            nodes_count = len(self.brick_data.get('NODES_AND_INTERFACES', {}))
            
            print(f"✓ Loaded {device_count} devices")
            print(f"✓ Loaded {nodes_count} device connectivity entries")
            
            return self.brick_data
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            sys.exit(1)
    
    def parse_devices(self):
        """Parse device details from brick data"""
        print("\n🔍 Parsing device details...")
        
        device_details = self.brick_data.get('DEVICE_DETAILS', {})
        
        for device_name, details in device_details.items():
            self.devices[device_name] = {
                'name': device_name,
                'type': details.get('device_type', 'unknown'),
                'layer': details.get('device_layer', 'unknown'),
                'az': self._extract_az(device_name),
                'dc': self._extract_dc(device_name),
                'fabric': self._extract_fabric(device_name)
            }
        
        print(f"✓ Parsed {len(self.devices)} devices")
        
        # Show device distribution
        az_counts = defaultdict(int)
        for dev in self.devices.values():
            az_counts[dev['az']] += 1
        
        print(f"  AZ distribution: {dict(az_counts)}")
        
        return self.devices
    
    def _extract_az(self, device_name: str) -> str:
        """Extract AZ from device name (e.g., bjs11-11-... -> bjs11)"""
        match = re.match(r'([a-z]+\d+)-', device_name)
        return match.group(1) if match else 'unknown'
    
    def _extract_dc(self, device_name: str) -> str:
        """Extract DC from device name (e.g., bjs11-11-... -> 11)"""
        match = re.match(r'[a-z]+\d+-(\d+)-', device_name)
        return match.group(1) if match else 'unknown'
    
    def _extract_fabric(self, device_name: str) -> str:
        """Extract fabric type from device name (e.g., es-c1, es-e1, es-mgmt)"""
        match = re.search(r'-(es-[a-z0-9]+)-', device_name)
        return match.group(1) if match else 'unknown'
    
    def parse_connections(self):
        """Parse connections from NODES_AND_INTERFACES section"""
        print("\n🔗 Parsing connections...")
        
        nodes_and_interfaces = self.brick_data.get('NODES_AND_INTERFACES', {})
        
        if not nodes_and_interfaces:
            print("⚠️  No NODES_AND_INTERFACES data found")
            return []
        
        raw_connections = []
        
        for source_device, interfaces in nodes_and_interfaces.items():
            for interface_name, interface_data in interfaces.items():
                target_device = interface_data.get('remote_device')
                
                if target_device:
                    raw_connections.append({
                        'source': source_device,
                        'target': target_device,
                        'interface': interface_name,
                        'remote_interface': interface_data.get('remote_device_interface'),
                        'type': interface_data.get('interface_type'),
                        'ip': interface_data.get('local_ip')
                    })
        
        print(f"✓ Found {len(raw_connections)} raw connections")
        
        # Remove duplicates (bidirectional connections)
        self.connections = self._deduplicate_connections(raw_connections)
        
        print(f"✓ After deduplication: {len(self.connections)} unique connections")
        
        return self.connections
    
    def _deduplicate_connections(self, connections: List[Dict]) -> List[Dict]:
        """Remove duplicate bidirectional connections"""
        seen = set()
        unique = []
        
        for conn in connections:
            # Create sorted tuple for deduplication
            key = tuple(sorted([conn['source'], conn['target']]))
            
            if key not in seen:
                seen.add(key)
                unique.append(conn)
        
        return unique
    
    def identify_connection_types(self):
        """Categorize connections as inter-AZ, intra-AZ, or es-c1"""
        print("\n📊 Identifying connection types...")
        
        connection_types = {
            'inter_az': [],
            'intra_az': [],
            'es_c1': [],
            'local': [],
            'other': []
        }
        
        for conn in self.connections:
            src = conn['source']
            tgt = conn['target']
            
            # Check if source device is in our device list
            if src not in self.devices:
                # Target might be external (es-c1, es-e1, etc.)
                if 'es-c1' in tgt:
                    connection_types['es_c1'].append(conn)
                else:
                    connection_types['other'].append(conn)
                continue
            
            # Check if target device is in our device list
            if tgt not in self.devices:
                # Target is external
                if 'es-c1' in tgt:
                    connection_types['es_c1'].append(conn)
                elif 'es-e1' in tgt or 'es-x1' in tgt:
                    connection_types['local'].append(conn)
                else:
                    connection_types['other'].append(conn)
                continue
            
            # Both devices are in our list
            src_az = self.devices[src]['az']
            dst_az = self.devices[tgt]['az']
            src_dc = self.devices[src]['dc']
            dst_dc = self.devices[tgt]['dc']
            
            # Categorize connection
            if src_az != dst_az:
                connection_types['inter_az'].append(conn)
            elif src_dc != dst_dc:
                connection_types['intra_az'].append(conn)
            else:
                connection_types['local'].append(conn)
        
        print(f"✓ Inter-AZ: {len(connection_types['inter_az'])}")
        print(f"✓ Intra-AZ: {len(connection_types['intra_az'])}")
        print(f"✓ ES-C1: {len(connection_types['es_c1'])}")
        print(f"✓ Local: {len(connection_types['local'])}")
        print(f"✓ Other: {len(connection_types['other'])}")
        
        # Save analysis
        analysis_file = os.path.join(self.output_dir, 'analysis', 'connection_types.json')
        with open(analysis_file, 'w') as f:
            json.dump({
                'summary': {k: len(v) for k, v in connection_types.items()},
                'details': connection_types
            }, f, indent=2)
        
        print(f"✓ Saved connection analysis to: {analysis_file}")
        
        return connection_types
    
    def group_devices(self):
        """Group similar devices (e.g., r1 + r2 -> r[12])"""
        print("\n🔄 Grouping devices...")
        
        # Group devices by base name (without r1/r2/v1/v2 suffix)
        device_groups = defaultdict(list)
        
        for device_name in self.devices.keys():
            # Extract base name (remove -r1, -r2, -v1, -v2 suffix)
            base_match = re.match(r'(.+)-([rv]\d+)$', device_name)
            if base_match:
                base_name = base_match.group(1)
                suffix = base_match.group(2)
                device_groups[base_name].append((device_name, suffix))
            else:
                # Device doesn't have a groupable suffix
                device_groups[device_name].append((device_name, ''))
        
        # Create grouped device names
        for base_name, devices in device_groups.items():
            if len(devices) > 1:
                # Sort devices by suffix
                devices.sort(key=lambda x: x[1])
                suffixes = [d[1] for d in devices]
                
                # Create grouped name (e.g., r[12], v[12])
                if all(s.startswith('r') for s in suffixes):
                    numbers = ''.join([s[1:] for s in suffixes])
                    grouped_suffix = f"r[{numbers}]"
                elif all(s.startswith('v') for s in suffixes):
                    numbers = ''.join([s[1:] for s in suffixes])
                    grouped_suffix = f"v[{numbers}]"
                else:
                    grouped_suffix = f"[{','.join(suffixes)}]"
                
                grouped_name = f"{base_name}-{grouped_suffix}"
                self.grouped_devices[grouped_name] = [d[0] for d in devices]
            else:
                # Single device, no grouping needed
                self.grouped_devices[devices[0][0]] = [devices[0][0]]
        
        print(f"✓ Grouped {len(self.devices)} devices into {len(self.grouped_devices)} display nodes")
        
        # Show grouping examples
        grouped_count = sum(1 for members in self.grouped_devices.values() if len(members) > 1)
        print(f"  • {grouped_count} groups created")
        print(f"  • {len(self.grouped_devices) - grouped_count} individual devices")
        
        # Show some examples
        print("\n  Examples:")
        for grouped_name, members in list(self.grouped_devices.items())[:5]:
            if len(members) > 1:
                print(f"    • {grouped_name} ← {', '.join(members)}")
        
        return self.grouped_devices
    
    def determine_device_color(self, grouped_name: str, members: List[str]) -> str:
        """Determine color for a device based on its type and location"""
        
        # Check if this is the ROOT DC (bjs11-11)
        if any('bjs11-11' in d for d in members):
            return self.colors['mgmt_cor_root']
        
        # Get device info from first member of the group
        first_member = members[0]
        
        if first_member not in self.devices:
            return self.colors['other']
        
        device_info = self.devices[first_member]
        
        # Check fabric type in device name
        if 'es-c1' in grouped_name:
            return self.colors['es_c1']
        elif 'es-e1' in grouped_name:
            return self.colors['es_e1']
        elif 'es-x1' in grouped_name:
            return self.colors['es_x1']
        
        # Check device type
        if device_info['type'] == 'juniper':
            return self.colors['juniper']
        
        # Check if inter-AZ or intra-AZ based on location
        az = device_info['az']
        dc = device_info['dc']
        
        # Intra-AZ: same AZ as root (bjs11) but different DC
        if az == 'bjs11' and dc != '11':
            return self.colors['mgmt_cor_intra_az']
        
        # Inter-AZ: different AZ from root
        if az != 'bjs11':
            return self.colors['mgmt_cor_inter_az']
        
        return self.colors['other']
    
    def generate_drawio_xml(self, connection_types: Dict):
        """Generate draw.io XML topology with all connections"""
        print("\n🎨 Generating draw.io topology...")
        
        # XML header
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile host="app.diagrams.net" modified="2024-11-04T12:00:00.000Z" agent="UMN Topology Generator" version="1.0">',
            '  <diagram name="BJS11 UMN EC2 Topology" id="topology">',
            '    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="3000" pageHeight="2000" math="0" shadow="0">',
            '      <root>',
            '        <mxCell id="0"/>',
            '        <mxCell id="1" parent="0"/>',
        ]
        
        # Generate device nodes with smart positioning
        cell_id = 2
        device_to_cell = {}
        
        # Position devices by category
        positions = {
            'root': {'x': 1400, 'y': 100},
            'inter_az': {'x': 100, 'y': 400},
            'intra_az': {'x': 1200, 'y': 600},
            'other': {'x': 2400, 'y': 400}
        }
        
        # Separate devices by category
        root_devices = []
        inter_az_devices = []
        intra_az_devices = []
        other_devices = []
        
        for grouped_name, members in self.grouped_devices.items():
            if any('bjs11-11' in d for d in members):
                root_devices.append((grouped_name, members))
            elif any(self.devices.get(m, {}).get('az', '') != 'bjs11' for m in members if m in self.devices):
                inter_az_devices.append((grouped_name, members))
            elif any(self.devices.get(m, {}).get('az', '') == 'bjs11' and self.devices.get(m, {}).get('dc', '') != '11' for m in members if m in self.devices):
                intra_az_devices.append((grouped_name, members))
            else:
                other_devices.append((grouped_name, members))
        
        # Generate nodes for each category
        def add_device_nodes(devices, start_pos, label_prefix=""):
            nonlocal cell_id
            x, y = start_pos['x'], start_pos['y']
            
            for grouped_name, members in devices:
                color = self.determine_device_color(grouped_name, members)
                
                # Create device label
                if members[0] in self.devices:
                    fabric_type = self.devices[members[0]]['fabric']
                    device_type = self.devices[members[0]]['type']
                else:
                    fabric_type = 'unknown'
                    device_type = 'unknown'
                
                label = f'<b>{grouped_name}</b><br/><i>{fabric_type} ({device_type})</i>'
                
                # Add device node
                xml_lines.append(
                    f'        <mxCell id="{cell_id}" value="{label}" '
                    f'style="rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#000000;" '
                    f'vertex="1" parent="1">'
                )
                xml_lines.append(
                    f'          <mxGeometry x="{x}" y="{y}" width="220" height="70" as="geometry"/>'
                )
                xml_lines.append('        </mxCell>')
                
                device_to_cell[grouped_name] = cell_id
                # Also map individual devices to this cell
                for member in members:
                    device_to_cell[member] = cell_id
                
                cell_id += 1
                
                # Update position
                y += 120
                if y > 1800:
                    y = start_pos['y']
                    x += 280
        
        # Add all device categories
        print(f"  • ROOT devices: {len(root_devices)}")
        add_device_nodes(root_devices, positions['root'], "ROOT")
        
        print(f"  • Inter-AZ devices: {len(inter_az_devices)}")
        add_device_nodes(inter_az_devices, positions['inter_az'], "Inter-AZ")
        
        print(f"  • Intra-AZ devices: {len(intra_az_devices)}")
        add_device_nodes(intra_az_devices, positions['intra_az'], "Intra-AZ")
        
        print(f"  • Other devices: {len(other_devices)}")
        add_device_nodes(other_devices, positions['other'], "Other")
        
        print(f"✓ Generated {len(device_to_cell)} device nodes")
        
        # Generate connections
        connection_count = 0
        
        # Only show connections between devices we're displaying
        for conn_type, conns in connection_types.items():
            for conn in conns:
                src = conn['source']
                tgt = conn['target']
                
                # Check if both devices are in our display
                if src in device_to_cell and tgt in device_to_cell:
                    src_cell = device_to_cell[src]
                    tgt_cell = device_to_cell[tgt]
                    
                    # Add connection edge
                    xml_lines.append(
                        f'        <mxCell id="{cell_id}" value="" '
                        f'style="endArrow=none;html=1;strokeColor=#000000;" '
                        f'edge="1" parent="1" source="{src_cell}" target="{tgt_cell}">'
                    )
                    xml_lines.append(
                        f'          <mxGeometry relative="1" as="geometry"/>'
                    )
                    xml_lines.append('        </mxCell>')
                    
                    cell_id += 1
                    connection_count += 1
        
        print(f"✓ Generated {connection_count} connection edges")
        
        # XML footer
        xml_lines.extend([
            '      </root>',
            '    </mxGraphModel>',
            '  </diagram>',
            '</mxfile>'
        ])
        
        return '\n'.join(xml_lines)
    
    def save_topology(self, xml_content: str):
        """Save topology to draw.io file"""
        output_file = os.path.join(self.output_dir, 'bjs11-11-umn-ec2-topology.drawio')
        
        with open(output_file, 'w') as f:
            f.write(xml_content)
        
        print(f"\n✅ Topology saved to: {output_file}")
        return output_file
    
    def run(self, mcp_content: str):
        """Main execution flow"""
        print("=" * 70)
        print("UMN EC2 Fabric Topology Generator")
        print("=" * 70)
        
        # Load and parse data
        self.load_brick_data_from_mcp(mcp_content)
        self.parse_devices()
        self.parse_connections()
        
        # Analyze connections
        connection_types = self.identify_connection_types()
        
        # Group devices
        self.group_devices()
        
        # Generate topology
        xml_content = self.generate_drawio_xml(connection_types)
        output_file = self.save_topology(xml_content)
        
        print("\n" + "=" * 70)
        print("✅ Generation Complete!")
        print("=" * 70)
        print(f"\n📁 Output: {output_file}")
        print(f"🎨 Devices: {len(self.grouped_devices)} grouped nodes")
        print(f"🔗 Connections: {len(self.connections)} unique")
        print(f"\n💡 Open the .drawio file in draw.io to view and edit the topology")

# MCP response content (from the tool output)
MCP_CONTENT = """{
   "BRICK" : "cor",
   "BRICK_CONFIG_DIR" : "device_config_datastore/bjs-es-mgmt-cor-configs",
   "CAT_TYPE" : null,
   "COMPONENT_ATTRIBUTES" : null,
   "CONFIG_COMMIT_ID" : null,
   "DATA_CENTER_NAME" : null,
   "DEVICE_DETAILS" : {
      "bjs11-11-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs11-11-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs11-11-es-mgmt-cor-v1" : {"device_type" : "juniper"},
      "bjs11-50-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs11-50-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs11-51-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs11-51-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs11-52-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs11-52-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs12-12-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs12-12-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs20-20-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs20-20-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs20-70-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs20-70-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs20-73-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs20-73-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs20-74-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs20-74-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs80-80-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "bjs80-80-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "pkx140-140-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "pkx140-140-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "pkx140-141-es-mgmt-cor-r1" : {"device_layer" : "mgmt_core", "device_type" : "almach"},
      "pkx140-141-es-mgmt-cor-r2" : {"device_layer" : "mgmt_core", "device_type" : "almach"}
   },
   "FABRIC" : "bjs-es-mgmt",
   "TYPE" : "L3_AGG_UMN",
   "NODES_AND_INTERFACES" : {}
}"""

def main():
    """Main entry point"""
    output_dir = '/Users/anishkt/bjs11-11-umn-ec2-topology'
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'analysis'), exist_ok=True)
    
    # Run generator
    generator = UMNTopologyGenerator(output_dir)
    generator.run(MCP_CONTENT)

if __name__ == '__main__':
    main()