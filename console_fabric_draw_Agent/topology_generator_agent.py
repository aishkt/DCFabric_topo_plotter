#!/usr/bin/env python3
"""
Automated Topology Generator Agent

Takes site/DC input, reads brick config from code.amazon.com, and generates draw.io topology

Usage:
    python3 topology_generator_agent.py --site bjs11-11 --fabric es-mgmt-cor
    python3 topology_generator_agent.py --site iad12-12 --fabric es-fnc
"""

import argparse
import json
import re
import sys
import subprocess
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Set, Tuple

# Color scheme for device types
DEVICE_COLORS = {
    'mgmt-cor': '#FFE6CC',      # Management Core (all es-mgmt-cor same color)
    'mgmt-cor-v': '#FFE6CC',    # Virtual Management (same as mgmt-cor)
    'es-cor': '#D5E8D4',        # Edge Services Core
    'fnc-cor': '#D5E8D4',       # FNC Core
    'es-c1': '#DAE8FC',         # BFC (ES-C1)
    'es-mgmt': '#FFF2CC',       # Edge Management
    'es-x1-mgmt': '#F8CECC',    # X1 Management
    'tt-acc': '#E6D0DE',        # Transit Access
    'cv1-agg': '#D0E0E3',       # CV1 Aggregation
    'inter-az': '#E8E8E8'       # Inter-DC
}

class TopologyGeneratorAgent:
    """Agent to automatically generate network topology diagrams"""
    
    def __init__(self, site: str, fabric: str):
        self.site = site  # e.g., "bjs11-11"
        self.fabric = fabric  # e.g., "es-mgmt-cor"
        self.brick_url = None
        self.brick_data = None
        # Create output directory OUTSIDE agent folder
        self.output_dir = Path.home() / f"{site}-{fabric}-topology"
        
    def construct_brick_url(self) -> str:
        """Construct the code.amazon.com URL for the brick file"""
        # Extract region from site (e.g., "bjs" from "bjs11-11")
        region = re.match(r'^([a-z]+)', self.site).group(1).upper()
        location = region.lower()  # bjs, nrt, iad
        
        # Construct URL - brick file is region-specific, not site-specific
        package = f"SwitchBuilderBrickDef-EC2-{region}"
        brick_file = f"{location}-{self.fabric}.brick"  # e.g., bjs-es-mgmt-cor.brick
        
        url = f"https://code.amazon.com/packages/{package}/blobs/mainline/--/configuration/etc/brick/EC2-{region}/{brick_file}"
        
        print(f"📍 Brick URL: {url}")
        return url
    
    def fetch_brick_data(self, url: str) -> Dict:
        """Fetch brick data from code.amazon.com using MCP tool"""
        print(f"📥 Fetching brick data from code.amazon.com...")
        
        # This would use the MCP tool in practice
        # For now, return a placeholder that shows the structure
        print("⚠️  Note: In production, this would use the amzn-mcp read_internal_website tool")
        print("    For now, please ensure brick data is available in brick-data.json")
        
        # Try to load from local file if available
        brick_file = self.output_dir / "brick-data.json"
        if brick_file.exists():
            with open(brick_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def categorize_device(self, device_name: str) -> Dict:
        """Categorize device by type and location"""
        site_match = re.match(r'^([a-z]+\d+-\d+)', device_name)
        site = site_match.group(1) if site_match else ""
        
        # Determine device type
        if '-mgmt-cor-r' in device_name:
            dtype, role = 'mgmt-cor', 'Management Core'
        elif '-mgmt-cor-v' in device_name:
            dtype, role = 'mgmt-cor-v', 'Virtual Mgmt Core'
        elif '-es-cor-r' in device_name or '-fnc-cor-r' in device_name:
            dtype, role = 'es-cor', 'Edge Services Core'
        elif '-es-c1-b' in device_name and '-t1-r' in device_name:
            dtype, role = 'es-c1', 'ES-C1 Compute'
        elif '-es-c1-mgmt' in device_name:
            dtype, role = 'es-c1', 'ES-C1 Mgmt'
        elif '-es-e1-mgmt' in device_name:
            dtype, role = 'es-mgmt', 'E1 Edge Mgmt'
        elif '-es-e2-mgmt' in device_name:
            dtype, role = 'es-mgmt', 'E2 Edge Mgmt'
        elif '-es-x1-mgmt' in device_name:
            dtype, role = 'es-x1-mgmt', 'X1 Mgmt'
        elif '-tt-acc' in device_name:
            dtype, role = 'tt-acc', 'Transit Access'
        elif '-cv1-agg' in device_name:
            dtype, role = 'cv1-agg', 'CV1 Agg'
        else:
            dtype, role = 'unknown', 'Unknown'
        
        return {
            'site': site,
            'device_type': dtype,
            'role': role,
            'color': DEVICE_COLORS.get(dtype, '#FFFFFF'),
            'is_target_site': site == self.site
        }
    
    def group_devices(self, devices: List[str]) -> Dict[str, List[str]]:
        """Group r1/r2 device pairs"""
        groups = defaultdict(list)
        for device in sorted(devices):
            base = re.sub(r'-r[12]$', '', device)
            groups[base].append(device)
        return dict(groups)
    
    def extract_topology_data(self, brick_data: Dict) -> Dict:
        """Extract and analyze topology from brick data"""
        nodes_and_interfaces = brick_data.get('NODES_AND_INTERFACES', {})
        
        all_devices = set()
        connections = []
        
        # Extract all devices and connections
        for device, interfaces in nodes_and_interfaces.items():
            all_devices.add(device)
            for iface, details in interfaces.items():
                remote = details.get('remote_device')
                if remote:
                    all_devices.add(remote)
                    connections.append({
                        'source': device,
                        'destination': remote,
                        'interface': iface,
                        'interface_type': details.get('interface_type', 'physical')
                    })
        
        # Separate intra-site and inter-site devices
        intra_site = [d for d in all_devices if d.startswith(self.site)]
        inter_site = [d for d in all_devices if not d.startswith(self.site)]
        
        # Group ALL devices (both intra-site and inter-site) - UPDATED
        intra_groups = self.group_devices(intra_site)
        inter_groups = self.group_devices(inter_site)  # NEW: Group inter-site too
        
        # Further group by device type for intra-site
        type_groups = defaultdict(list)
        for group_name, devices in intra_groups.items():
            cat = self.categorize_device(devices[0])
            
            # Aggressive grouping for certain types
            if cat['device_type'] == 'es-c1':
                type_groups['es-c1'].extend(devices)
            elif cat['device_type'] == 'es-mgmt':
                type_groups['es-mgmt'].extend(devices)
            else:
                type_groups[group_name] = devices
        
        # NEW: Also group inter-site devices by type (like ES-C1)
        inter_type_groups = defaultdict(list)
        for group_name, devices in inter_groups.items():
            cat = self.categorize_device(devices[0])
            site_match = re.match(r'^([a-z]+\d+-\d+)', group_name)
            site = site_match.group(1) if site_match else ""
            
            # Group ES-C1 and ES-MGMT devices by site
            if cat['device_type'] == 'es-c1':
                inter_type_groups[f"{site}-es-c1"].extend(devices)
            elif cat['device_type'] == 'es-mgmt':
                inter_type_groups[f"{site}-es-mgmt"].extend(devices)
            else:
                inter_type_groups[group_name] = devices
        
        inter_groups = inter_type_groups  # Replace with type-grouped version
        
        # Count ES-C1 connections
        es_c1_connections = [c for c in connections 
                            if 'es-c1' in c['source'] or 'es-c1' in c['destination']]
        
        return {
            'all_devices': all_devices,
            'intra_site': intra_site,
            'inter_site': inter_site,
            'intra_groups': intra_groups,
            'inter_groups': inter_groups,  # NEW: Include inter-site groups
            'type_groups': type_groups,
            'connections': connections,
            'es_c1_connections': es_c1_connections
        }
    
    def generate_drawio_xml(self, topology_data: Dict) -> str:
        """Generate draw.io XML from topology data"""
        
        # Create simplified node list
        nodes = {}
        node_positions = {}
        
        # Layout parameters - Enhanced spacing for beautification
        x_start, y_start = 120, 100
        x_spacing, y_spacing = 280, 150
        
        # Create intra-site grouped nodes
        row, col = 0, 0
        for group_name, devices in sorted(topology_data['type_groups'].items()):
            if not devices:
                continue
            
            cat = self.categorize_device(devices[0])
            
            # Create label
            if group_name in ['es-c1', 'es-mgmt']:
                label = f"{self.site}-{group_name}"
            elif len(devices) > 1:
                nums = [d.split('-r')[-1] for d in sorted(devices)]
                label = group_name + '-r[' + ','.join(nums) + ']'
            else:
                label = devices[0]
            
            x = x_start + (col * x_spacing)
            y = y_start + (row * y_spacing)
            
            nodes[group_name] = {
                'label': label,
                'role': cat['role'],
                'color': cat['color'],
                'x': x,
                'y': y,
                'devices': devices
            }
            
            col += 1
            if col >= 4:  # 4 columns for better spacing
                col, row = 0, row + 1
        
        row += 2  # Space before inter-site
        
        # Create inter-site nodes (GROUPED) - UPDATED
        col = 0
        for group_name, devices in sorted(topology_data['inter_groups'].items()):
            if not devices:
                continue
            
            # Create grouped label for inter-site
            if len(devices) > 1:
                nums = [d.split('-r')[-1] for d in sorted(devices)]
                label = group_name + '-r[' + ','.join(nums) + ']'
            else:
                label = devices[0]
            
            x = x_start + (col * x_spacing)
            y = y_start + (row * y_spacing)
            
            nodes[group_name] = {
                'label': label,
                'role': 'Inter-AZ',
                'color': DEVICE_COLORS['inter-az'],
                'x': x,
                'y': y,
                'devices': devices
            }
            
            col += 1
            if col >= 5:
                col, row = 0, row + 1
        
        # Build XML
        return self._build_xml(nodes, topology_data['connections'])
    
    def _build_xml(self, nodes: Dict, connections: List[Dict]) -> str:
        """Build the actual XML structure"""
        
        mxfile = ET.Element('mxfile', {
            'host': 'app.diagrams.net',
            'modified': '2025-10-01T09:45:00.000Z',
            'agent': 'Topology Generator Agent',
            'version': '24.0.0',
            'type': 'device'
        })
        
        diagram = ET.SubElement(mxfile, 'diagram', {
            'id': 'auto-topology',
            'name': f'{self.site.upper()} {self.fabric.upper()} Topology'
        })
        
        model = ET.SubElement(diagram, 'mxGraphModel', {
            'dx': '1600', 'dy': '1200', 'grid': '1', 'gridSize': '10',
            'guides': '1', 'tooltips': '1', 'connect': '1', 'arrows': '1',
            'fold': '1', 'page': '1', 'pageScale': '1',
            'pageWidth': '1600', 'pageHeight': '1200', 'math': '0', 'shadow': '0'
        })
        
        root = ET.SubElement(model, 'root')
        ET.SubElement(root, 'mxCell', {'id': '0'})
        ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})
        
        # Create nodes
        node_ids = {}
        device_to_node = {}
        cell_id = 2
        
        for node_key, node_data in nodes.items():
            # Determine if this is inter-site for styling
            is_inter_site = node_data['role'] == 'Inter-AZ'
            
            # Use HTML formatting for better appearance
            label_html = f"<b>{node_data['label']}</b><br/><i>{node_data['role']}</i>"
            
            # Enhanced styling with shadows and thicker borders
            if is_inter_site:
                style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={node_data['color']};strokeColor=#666666;strokeWidth=2;fontStyle=0;fontSize=11;shadow=1;"
            else:
                style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={node_data['color']};strokeColor=#000000;strokeWidth=2;fontStyle=0;fontSize=12;shadow=1;"
            
            cell = ET.SubElement(root, 'mxCell', {
                'id': str(cell_id),
                'value': label_html,
                'style': style,
                'vertex': '1',
                'parent': '1'
            })
            
            # Larger nodes for better visibility
            width = 220
            height = 90
            
            ET.SubElement(cell, 'mxGeometry', {
                'x': str(node_data['x']),
                'y': str(node_data['y']),
                'width': str(width),
                'height': str(height),
                'as': 'geometry'
            })
            
            node_ids[node_key] = str(cell_id)
            
            # Map all devices in this node to the node ID
            for device in node_data['devices']:
                device_to_node[device] = node_key
            
            cell_id += 1
        
        # Create connections
        added_connections = set()
        
        for conn in connections:
            src = conn['source']
            dst = conn['destination']
            
            # Map devices to their node groups
            src_node = device_to_node.get(src)
            dst_node = device_to_node.get(dst)
            
            if not src_node or not dst_node:
                continue
            
            # Avoid duplicate connections
            conn_key = tuple(sorted([src_node, dst_node]))
            if conn_key in added_connections:
                continue
            added_connections.add(conn_key)
            
            # Determine connection style
            src_cat = self.categorize_device(src)
            dst_cat = self.categorize_device(dst)
            
            if 'es-c1' in src or 'es-c1' in dst:
                # ES-C1 connection - HIGHLIGHTED (blue, thick)
                style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0066CC;strokeWidth=4;shadow=1;"
            elif src_cat['site'] != dst_cat['site']:
                # Inter-AZ - Solid line (gray, medium)
                style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#999999;strokeWidth=2.5;shadow=1;"
            else:
                # Intra-AZ - Solid line (black, medium)
                style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#333333;strokeWidth=2.5;shadow=1;"
            
            edge = ET.SubElement(root, 'mxCell', {
                'id': str(cell_id),
                'style': style,
                'edge': '1',
                'parent': '1',
                'source': node_ids[src_node],
                'target': node_ids[dst_node]
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
        print(f"  Topology Generator Agent")
        print(f"  Site: {self.site} | Fabric: {self.fabric}")
        print("="*80)
        
        # Step 1: Create output directory
        print(f"\n[1/5] Creating output directory...")
        self.output_dir.mkdir(exist_ok=True)
        print(f"  ✓ {self.output_dir}")
        
        # Step 2: Construct brick URL
        print(f"\n[2/5] Constructing brick file URL...")
        self.brick_url = self.construct_brick_url()
        
        # Step 3: Fetch brick data
        print(f"\n[3/5] Fetching brick data...")
        print(f"  ℹ️  To fetch automatically, use:")
        print(f"     Q CLI with amzn-mcp tool: read_internal_website")
        print(f"     URL: {self.brick_url}")
        
        # Check if brick data exists
        brick_file = self.output_dir / "brick-data.json"
        if not brick_file.exists():
            print(f"\n  ⚠️  Brick data not found. Please:")
            print(f"     1. Fetch brick data from: {self.brick_url}")
            print(f"     2. Save to: {brick_file}")
            print(f"     3. Run this script again")
            return False
        
        with open(brick_file, 'r') as f:
            self.brick_data = json.load(f)
        print(f"  ✓ Loaded brick data")
        
        # Step 4: Analyze topology
        print(f"\n[4/5] Analyzing topology...")
        topology_data = self.extract_topology_data(self.brick_data)
        
        print(f"  • Total devices: {len(topology_data['all_devices'])}")
        print(f"  • Intra-site ({self.site}): {len(topology_data['intra_site'])}")
        print(f"  • Inter-site: {len(topology_data['inter_site'])}")
        print(f"  • Connections: {len(topology_data['connections'])}")
        print(f"  • ES-C1 connections: {len(topology_data['es_c1_connections'])}")
        
        # Step 5: Generate draw.io topology
        print(f"\n[5/5] Generating draw.io topology...")
        xml_content = self.generate_drawio_xml(topology_data)
        
        output_file = self.output_dir / f"{self.site}-{self.fabric}-topology.drawio"
        with open(output_file, 'w') as f:
            f.write(xml_content)
        
        print(f"  ✓ Generated: {output_file}")
        
        # Summary
        print("\n" + "="*80)
        print("✅ Topology generation complete!")
        print("="*80)
        print(f"\nOutput file: {output_file}")
        print("\nFeatures:")
        print("  ✓ Plain XML (no compression)")
        print("  ✓ ALL r1/r2 pairs grouped (including inter-AZ)")
        print("  ✓ Separate, clear connections (not grouped)")
        print("  ✓ ES-C1 connections highlighted (blue, thick)")
        print("  ✓ Color-coded by device type")
        print("  ✓ Enhanced spacing and layout (280x150 grid)")
        print("  ✓ Shadows on nodes and connections")
        print("  ✓ Bold labels with italic roles")
        print("  ✓ No link labels")
        print("  ✓ Fully editable")
        print("\n" + "="*80 + "\n")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Automated Network Topology Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 topology_generator_agent.py --site bjs11-11 --fabric es-mgmt-cor
  python3 topology_generator_agent.py --site iad12-12 --fabric es-fnc
  python3 topology_generator_agent.py --site pdx50-50 --fabric es-mgmt-cor
        """
    )
    
    parser.add_argument('--site', required=True,
                       help='Site/DC identifier (e.g., bjs11-11, iad12-12)')
    parser.add_argument('--fabric', required=True,
                       help='Fabric type (e.g., es-mgmt-cor, es-fnc)')
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = TopologyGeneratorAgent(args.site, args.fabric)
    success = agent.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()