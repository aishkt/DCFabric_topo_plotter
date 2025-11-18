#!/usr/bin/env python3
"""
UMN EC2 Fabric Topology Generator
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
    
    def __init__(self, site: str, brick_file: str, output_dir: str):
        self.site = site
        self.brick_file = brick_file
        self.output_dir = output_dir
        self.devices = {}
        self.connections = []
        self.grouped_devices = {}
        
        # Extract ROOT AZ and DC from site
        match = re.match(r'([a-z]+\d+)-(\d+)', site)
        if match:
            self.root_az = match.group(1)
            self.root_dc = match.group(2)
        else:
            raise ValueError(f"Invalid site format: {site}. Expected format: abc12-34")
        
        # Color scheme for device types
        self.colors = {
            'mgmt_cor_root': '#FFE6CC',      # Orange - ROOT DC
            'mgmt_cor_inter_az': '#DAE8FC',  # Light Blue - Inter-AZ
            'mgmt_cor_intra_az': '#D5E8D4',  # Light Green - Intra-AZ
            'es_c1': '#F8CECC',              # Light Red - ES-C1 fabric
            'es_e1': '#E1D5E7',              # Light Purple - ES-E1 (OneFabric)
            'es_x1': '#FFF4E6',              # Light Yellow - ES-X1
            'juniper': '#D0D0D0',            # Gray - Juniper devices
            'other': '#FFFFFF'               # White - Other devices
        }
    
    def load_brick_data(self):
        """Load brick definition from JSON file"""
        print(f"\n📂 Loading brick data from: {self.brick_file}")
        
        with open(self.brick_file, 'r') as f:
            data = json.load(f)
        
        self.brick_data = data
        print(f"✓ Loaded {len(data.get('DEVICE_DETAILS', {}))} devices")
        return data
    
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
        return self.devices
    
    def _extract_az(self, device_name: str) -> str:
        """Extract AZ from device name (e.g., nrt55-62-... -> nrt55)"""
        match = re.match(r'([a-z]+\d+)-', device_name)
        return match.group(1) if match else 'unknown'
    
    def _extract_dc(self, device_name: str) -> str:
        """Extract DC from device name (e.g., nrt55-62-... -> 62)"""
        match = re.match(r'[a-z]+\d+-(\d+)-', device_name)
        return match.group(1) if match else 'unknown'
    
    def _extract_fabric(self, device_name: str) -> str:
        """Extract fabric type from device name (e.g., es-c1, es-e1, es-mgmt)"""
        match = re.search(r'-(es-[a-z0-9]+)-', device_name)
        return match.group(1) if match else 'unknown'
    
    def parse_connections(self):
        """Parse connections from NODES_AND_INTERFACES section"""
        print("\n🔗 Parsing connections...")
        
        # Since we don't have NODES_AND_INTERFACES in the simplified JSON,
        # we'll need to fetch it from the original MCP response
        # For now, let's create a placeholder that will be filled by the full data
        
        print("⚠️  NODES_AND_INTERFACES data needed for connection parsing")
        print("    Please ensure the full brick file includes this section")
        
        return []
    
    def identify_connection_types(self):
        """Categorize connections as inter-AZ, intra-AZ, or es-c1"""
        print("\n📊 Identifying connection types...")
        
        connection_types = {
            'inter_az': [],
            'intra_az': [],
            'es_c1': [],
            'local': []
        }
        
        for conn in self.connections:
            src_az = self.devices[conn['source']]['az']
            dst_az = self.devices[conn['target']]['az']
            src_dc = self.devices[conn['source']]['dc']
            dst_dc = self.devices[conn['target']]['dc']
            
            # Categorize connection
            if 'es-c1' in conn['target'] or 'es-c1' in conn['source']:
                connection_types['es_c1'].append(conn)
            elif src_az != dst_az:
                connection_types['inter_az'].append(conn)
            elif src_dc != dst_dc:
                connection_types['intra_az'].append(conn)
            else:
                connection_types['local'].append(conn)
        
        print(f"✓ Inter-AZ: {len(connection_types['inter_az'])}")
        print(f"✓ Intra-AZ: {len(connection_types['intra_az'])}")
        print(f"✓ ES-C1: {len(connection_types['es_c1'])}")
        print(f"✓ Local: {len(connection_types['local'])}")
        
        return connection_types
    
    def group_devices(self):
        """Group similar devices (e.g., r1 + r2 -> r[12])"""
        print("\n🔄 Grouping devices...")
        
        # Group devices by base name (without r1/r2 suffix)
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
                
                # Create grouped name (e.g., r[12], r[1-2])
                if all(s.startswith('r') for s in suffixes):
                    numbers = [s[1:] for s in suffixes]
                    grouped_suffix = f"r[{''.join(numbers)}]"
                elif all(s.startswith('v') for s in suffixes):
                    numbers = [s[1:] for s in suffixes]
                    grouped_suffix = f"v[{''.join(numbers)}]"
                else:
                    grouped_suffix = f"[{','.join(suffixes)}]"
                
                grouped_name = f"{base_name}-{grouped_suffix}"
                self.grouped_devices[grouped_name] = [d[0] for d in devices]
            else:
                # Single device, no grouping needed
                self.grouped_devices[devices[0][0]] = [devices[0][0]]
        
        print(f"✓ Grouped {len(self.devices)} devices into {len(self.grouped_devices)} display nodes")
        
        # Show some examples
        for grouped_name, members in list(self.grouped_devices.items())[:5]:
            if len(members) > 1:
                print(f"  • {grouped_name} ← {', '.join(members)}")
        
        return self.grouped_devices
    
    def determine_device_color(self, device_name: str, grouped_devices: List[str]) -> str:
        """Determine color for a device based on its type and location"""
        
        # Check if this is the ROOT DC
        root_pattern = f"{self.root_az}-{self.root_dc}"
        if any(root_pattern in d for d in grouped_devices):
            return self.colors['mgmt_cor_root']
        
        # Get device info from first member of the group
        device_info = self.devices[grouped_devices[0]]
        
        # Check fabric type
        if 'es-c1' in device_name:
            return self.colors['es_c1']
        elif 'es-e1' in device_name:
            return self.colors['es_e1']
        elif 'es-x1' in device_name:
            return self.colors['es_x1']
        
        # Check device type
        if device_info['type'] == 'juniper':
            return self.colors['juniper']
        
        # Check if inter-AZ or intra-AZ based on DC
        az = device_info['az']
        dc = device_info['dc']
        
        if az == self.root_az and dc != self.root_dc:
            return self.colors['mgmt_cor_intra_az']
        elif az != self.root_az:
            return self.colors['mgmt_cor_inter_az']
        
        return self.colors['other']
    
    def generate_drawio_xml(self):
        """Generate draw.io XML topology"""
        print("\n🎨 Generating draw.io topology...")
        
        # XML header
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile host="app.diagrams.net" modified="2024-11-04T12:00:00.000Z" agent="UMN Topology Generator" version="1.0">',
            '  <diagram name="UMN EC2 Topology" id="topology">',
            '    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="3000" pageHeight="2000" math="0" shadow="0">',
            '      <root>',
            '        <mxCell id="0"/>',
            '        <mxCell id="1" parent="0"/>',
        ]
        
        # Generate device nodes
        cell_id = 2
        device_positions = {}
        x, y = 100, 100
        
        for grouped_name, members in self.grouped_devices.items():
            color = self.determine_device_color(grouped_name, members)
            
            # Create device label
            fabric_type = self.devices[members[0]]['fabric']
            device_type = self.devices[members[0]]['type']
            label = f'<b>{grouped_name}</b><br/><i>{fabric_type} ({device_type})</i>'
            
            # Add device node
            xml_lines.append(
                f'        <mxCell id="{cell_id}" value="{label}" '
                f'style="rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#000000;" '
                f'vertex="1" parent="1">'
            )
            xml_lines.append(
                f'          <mxGeometry x="{x}" y="{y}" width="200" height="60" as="geometry"/>'
            )
            xml_lines.append('        </mxCell>')
            
            device_positions[grouped_name] = cell_id
            cell_id += 1
            
            # Update position for next device
            x += 250
            if x > 2500:
                x = 100
                y += 150
        
        # Generate connections (placeholder - needs full connectivity data)
        print(f"✓ Generated {len(self.grouped_devices)} device nodes")
        print("⚠️  Connection generation requires NODES_AND_INTERFACES data")
        
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
        output_file = os.path.join(self.output_dir, f'{self.site}-umn-ec2-topology.drawio')
        
        with open(output_file, 'w') as f:
            f.write(xml_content)
        
        print(f"\n✅ Topology saved to: {output_file}")
        return output_file
    
    def run(self):
        """Main execution flow"""
        print("=" * 60)
        print("UMN EC2 Fabric Topology Generator")
        print("=" * 60)
        
        # Load and parse data
        self.load_brick_data()
        self.parse_devices()
        
        # Group devices
        self.group_devices()
        
        # Generate topology
        xml_content = self.generate_drawio_xml()
        output_file = self.save_topology(xml_content)
        
        print("\n" + "=" * 60)
        print("✅ Generation Complete!")
        print("=" * 60)
        print(f"\n📁 Output: {output_file}")
        print(f"🎨 Devices: {len(self.grouped_devices)} grouped nodes")
        print("\n⚠️  Note: Full connectivity requires NODES_AND_INTERFACES data")
        print("    from the complete brick definition file")

def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python3 umn_ec2_topology_generator.py <site> <brick_file> [output_dir]")
        print("\nExample:")
        print("  python3 umn_ec2_topology_generator.py nrt55-62 \\")
        print("    /Users/anishkt/nrt55-62-umn-ec2-topology/brick-configs/nrt-es-mgmt-cor.json \\")
        print("    /Users/anishkt/nrt55-62-umn-ec2-topology")
        sys.exit(1)
    
    site = sys.argv[1]
    brick_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(brick_file)
    
    if not os.path.exists(brick_file):
        print(f"❌ Error: Brick file not found: {brick_file}")
        sys.exit(1)
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Run generator
    generator = UMNTopologyGenerator(site, brick_file, output_dir)
    generator.run()

if __name__ == '__main__':
    main()