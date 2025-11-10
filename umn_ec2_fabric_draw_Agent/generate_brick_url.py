#!/usr/bin/env python3
"""
Brick URL Generator for UMN EC2 Fabric Topology
Generates code.amazon.com URLs for SwitchBuilder brick definition files
"""

import sys
import re

def construct_brick_url(site: str, fabric: str = "es-mgmt-cor") -> str:
    """
    Construct brick file URL from site identifier
    
    Args:
        site: Site identifier (e.g., "bjs11-11", "iad12-12", "nrt55-55")
        fabric: Fabric type (default: "es-mgmt-cor")
    
    Returns:
        Full URL to brick file
    
    Examples:
        construct_brick_url("bjs11-11") → BJS brick URL
        construct_brick_url("iad12-12") → IAD brick URL
        construct_brick_url("nrt55-55") → NRT brick URL
    """
    
    # Extract region code (first 3 letters)
    region_match = re.match(r'^([a-z]{3})', site)
    if not region_match:
        raise ValueError(f"Invalid site format: {site}. Expected format: xxx##-##")
    
    region_code = region_match.group(1)  # "bjs", "iad", "nrt", etc.
    region_upper = region_code.upper()   # "BJS", "IAD", "NRT", etc.
    
    # Construct URL components
    package = f"SwitchBuilderBrickDef-EC2-{region_upper}"
    path = f"configuration/etc/brick/EC2-{region_upper}"
    brick_file = f"{region_code}-{fabric}.brick"
    
    # Build complete URL
    url = (
        f"https://code.amazon.com/packages/{package}/blobs/mainline/--/"
        f"{path}/{brick_file}"
    )
    
    return url

def print_url_examples():
    """Print URL examples for common regions"""
    
    print("\n" + "=" * 70)
    print("Brick URL Generator - Examples")
    print("=" * 70)
    
    examples = [
        ("bjs11-11", "Beijing"),
        ("iad12-12", "Virginia"),
        ("nrt12-12", "Tokyo"),
        ("nrt55-55", "Tokyo NRT55"),
        ("pdx50-50", "Portland"),
        ("syd6-61", "Sydney"),
        ("fra52-52", "Frankfurt"),
        ("dub8-78", "Dublin"),
        ("cmh50-50", "Columbus"),
    ]
    
    for site, location in examples:
        url = construct_brick_url(site)
        print(f"\n{location} ({site}):")
        print(f"  {url}")

def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python3 generate_brick_url.py <site> [fabric]")
        print("\nExamples:")
        print("  python3 generate_brick_url.py bjs11-11")
        print("  python3 generate_brick_url.py iad12-12")
        print("  python3 generate_brick_url.py nrt55-55")
        print("  python3 generate_brick_url.py nrt12-12 es-mgmt-cor")
        print("\nCommon sites:")
        print("  • Beijing: bjs11-11, bjs12-12, bjs20-20, bjs80-80")
        print("  • Virginia: iad12-12, iad50-50, iad89-89")
        print("  • Tokyo: nrt12-12, nrt20-20, nrt55-55")
        print("  • Portland: pdx50-50, pdx52-52")
        print("  • Sydney: syd6-61, syd62-62")
        print("  • Frankfurt: fra52-52, fra56-56")
        print("\nTo see all examples:")
        print("  python3 generate_brick_url.py --examples")
        sys.exit(1)
    
    if sys.argv[1] == '--examples':
        print_url_examples()
        sys.exit(0)
    
    site = sys.argv[1]
    fabric = sys.argv[2] if len(sys.argv) > 2 else "es-mgmt-cor"
    
    try:
        url = construct_brick_url(site, fabric)
        
        print("\n" + "=" * 70)
        print(f"Brick URL for {site.upper()}")
        print("=" * 70)
        print(f"\nSite: {site}")
        print(f"Fabric: {fabric}")
        print(f"\nGenerated URL:")
        print(f"{url}")
        print("\n" + "=" * 70)
        print("\nNext steps:")
        print("  1. Use MCP tool to fetch this URL:")
        print("     use_mcp_tool(")
        print("       server_name='amzn-mcp',")
        print("       tool_name='read_internal_website',")
        print(f"       url='{url}'")
        print("     )")
        print("  2. Save the response to brick-configs/")
        print("  3. Run the topology generator")
        print("=" * 70 + "\n")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Test with nrt55-55
    site = "nrt55-55"
    url = construct_brick_url(site)
    
    print("=" * 70)
    print(f"URL Generated for {site.upper()}")
    print("=" * 70)
    print(f"\n✅ {url}")
    print("\n" + "=" * 70)
PYTHON_EOF</command>
</execute_command>