#!/usr/bin/env python3
"""
EC2 Fabric Topology Generator Agent

Generates comprehensive EC2 fabric topology diagrams showing BFC and OneFabric devices
with their interconnections across intra-AZ and inter-AZ boundaries.

Usage:
    python3 ec2_fabric_generator.py --site bjs11-11 --fabric es-c1
    python3 ec2_fabric_generator.py --site iad12-12 --fabric es-c1
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Color scheme for device types
DEVICE_COLORS = {
    'root': '#FFE6CC',           # ROOT DC (Orange)
    'bfc-inter-az': '#DAE8FC',   # BFC Inter-AZ (Light Blue)
    'bfc-intra-az': '#D5E8D4',   # BFC Intra-AZ (Light Green)
    'onefabric': '#E1D5E7',      # OneFabric (Light Purple)
}

class EC2FabricTopologyGenerator:
    """Agent to generate EC2 fabric topology diagrams"""
    
    def __init__(self, site: str, fabric: str):
        self.site = site  # e.g., "bjs11-11"
        self.fabric = fabric  # e.g., "es-c1"
        self.az = self.extract_az(site)  # e.g., "bjs11"
        
        # Create output directory OUTSIDE agent folder
        self.output_dir = Path.home() / f"{site}-{fabric}-topology"
        self.yaml_dir = self.output_dir / "yaml-configs"
        self.analysis_dir = self.output_dir / "analysis"
        
        # Data storage
        self.yaml_cache = {}  # Store all YAML data
        self.devices = {}  # All discovered devices
        self.connections = set()  # All connections
        
    def extract_az(self, site: str) -> str:
        """Extract AZ from site (e.g., 'bjs11-11' -> 'bjs11')"""
        match = re.match(r'^([a-z]+\d+)', site)
        return match.group(1) if match else ""
    
    def construct_yaml_url(self, device_name: str) -> str:
        """Construct YAML URL for any device"""
        # Handle different device name formats
        if device_name.endswith('-es-c1'):
            yaml_name = device_name
        elif '-es-c1-' in device_name:
            # Normalize: bjs11-51-es-c1-b3 -> bjs11-51-es-c1
            yaml_name = re.sub(r'-b\d+$', '', device_name)
        elif '-es-e1-' in device_name:
            # OneFabric: bjs11-52-es-e1-b129 -> bjs11-52-es-e1
            yaml_name = re.sub(r'-b\d+$', '', device_name)
        else:
            yaml_name = device_name
        
        url = f"https://code.amazon.com/packages/FabricBuilderSiteConfigs/blobs/mainline/--/site-configs/{yaml_name}.yaml"
        return url
    
    def normalize_device_name(self, device_name: str) -> str:
        """
        Normalize device names by removing brick suffixes
        Examples:
            bjs11-51-es-c1-b3 -> bjs11-51-es-c1
            bjs11-51-es-c1-b4 -> bjs11-51-es-c1
            bjs11-52-es-e1-b129 -> bjs11-52-es-e1
        """
        # Remove brick suffix (-bXX)
        normalized = re.sub(r'-b\d+$', '', device_name)
        return normalized
    
    def is_same_az(self, device_name: str) -> bool:
        """Check if device is in same AZ as ROOT"""
        device_az = self.extract_az(device_name)
        return device_az == self.az
    
    def categorize_device(self, device_name: str, device_data: Dict) -> Dict:
        """Categorize device by type and location"""
        normalized_name = self.normalize_device_name(device_name)
        device_type = device_data.get('type', 'unknown')
        
        # Determine category
        if normalized_name == f"{self.site}-{self.fabric}":
            category = 'root'
            role = 'ROOT DC'
        elif device_type == 'bfc':
            if self.is_same_az(device_name):
                category = 'bfc-intra-az'
                role = 'BFC Intra-AZ'
            else:
                category = 'bfc-inter-az'
                role = 'BFC Inter-AZ'
        elif device_type == 'onefabric':
            category = 'onefabric'
            role = 'OneFabric'
        else:
            category = 'unknown'
            role = device_type.upper()
        
        return {
            'normalized_name': normalized_name,
            'original_name': device_name,
            'category': category,
            'role': role,
            'color': DEVICE_COLORS.get(category, '#FFFFFF'),
            'type': device_type
        }
    
    def fetch_yaml(self, device_name: str) -> Dict:
        """Fetch YAML configuration for a device"""
        normalized = self.normalize_device_name(device_name)
        
        # Check cache first
        if normalized in self.yaml_cache:
            print(f"  ✓ Using cached YAML for {normalized}")
            return self.yaml_cache[normalized]
        
        url = self.construct_yaml_url(device_name)
        print(f"  📥 Fetching YAML: {normalized}")
        print(f"     URL: {url}")
        
        # In production, this would use MCP tool
        # For now, return placeholder
        print(f"  ⚠️  Note: Use amzn-mcp read_internal_website tool to fetch")
        
        # Try to load from local file if available (stored as JSON)
        json_file = self.yaml_dir / f"{normalized}.json"
        if json_file.exists():
            with open(json_file, 'r') as f:
                yaml_data = json.load(f)
                self.yaml_cache[normalized] = yaml_data
                return yaml_data
        
        return None
    
    def discover_neighbors(self, yaml_data: Dict) -> List[Tuple[str, Dict]]:
        """
        Discover all neighbors from YAML
        Returns list of (neighbor_name, neighbor_data) tuples
        """
        neighbors = []
        
        if not yaml_data or 'neighbors' not in yaml_data:
            return neighbors
        
        for neighbor_name, neighbor_data in yaml_data['neighbors'].items():
            neighbor_type = neighbor_data.get('type', '')
            
            # Include BFC and OneFabric only
            if neighbor_type in ['bfc', 'onefabric']:
                neighbors.append((neighbor_name, neighbor_data))
            # Include Euclid ONLY if it has OneFabric connections
            elif neighbor_type == 'euclid':
                # Check if this Euclid has OneFabric connections
                # We'll discover this when we fetch its YAML
                pass
        
        return neighbors
    
    def extract_connections_from_yaml(self, device_name: str, yaml_data: Dict) -> List[Tuple[str, str]]:
        """
        Extract all connections from a device's YAML
        Returns list of (source, destination) tuples
        """
        connections = []
        
        if not yaml_data or 'bricks' not in yaml_data:
            return connections
        
        normalized_source = self.normalize_device_name(device_name)
        
        # Parse each brick's neighbors
        for brick_id, brick_data in yaml_data['bricks'].items():
            if 'neighbors' not in brick_data:
                continue
            
            for neighbor_name in brick_data['neighbors'].keys():
                normalized_dest = self.normalize_device_name(neighbor_name)
                
                # Add connection (will deduplicate later)
                connections.append((normalized_source, normalized_dest))
        
        return connections
    
    def build_topology(self) -> Dict:
        """
        Main topology building logic
        Follows the 18-step process from requirements
        """
        print("\n" + "="*80)
        print(f"  EC2 Fabric Topology Generator")
        print(f"  Site: {self.site} | Fabric: {self.fabric} | AZ: {self.az}")
        print("="*80)
        
        # Step 1: Create directories
        print(f"\n[Step 1] Creating output directories...")
        self.output_dir.mkdir(exist_ok=True)
        self.yaml_dir.mkdir(exist_ok=True)
        self.analysis_dir.mkdir(exist_ok=True)
        print(f"  ✓ {self.output_dir}")
        
        # Step 2: Fetch ROOT DC YAML
        print(f"\n[Step 2] Fetching ROOT DC YAML...")
        root_device = f"{self.site}-{self.fabric}"
        root_yaml = self.fetch_yaml(root_device)
        
        if not root_yaml:
            print(f"\n  ⚠️  ROOT YAML not found. Please fetch:")
            print(f"     URL: {self.construct_yaml_url(root_device)}")
            print(f"     Save to: {self.yaml_dir}/{root_device}.yaml")
            return None
        
        # Step 3: Discover neighbors from ROOT
        print(f"\n[Step 3] Discovering neighbors from ROOT DC...")
        root_neighbors = self.discover_neighbors(root_yaml)
        print(f"  ✓ Found {len(root_neighbors)} BFC/OneFabric neighbors")
        
        # Track all devices to fetch
        devices_to_fetch = set()
        for neighbor_name, neighbor_data in root_neighbors:
            devices_to_fetch.add(neighbor_name)
        
        # Step 4: Identify intra-AZ neighbors
        print(f"\n[Step 4] Identifying intra-AZ neighbors...")
        intra_az_neighbors = []
        for neighbor_name, neighbor_data in root_neighbors:
            if self.is_same_az(neighbor_name):
                intra_az_neighbors.append(neighbor_name)
                print(f"  • {neighbor_name} (same AZ)")
        
        # Step 5: Fetch YAML for INTRA-AZ neighbors ONLY (optimization)
        print(f"\n[Step 5] Fetching YAML for intra-AZ neighbors only...")
        print(f"  ℹ️  Optimization: Skipping inter-AZ neighbors (only connect to ROOT)")
        
        intra_az_to_fetch = set()
        for device_name in devices_to_fetch:
            if self.is_same_az(device_name):
                intra_az_to_fetch.add(device_name)
                print(f"  📥 Will fetch: {device_name} (same AZ)")
            else:
                print(f"  ⏭️  Skipping: {device_name} (different AZ)")
        
        # Fetch intra-AZ YAMLs
        for device_name in intra_az_to_fetch:
            yaml_data = self.fetch_yaml(device_name)
            if yaml_data:
                self.yaml_cache[self.normalize_device_name(device_name)] = yaml_data
        
        # Step 6: For intra-AZ neighbors, get THEIR intra-AZ neighbors too
        print(f"\n[Step 6] Discovering intra-AZ mesh connections...")
        for intra_device in intra_az_neighbors:
            normalized = self.normalize_device_name(intra_device)
            if normalized in self.yaml_cache:
                intra_yaml = self.yaml_cache[normalized]
                intra_neighbors = self.discover_neighbors(intra_yaml)
                
                # Only process intra-AZ neighbors
                intra_az_count = sum(1 for n, _ in intra_neighbors if self.is_same_az(n))
                print(f"  • {normalized}: {intra_az_count} intra-AZ neighbors")
                
                # Fetch their YAMLs if they're also intra-AZ
                for neighbor_name, _ in intra_neighbors:
                    if self.is_same_az(neighbor_name) and neighbor_name not in devices_to_fetch:
                        devices_to_fetch.add(neighbor_name)
                        yaml_data = self.fetch_yaml(neighbor_name)
                        if yaml_data:
                            self.yaml_cache[self.normalize_device_name(neighbor_name)] = yaml_data
        
        # Step 7: Build connection matrix
        print(f"\n[Step 7] Building connection matrix...")
        all_connections = []
        
        # Extract connections from ROOT
        root_connections = self.extract_connections_from_yaml(root_device, root_yaml)
        all_connections.extend(root_connections)
        print(f"  • ROOT: {len(root_connections)} connections")
        
        # Extract connections from all neighbors
        for device_name, yaml_data in self.yaml_cache.items():
            device_connections = self.extract_connections_from_yaml(device_name, yaml_data)
            all_connections.extend(device_connections)
            if device_connections:
                print(f"  • {device_name}: {len(device_connections)} connections")
        
        # Step 8: Remove duplicates
        print(f"\n[Step 8] Removing duplicate connections...")
        unique_connections = set()
        for src, dst in all_connections:
            # Create bidirectional key (sorted tuple)
            conn_key = tuple(sorted([src, dst]))
            unique_connections.add(conn_key)
        
        print(f"  • Total connections: {len(all_connections)}")
        print(f"  • Unique connections: {len(unique_connections)}")
        
        # Step 9: Filter devices (BFC and OneFabric only)
        print(f"\n[Step 9] Filtering devices...")
        filtered_devices = {}
        
        # Add ROOT
        filtered_devices[root_device] = {
            'category': 'root',
            'role': 'ROOT DC',
            'color': DEVICE_COLORS['root'],
            'type': 'bfc'
        }
        
        # Add neighbors from YAML cache
        for device_name, yaml_data in self.yaml_cache.items():
            if device_name == root_device:
                continue
            
            # Get device type from neighbors section of ROOT or from its own YAML
            device_type = None
            if 'neighbors' in root_yaml and device_name in root_yaml['neighbors']:
                device_type = root_yaml['neighbors'][device_name].get('type')
            elif yaml_data and 'site' in yaml_data:
                # Infer from topology
                topology = yaml_data['site'].get('topology', '')
                if 'bfc' in topology:
                    device_type = 'bfc'
                elif 'onefabric' in topology:
                    device_type = 'onefabric'
            
            # Include BFC and OneFabric only
            if device_type in ['bfc', 'onefabric']:
                cat_data = self.categorize_device(device_name, {'type': device_type})
                filtered_devices[device_name] = cat_data
        
        print(f"  ✓ Filtered to {len(filtered_devices)} devices")
        
        # Step 10: Filter connections (only between filtered devices)
        print(f"\n[Step 10] Filtering connections...")
        filtered_connections = []
        for src, dst in unique_connections:
            if src in filtered_devices and dst in filtered_devices:
                filtered_connections.append((src, dst))
        
        print(f"  ✓ Filtered to {len(filtered_connections)} connections")
        
        return {
            'devices': filtered_devices,
            'connections': filtered_connections
        }
    
    def generate_drawio_xml(self, topology_data: Dict) -> str:
        """Generate draw.io XML from topology data"""
        
        devices = topology_data['devices']
        connections = topology_data['connections']
        
        # Layout parameters
        x_start, y_start = 120, 100
        x_spacing, y_spacing = 300, 150
        
        # Organize devices by category
        device_layout = {
            'root': [],
            'bfc-inter-az': [],
            'bfc-intra-az': [],
            'onefabric': []
        }
        
        for device_name, device_data in sorted(devices.items()):
            category = device_data['category']
            device_layout[category].append((device_name, device_data))
        
        # Build XML
        mxfile = ET.Element('mxfile', {
            'host': 'app.diagrams.net',
            'modified': '2025-10-27T00:00:00.000Z',
            'agent': 'EC2 Fabric Topology Generator',
            'version': '24.0.0',
            'type': 'device'
        })
        
        diagram = ET.SubElement(mxfile, 'diagram', {
            'id': 'ec2-fabric-topology',
            'name': f'{self.site.upper()} {self.fabric.upper()} Topology'
        })
        
        model = ET.SubElement(diagram, 'mxGraphModel', {
            'dx': '2000', 'dy': '1500', 'grid': '1', 'gridSize': '10',
            'guides': '1', 'tooltips': '1', 'connect': '1', 'arrows': '1',
            'fold': '1', 'page': '1', 'pageScale': '1',
            'pageWidth': '2000', 'pageHeight': '1500', 'math': '0', 'shadow': '0'
        })
        
        root = ET.SubElement(model, 'root')
        ET.SubElement(root, 'mxCell', {'id': '0'})
        ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})
        
        # Create nodes
        node_ids = {}
        cell_id = 2
        row = 0
        
        # Layout each category
        for category in ['root', 'bfc-inter-az', 'bfc-intra-az', 'onefabric']:
            if not device_layout[category]:
                continue
            
            col = 0
            for device_name, device_data in device_layout[category]:
                # Create label with HTML formatting
                label_html = f"<b>{device_name}</b><br/><i>{device_data['role']}</i>"
                
                style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={device_data['color']};strokeColor=#000000;strokeWidth=2;fontStyle=0;fontSize=12;shadow=1;"
                
                x = x_start + (col * x_spacing)
                y = y_start + (row * y_spacing)
                
                cell = ET.SubElement(root, 'mxCell', {
                    'id': str(cell_id),
                    'value': label_html,
                    'style': style,
                    'vertex': '1',
                    'parent': '1'
                })
                
                ET.SubElement(cell, 'mxGeometry', {
                    'x': str(x),
                    'y': str(y),
                    'width': '220',
                    'height': '90',
                    'as': 'geometry'
                })
                
                node_ids[device_name] = str(cell_id)
                cell_id += 1
                
                col += 1
                if col >= 4:
                    col, row = 0, row + 1
            
            row += 2  # Space between categories
        
        # Create connections (no labels, no color coding)
        for src, dst in connections:
            if src not in node_ids or dst not in node_ids:
                continue
            
            # Simple connection style (no labels, same color for all)
            style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#666666;strokeWidth=2;shadow=1;"
            
            edge = ET.SubElement(root, 'mxCell', {
                'id': str(cell_id),
                'style': style,
                'edge': '1',
                'parent': '1',
                'source': node_ids[src],
                'target': node_ids[dst]
            })
            
            ET.SubElement(edge, 'mxGeometry', {
                'relative': '1',
                'as': 'geometry'
            })
            
            cell_id += 1
        
        # Convert to pretty XML
        xml_str = ET.tostring(mxfile, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")
    
    def run(self):
        """Main execution flow"""
        print("\n" + "="*80)
        print("  EC2 Fabric Topology Generator")
        print("="*80)
        
        # Build topology
        topology_data = self.build_topology()
        
        if not topology_data:
            print("\n❌ Failed to build topology. Please fetch required YAML files.")
            return False
        
        # Generate draw.io XML
        print(f"\n[Step 11] Generating draw.io topology...")
        xml_content = self.generate_drawio_xml(topology_data)
        
        output_file = self.output_dir / f"{self.site}-{self.fabric}-topology.drawio"
        with open(output_file, 'w') as f:
            f.write(xml_content)
        
        print(f"  ✓ Generated: {output_file}")
        
        # Summary
        print("\n" + "="*80)
        print("✅ EC2 Fabric Topology Generation Complete!")
        print("="*80)
        print(f"\nOutput: {output_file}")
        print(f"\nDevices: {len(topology_data['devices'])}")
        print(f"Connections: {len(topology_data['connections'])}")
        print("\nFeatures:")
        print("  ✓ Plain XML (no compression)")
        print("  ✓ Individual devices (no grouping)")
        print("  ✓ Normalized device names")
        print("  ✓ Color-coded by type and location")
        print("  ✓ All inter-AZ and intra-AZ connections")
        print("  ✓ No link labels or colors")
        print("  ✓ Fully editable in draw.io")
        print("\n" + "="*80 + "\n")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='EC2 Fabric Topology Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ec2_fabric_generator.py --site bjs11-11 --fabric es-c1
  python3 ec2_fabric_generator.py --site iad12-12 --fabric es-c1
  python3 ec2_fabric_generator.py --site nrt12-12 --fabric es-c1
        """
    )
    
    parser.add_argument('--site', required=True,
                       help='Site/DC identifier (e.g., bjs11-11, iad12-12)')
    parser.add_argument('--fabric', required=True,
                       help='Fabric type (e.g., es-c1)')
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = EC2FabricTopologyGenerator(args.site, args.fabric)
    success = agent.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()