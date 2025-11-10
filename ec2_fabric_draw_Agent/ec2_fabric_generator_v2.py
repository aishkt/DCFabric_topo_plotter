#!/usr/bin/env python3
"""
EC2 Fabric Topology Generator V2 - Simplified
Generates EC2 fabric topology from just the ROOT YAML file

Key Improvements:
- Works with ONLY the ROOT YAML (no neighbor fetching required)
- Extracts all connections from ROOT bricks section
- Discovers all BFC/OneFabric neighbors from ROOT neighbors section
- Generates complete topology in one pass
- Saves everything to output directory (no Desktop files)

Usage:
    python3 ec2_fabric_generator_v2.py --site nrt12-12 --fabric es-c1 --yaml-content <yaml_string>
    
Or with MCP tool integration:
    1. Fetch ROOT YAML using MCP tool
    2. Pass content to this script
    3. Get complete topology
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Color scheme
COLORS = {
    'root': '#FFE6CC',           # ROOT DC (Orange)
    'bfc-inter-az': '#DAE8FC',   # BFC Inter-AZ (Light Blue)
    'bfc-intra-az': '#D5E8D4',   # BFC Intra-AZ (Light Green)
    'onefabric': '#E1D5E7',      # OneFabric (Light Purple)
}

class EC2TopologyGeneratorV2:
    """Simplified EC2 fabric topology generator - ROOT YAML only"""
    
    def __init__(self, site: str, fabric: str, yaml_content: str):
        self.site = site
        self.fabric = fabric
        self.root_az = self.extract_az(site)
        self.root_name = f"{site}-{fabric}"
        
        # Parse YAML content (assuming it's already converted to dict/JSON)
        if isinstance(yaml_content, str):
            try:
                import yaml
                self.yaml_data = yaml.safe_load(yaml_content)
            except ImportError:
                # If PyYAML not available, assume JSON string
                self.yaml_data = json.loads(yaml_content)
        else:
            self.yaml_data = yaml_content
        
        # Create output directory
        self.output_dir = Path.home() / f"{site}-{fabric}-topology"
        self.output_dir.mkdir(exist_ok=True)
        
        # Data storage
        self.devices = {}
        self.connections = set()
    
    def extract_az(self, site: str) -> str:
        """Extract AZ from site (e.g., 'nrt12-12' -> 'nrt12')"""
        match = re.match(r'^([a-z]+\d+)', site)
        return match.group(1) if match else ""
    
    def normalize_device_name(self, name: str) -> str:
        """Remove brick suffix: nrt12-56-es-c1-b4 -> nrt12-56-es-c1"""
        return re.sub(r'-b\d+$', '', name)
    
    def categorize_device(self, device_name: str, device_type: str) -> Dict:
        """Categorize device by type and location"""
        if device_name == self.root_name:
            return {
                'category': 'root',
                'role': 'ROOT DC',
                'color': COLORS['root'],
                'type': device_type
            }
        
        device_az = self.extract_az(device_name)
        
        if device_type == 'bfc':
            if device_az == self.root_az:
                return {
                    'category': 'bfc-intra-az',
                    'role': 'BFC Intra-AZ',
                    'color': COLORS['bfc-intra-az'],
                    'type': device_type
                }
            else:
                return {
                    'category': 'bfc-inter-az',
                    'role': 'BFC Inter-AZ',
                    'color': COLORS['bfc-inter-az'],
                    'type': device_type
                }
        elif device_type == 'onefabric':
            return {
                'category': 'onefabric',
                'role': 'OneFabric',
                'color': COLORS['onefabric'],
                'type': device_type
            }
        
        return {
            'category': 'unknown',
            'role': device_type.upper(),
            'color': '#FFFFFF',
            'type': device_type
        }
    
    def discover_neighbors(self) -> Dict[str, str]:
        """
        Discover BFC and OneFabric neighbors from ROOT YAML
        Returns dict of {normalized_name: device_type}
        """
        print(f"\n🔍 Discovering BFC/OneFabric neighbors from ROOT...")
        
        neighbors_dict = {}
        neighbors_section = self.yaml_data.get('neighbors', {})
        
        for neighbor_name, neighbor_data in neighbors_section.items():
            neighbor_type = neighbor_data.get('type', '')
            
            # Include BFC and OneFabric only
            if neighbor_type in ['bfc', 'onefabric']:
                normalized = self.normalize_device_name(neighbor_name)
                neighbors_dict[normalized] = neighbor_type
                print(f"  ✓ {normalized} ({neighbor_type})")
        
        print(f"\n✓ Found {len(neighbors_dict)} BFC/OneFabric neighbors")
        return neighbors_dict
    
    def extract_connections(self) -> Set[Tuple[str, str]]:
        """
        Extract all connections from ROOT bricks section
        Returns set of (source, dest) tuples
        """
        print(f"\n🔗 Extracting connections from ROOT bricks...")
        
        connections = set()
        bricks = self.yaml_data.get('bricks', {})
        
        for brick_id, brick_data in bricks.items():
            if 'neighbors' not in brick_data:
                continue
            
            for neighbor_name in brick_data['neighbors'].keys():
                normalized_neighbor = self.normalize_device_name(neighbor_name)
                
                # Create bidirectional connection key (sorted tuple)
                conn_key = tuple(sorted([self.root_name, normalized_neighbor]))
                connections.add(conn_key)
        
        print(f"✓ Found {len(connections)} unique connections from ROOT")
        return connections
    
    def build_device_list(self, neighbors: Dict[str, str]):
        """Build complete device list with categorization"""
        print(f"\n📋 Building device list...")
        
        # Add ROOT device
        self.devices[self.root_name] = {
            'category': 'root',
            'role': 'ROOT DC',
            'color': COLORS['root'],
            'type': 'bfc'
        }
        
        # Add all neighbors
        for device_name, device_type in neighbors.items():
            device_info = self.categorize_device(device_name, device_type)
            self.devices[device_name] = device_info
        
        print(f"✓ Total devices: {len(self.devices)}")
        
        # Show breakdown
        for category in ['root', 'bfc-inter-az', 'bfc-intra-az', 'onefabric']:
            count = sum(1 for d in self.devices.values() if d['category'] == category)
            if count > 0:
                print(f"  • {category}: {count}")
    
    def filter_connections(self):
        """Filter connections to only include devices in our device list"""
        print(f"\n🔗 Filtering connections...")
        
        filtered = set()
        for src, dst in self.connections:
            if src in self.devices and dst in self.devices:
                filtered.add((src, dst))
        
        self.connections = filtered
        print(f"✓ Filtered to {len(self.connections)} connections between known devices")
    
    def generate_drawio_xml(self) -> str:
        """Generate draw.io XML topology"""
        print(f"\n🎨 Generating draw.io topology...")
        
        # XML header
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile host="app.diagrams.net" modified="2024-11-10T00:00:00.000Z" agent="EC2 Fabric Generator V2" version="2.0">',
            f'  <diagram name="{self.site.upper()} {self.fabric.upper()} Topology" id="topology">',
            '    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="3000" pageHeight="2000" math="0" shadow="0">',
            '      <root>',
            '        <mxCell id="0"/>',
            '        <mxCell id="1" parent="0"/>',
        ]
        
        # Organize devices by category
        device_layout = {
            'root': [],
            'bfc-inter-az': [],
            'bfc-intra-az': [],
            'onefabric': []
        }
        
        for device_name, device_data in sorted(self.devices.items()):
            category = device_data['category']
            device_layout[category].append((device_name, device_data))
        
        # Generate device nodes with smart positioning
        cell_id = 2
        device_to_cell = {}
        
        # Position devices by category
        positions = {
            'root': {'x': 1400, 'y': 100, 'label': 'ROOT DC'},
            'bfc-inter-az': {'x': 100, 'y': 400, 'label': 'Inter-AZ BFC'},
            'bfc-intra-az': {'x': 1200, 'y': 600, 'label': 'Intra-AZ BFC'},
            'onefabric': {'x': 2400, 'y': 400, 'label': 'OneFabric'}
        }
        
        for category in ['root', 'bfc-inter-az', 'bfc-intra-az', 'onefabric']:
            if not device_layout[category]:
                continue
            
            x, y = positions[category]['x'], positions[category]['y']
            
            for device_name, device_data in device_layout[category]:
                label = f"<b>{device_name}</b><br/><i>{device_data['role']}</i>"
                
                xml_lines.append(
                    f'        <mxCell id="{cell_id}" value="{label}" '
                    f'style="rounded=1;whiteSpace=wrap;html=1;fillColor={device_data["color"]};strokeColor=#000000;strokeWidth=2;fontSize=11;" '
                    f'vertex="1" parent="1">'
                )
                xml_lines.append(
                    f'          <mxGeometry x="{x}" y="{y}" width="240" height="80" as="geometry"/>'
                )
                xml_lines.append('        </mxCell>')
                
                device_to_cell[device_name] = cell_id
                cell_id += 1
                
                y += 120
                if y > 1800:
                    y = positions[category]['y']
                    x += 280
        
        print(f"✓ Generated {len(device_to_cell)} device nodes")
        
        # Generate connections
        connection_count = 0
        for src, dst in sorted(self.connections):
            if src in device_to_cell and dst in device_to_cell:
                src_cell = device_to_cell[src]
                dst_cell = device_to_cell[dst]
                
                xml_lines.append(
                    f'        <mxCell id="{cell_id}" value="" '
                    f'style="endArrow=none;html=1;strokeColor=#666666;strokeWidth=2;" '
                    f'edge="1" parent="1" source="{src_cell}" target="{dst_cell}">'
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
    
    def save_topology(self, xml_content: str) -> Path:
        """Save topology to output directory"""
        output_file = self.output_dir / f'{self.site}-{self.fabric}-topology.drawio'
        
        with open(output_file, 'w') as f:
            f.write(xml_content)
        
        return output_file
    
    def save_analysis(self):
        """Save analysis data for reference"""
        analysis_dir = self.output_dir / 'analysis'
        analysis_dir.mkdir(exist_ok=True)
        
        # Save device list
        devices_file = analysis_dir / 'devices.json'
        with open(devices_file, 'w') as f:
            json.dump(self.devices, f, indent=2)
        
        # Save connections
        connections_file = analysis_dir / 'connections.json'
        with open(connections_file, 'w') as f:
            json.dump({
                'total': len(self.connections),
                'connections': [{'source': src, 'target': dst} for src, dst in sorted(self.connections)]
            }, f, indent=2)
        
        print(f"\n📊 Analysis saved to: {analysis_dir}")
    
    def run(self):
        """Main execution flow"""
        print("=" * 80)
        print(f"EC2 Fabric Topology Generator V2 - {self.site.upper()}")
        print("=" * 80)
        print(f"\n📁 Output directory: {self.output_dir}")
        
        # Step 1: Discover neighbors from ROOT YAML
        neighbors = self.discover_neighbors()
        
        # Step 2: Build device list
        self.build_device_list(neighbors)
        
        # Step 3: Extract connections from ROOT YAML
        self.connections = self.extract_connections()
        
        # Step 4: Filter connections
        self.filter_connections()
        
        # Step 5: Generate topology
        xml_content = self.generate_drawio_xml()
        
        # Step 6: Save topology
        output_file = self.save_topology(xml_content)
        
        # Step 7: Save analysis
        self.save_analysis()
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ Generation Complete!")
        print("=" * 80)
        print(f"\n📁 Topology: {output_file}")
        print(f"🎨 Devices: {len(self.devices)}")
        print(f"🔗 Connections: {len(self.connections)}")
        
        print(f"\n💡 Open the .drawio file in draw.io to view and edit")
        print("=" * 80)
        
        return output_file

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='EC2 Fabric Topology Generator V2 - Simplified',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # With YAML file
  python3 ec2_fabric_generator_v2.py --site nrt12-12 --fabric es-c1 --yaml-file config.yaml
  
  # With JSON file (from MCP tool)
  python3 ec2_fabric_generator_v2.py --site nrt12-12 --fabric es-c1 --json-file config.json
  
  # With inline content
  python3 ec2_fabric_generator_v2.py --site nrt12-12 --fabric es-c1 --yaml-content "$(cat config.yaml)"

Workflow with MCP:
  1. Fetch ROOT YAML:
     use_mcp_tool(server_name="amzn-mcp", tool_name="read_internal_website",
                  url="https://code.amazon.com/.../nrt12-12-es-c1.yaml")
  
  2. Save content to file or pass directly to this script
  
  3. Generate topology - done!
        """
    )
    
    parser.add_argument('--site', required=True,
                       help='Site identifier (e.g., nrt12-12, iad12-12)')
    parser.add_argument('--fabric', required=True,
                       help='Fabric type (e.g., es-c1)')
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--yaml-file',
                            help='Path to YAML configuration file')
    input_group.add_argument('--json-file',
                            help='Path to JSON configuration file')
    input_group.add_argument('--yaml-content',
                            help='YAML content as string')
    
    args = parser.parse_args()
    
    # Load content
    if args.yaml_file:
        with open(args.yaml_file, 'r') as f:
            content = f.read()
    elif args.json_file:
        with open(args.json_file, 'r') as f:
            content = json.load(f)
    else:
        content = args.yaml_content
    
    # Create and run generator
    generator = EC2TopologyGeneratorV2(args.site, args.fabric, content)
    output_file = generator.run()
    
    print(f"\n✅ Success! Topology saved to: {output_file}")
    sys.exit(0)

if __name__ == '__main__':
    main()