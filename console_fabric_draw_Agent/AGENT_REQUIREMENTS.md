# Topology Generator Agent - Requirements & Best Practices

## Overview
This document captures all the requirements and best practices learned during the development of the topology generator agent.

---

## 🚀 Quick Start - Create Console Topology from Scratch

**When you receive a request to create Console fabric topology for ANY site:**

### Complete Workflow (Self-Contained)

**Step 1: Generate Brick URL**
```python
# Formula (same as UMN EC2)
site = "bjs11-11"  # User provides
region = site[:3]  # "bjs"
REGION = region.upper()  # "BJS"

url = f"https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-{REGION}/blobs/mainline/--/configuration/etc/brick/EC2-{REGION}/{region}-es-mgmt-cor.brick"

# Examples:
# bjs11-11 → .../EC2-BJS/.../bjs-es-mgmt-cor.brick
# nrt12-12 → .../EC2-NRT/.../nrt-es-mgmt-cor.brick
```

**Step 2: Fetch Brick Config (ALWAYS FRESH)**
```
use_mcp_tool(
  server_name="amzn-mcp",
  tool_name="read_internal_website",
  url="<URL from Step 1>"
)
```

**Step 3: Parse Brick Data**
```python
brick_data = json.loads(mcp_response['content'])

# Extract:
devices = brick_data['DEVICE_DETAILS']
nodes = brick_data['NODES_AND_INTERFACES']
```

**Step 4: Extract Connections**
```python
# From Console YAML:
# 1. Parse neighbors section:
for con_cor_device in yaml_data['sites'][az][dc]['con_cor']:
    neighbors = con_cor_device['ec2']['neighbors']  # or 'prod'
    for neighbor in neighbors:
        dc_num = neighbor['dc']  # e.g., 50
        target = f"{region}{az}-{dc_num}-con-cor"
        connections.append((source_device, target))

# 2. Extract cross-region from ASN comments:
# Look for site codes in comments near titan_fw/asn fields
# Pattern: Any 3 letters + numbers (e.g., PKX140, IAD12, NRT55)
# Comment can be anything, just extract the site code

import re
for line_num, line in enumerate(yaml_lines):
    if 'titan_fw' in line or 'asn:' in line:
        # Check next 4 lines for site codes in comments
        for i in range(4):
            if line_num + i < len(yaml_lines):
                comment_line = yaml_lines[line_num + i]
                if '#' in comment_line:
                    # Look for airport codes (3 letters) + numbers
                    # All AWS sites use airport codes: BJS, NRT, IAD, PDX, PKX, etc.
                    # Pattern: {3 letters}{numbers} (e.g., PKX140, IAD12, NRT55)
                    match = re.search(r'\b([A-Z]{3}\d+)\b', comment_line)
                    if match:
                        site_code = match.group(1).lower()
                        # Add connection to that site's con-cor
                        connections.append((source_device, f"{site_code}-con-cor"))
```

**Special Case - Cross-Region Connections**:
```python
# Example from BJS11 YAML:
# titan_fw:
#   - local_intf: 1
#     asn: 16524 # ASN changed to match PKX140 UMN COR
#                                    ^^^^^^
# Extract: PKX140 → add connection to pkx140-con-cor

# Pattern: Look for airport codes (3 letters) in ANY comment
# Airport codes: BJS, NRT, IAD, PDX, PKX, SYD, FRA, DUB, CMH, etc.
# Comment text can be anything - just extract the site code
# Examples in comments:
#   "ASN changed to match PKX140 UMN COR" → PKX140
#   "Connection to IAD12 fabric" → IAD12
#   "Peer with NRT55 core" → NRT55
```

**Step 5: Group Devices (Aggressive for Console)**
```python
# Intra-site (target DC):
# - All ES-C1 → single node
# - All Edge Mgmt → single node
# - r1/r2 pairs → r[1,2]

# Inter-site (other DCs):
# - r1/r2 pairs → r[1,2]
# - Keep DCs separate
```

**Step 6: Generate draw.io XML**
```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Use ElementTree (handles HTML escaping)
# Aggressive grouping for intra-site
# Color code by device type
# Highlight ES-C1 connections (blue, thick)
```

### ⚠️ CRITICAL RULES

1. **NEVER use saved/cached config files**
2. **ALWAYS generate URL from site identifier**
3. **ALWAYS fetch fresh config from code.amazon.com**
4. **Aggressive grouping for intra-site** (different from UMN EC2)
5. **Group ALL r1/r2 pairs** (both intra and inter-site)

### 📋 Complete Example: bjs11-11

```
1. URL: .../EC2-BJS/.../bjs-es-mgmt-cor.brick
2. Fetch using MCP
3. Parse: 25 devices in BJS region
4. Group aggressively: ~7 intra-site + ~9 inter-site nodes
5. Generate: bjs11-11-es-mgmt-cor-topology.drawio
```

---

## ⚠️ Critical Data Fetching Requirements

**ALWAYS Follow These Rules**:
- ⚠️ **NEVER use saved/cached config files**
- ⚠️ **ALWAYS generate URL from site identifier**
- ⚠️ **ALWAYS fetch fresh config from code.amazon.com**
- ⚠️ **ALWAYS use MCP tool for latest configuration**

**Why Fresh Fetch is Critical**:
- Network configurations change frequently
- Cached data may be outdated
- Topology must reflect current state
- Configuration files are the source of truth

---

## Core Requirements

### 1. Device Grouping Strategy

#### Intra-Site Devices (Target Site)
**Rule**: Aggressive grouping to simplify topology

- **r1/r2 pairs**: Group into single node with `r[1,2]` notation
  - Example: `bjs11-11-es-mgmt-cor-r1` + `r2` → `bjs11-11-es-mgmt-cor-r[1,2]`

- **Device type grouping**: Group all devices of same type
  - All ES-C1 devices → Single `{site}-es-c1` node
  - All Edge Management → Single `{site}-es-[e1,e2]-mgmt` node
  - Example: `bjs11-11-es-c1-b11-t1-r13/14/15/16` + `es-c1-mgmt-r1/r2` → `bjs11-11-es-c1`

- **Virtual devices**: Keep separate (e.g., `-v1`, `-v2`)

#### Inter-Site Devices (Other Sites)
**Rule**: Group r1/r2 pairs, but keep sites separate

- **r1/r2 pairs**: Group into single node with `r[1,2]` notation
  - Example: `bjs20-20-es-mgmt-cor-r1` + `r2` → `bjs20-20-es-mgmt-cor-r[1,2]`

- **Different sites**: Keep as separate nodes
  - `bjs11-50`, `bjs11-51`, `bjs11-52` → 3 separate grouped nodes
  - `bjs12-12`, `bjs20-20`, `bjs80-80` → 3 separate grouped nodes

- **Do NOT**: Group across different sites
  - ❌ `bjs11-[50,51,52]` (wrong - too much grouping)
  - ✅ `bjs11-50-es-mgmt-cor-r[1,2]`, `bjs11-51-es-mgmt-cor-r[1,2]`, etc. (correct)

### 2. Connection Visualization

#### Connection Rules
- **Separate connections**: Each connection must be a distinct edge element
- **No connection grouping**: Even if multiple devices connect to same target, show individual lines
- **Visible in diagram**: All connections must be clearly visible

#### Connection Styling

| Type | Color | Width | Pattern | Shadow |
|------|-------|-------|---------|--------|
| Intra-AZ | #333333 (dark gray) | 2.5px | Solid | Yes |
| ES-C1 ⭐ | #0066CC (blue) | 4px | Solid | Yes |
| Inter-AZ | #999999 (light gray) | 2.5px | Dashed | Yes |

### 3. Visual Design (Beautification)

#### Node Styling
- **Borders**: strokeWidth=2 (thicker than default)
- **Shadows**: shadow=1 (adds depth)
- **Labels**: HTML formatted with `<b>label</b><br/><i>role</i>`
- **Size**: 220x90 pixels (larger for readability)
- **Corners**: rounded=1 (smooth edges)

#### Inter-Site Node Styling
- **Border**: dashed=1 (distinguishes from intra-site)
- **Color**: Lighter gray (#E8E8E8 or #F5F5F5)
- **Border color**: #666666 (darker gray)
- **Font size**: 11px (slightly smaller)

#### Layout
- **Grid spacing**: 280x150 (wider spacing for clarity)
- **Columns**: 4 per row (better than 5 for readability)
- **Starting position**: (120, 100) - good margins
- **Row spacing**: Extra space between intra-site and inter-site sections

### 4. Color Coding

| Device Type | Color | Hex Code | Usage |
|------------|-------|----------|-------|
| Management Core | Orange | #FFE6CC | Core management devices |
| Virtual Management | Purple | #E1D5E7 | Virtual core devices |
| Edge Services Core | Green | #D5E8D4 | ES/FNC core routers |
| ES-C1 Compute | Blue | #DAE8FC | Compute fabric |
| Edge Management | Yellow | #FFF2CC | E1/E2 edge management |
| X1 Management | Red | #F8CECC | X1 management layer |
| Transit Access | Pink | #E6D0DE | Transit/TT devices |
| CV1 Aggregation | Cyan | #D0E0E3 | Compute aggregation |
| Inter-AZ | Gray | #E8E8E8 | Cross-site devices |

### 5. Technical Specifications

#### XML Format
- **Format**: Plain XML (no compression or encoding)
- **Indentation**: 2 spaces
- **mxGeometry**: All elements must have `as="geometry"` attribute
- **Cell IDs**: Sequential numbering starting from 2
- **Parent references**: All cells parent="1" (root)

#### Validation
- ✅ No mxGeometry errors
- ✅ All source/target references valid
- ✅ No orphaned nodes
- ✅ All connections have proper geometry
- ✅ Compatible with draw.io desktop and web

### 6. Connection Logic

#### Avoid Duplicates
```python
# Use set to track added connections
added_connections = set()
conn_key = tuple(sorted([src_node, dst_node]))
if conn_key not in added_connections:
    added_connections.add(conn_key)
    # Create edge
```

#### Device-to-Node Mapping
```python
# Map individual devices to their grouped nodes
device_to_node = {}
for node_key, node_data in nodes.items():
    for device in node_data['devices']:
        device_to_node[device] = node_key
```

---

## Implementation Checklist

When implementing the agent, ensure:

- [ ] Group ALL r1/r2 pairs (both intra-site and inter-site)
- [ ] Aggressive grouping for intra-site by device type (es-c1, es-mgmt)
- [ ] Keep inter-site groups separate by site
- [ ] Create individual connections (no grouping)
- [ ] Highlight ES-C1 connections (blue, thick)
- [ ] Apply shadows to nodes and connections
- [ ] Use HTML formatting for labels
- [ ] Enhanced spacing (280x150 grid)
- [ ] 4-column layout
- [ ] Thicker borders (strokeWidth=2)
- [ ] Larger nodes (220x90)
- [ ] Plain XML output
- [ ] Proper mxGeometry
- [ ] No link labels

---

## Example Output Structure

### For BJS11-11

**Intra-Site Nodes** (Grouped):
```
bjs11-11-es-mgmt-cor-r[1,2]     (Management Core)
bjs11-11-es-mgmt-cor-v1          (Virtual Management)
bjs11-11-es-cor-r[101,201]       (Edge Services Core)
bjs11-11-es-c1                   (ALL Compute)
bjs11-11-es-[e1,e2]-mgmt         (ALL Edge Mgmt)
bjs11-11-es-x1-mgmt-r[1,2]       (X1 Management)
bjs11-11-tt-acc-v[1,2]           (Transit Access)
```

**Inter-Site Nodes** (Grouped by site):
```
bjs11-50-es-mgmt-cor-r[1,2]     (Inter-AZ)
bjs11-51-es-mgmt-cor-r[1,2]     (Inter-AZ)
bjs11-52-es-mgmt-cor-r[1,2]     (Inter-AZ)
bjs12-12-es-mgmt-cor-r[1,2]     (Inter-AZ)
bjs20-20-es-mgmt-cor-r[1,2]     (Inter-AZ)
bjs80-80-es-mgmt-cor-r[1,2]     (Inter-AZ)
```

**Connections**:
- Intra-AZ: Solid black lines
- ES-C1: Blue thick lines (highlighted)
- Inter-AZ: Dashed gray lines
- Each connection is separate and visible

---

## Common Mistakes to Avoid

### ❌ Wrong Approaches

1. **Over-grouping inter-site**
   - ❌ `bjs11-[50,51,52]` (groups different sites)
   - ✅ `bjs11-50-r[1,2]`, `bjs11-51-r[1,2]`, `bjs11-52-r[1,2]` (separate sites)

2. **Not grouping inter-site r1/r2**
   - ❌ `bjs20-20-es-mgmt-cor-r1`, `bjs20-20-es-mgmt-cor-r2` (separate)
   - ✅ `bjs20-20-es-mgmt-cor-r[1,2]` (grouped)

3. **Grouping connections**
   - ❌ Single connection representing multiple links
   - ✅ Individual connection for each link

4. **Missing ES-C1 devices in grouping**
   - ❌ Showing `es-c1-b11-t1-r13`, `r14`, `r15`, `r16` separately
   - ✅ Group all as `{site}-es-c1`

5. **No visual distinction**
   - ❌ All connections same style
   - ✅ Different styles for intra-AZ, inter-AZ, and ES-C1

---

## Testing the Agent

### Test Cases

1. **BJS11-11** (Primary site)
   ```bash
   python3 topology_generator_agent.py --site bjs11-11 --fabric es-mgmt-cor
   ```
   Expected: 7 intra-site groups, ~13 inter-site groups

2. **BJS12-12** (Secondary site)
   ```bash
   python3 topology_generator_agent.py --site bjs12-12 --fabric es-mgmt-cor
   ```
   Expected: 4 intra-site groups, ~9 inter-site groups

3. **Different region**
   ```bash
   python3 topology_generator_agent.py --site iad12-12 --fabric es-fnc
   ```
   Expected: Region-specific topology

### Validation Checklist

After generation, verify:
- [ ] All r1/r2 pairs are grouped
- [ ] Inter-site devices grouped by site (not across sites)
- [ ] Connections are visible
- [ ] ES-C1 connection is blue and thick
- [ ] Inter-AZ connections are dashed
- [ ] Nodes have shadows
- [ ] Labels are bold with italic roles
- [ ] XML is plain (not compressed)
- [ ] File opens correctly in draw.io

---

## Future Enhancements

### Planned Improvements
1. **Automatic MCP integration** - Fetch brick data automatically
2. **Interactive mode** - Prompt for missing parameters
3. **Validation mode** - Check topology correctness
4. **Export formats** - PNG, SVG, PDF output
5. **Comparison mode** - Diff between topology versions
6. **Metrics overlay** - Add bandwidth/utilization data

### Integration Opportunities
- CI/CD pipeline for auto-generation
- Wiki/Quip embedding
- Monitoring dashboards
- Planning tools

---

**Version**: 2.0 (Updated with all best practices)
**Last Updated**: 2025-10-01
**Status**: Production Ready