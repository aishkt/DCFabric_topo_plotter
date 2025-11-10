# UMN EC2 Fabric Topology Generator - Requirements

## 🚀 Quick Start - Create Topology from Scratch

**When you receive a request to create UMN EC2 topology for ANY site:**

### Step-by-Step Instructions (Complete Workflow)

**Step 1: Generate Brick URL**
```python
# Extract region from site (first 3 letters)
site = "nrt55-55"  # or any site like "iad12-12", "pdx50-50"
region_code = site[:3]  # "nrt", "iad", "pdx"
region_upper = region_code.upper()  # "NRT", "IAD", "PDX"

# Construct URL
url = f"https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-{region_upper}/blobs/mainline/--/configuration/etc/brick/EC2-{region_upper}/{region_code}-es-mgmt-cor.brick"

# Example results:
# nrt55-55 → https://code.amazon.com/.../EC2-NRT/.../nrt-es-mgmt-cor.brick
# iad12-12 → https://code.amazon.com/.../EC2-IAD/.../iad-es-mgmt-cor.brick
```

**Step 2: Fetch Brick Config (ALWAYS FRESH)**
```
use_mcp_tool(
  server_name="amzn-mcp",
  tool_name="read_internal_website",
  url="<URL from Step 1>"
)
```

**Step 3: Parse MCP Response**
```python
# MCP returns JSON with:
# - DEVICE_DETAILS: {device_name: {device_type, device_layer}}
# - NODES_AND_INTERFACES: {device: {interface: {remote_device, ...}}}

# Extract:
devices = brick_data['DEVICE_DETAILS'].keys()
connections = extract_from_nodes_and_interfaces(brick_data['NODES_AND_INTERFACES'])
```

**Step 4: Filter for ROOT AZ**
```python
# Include:
# - All devices in ROOT AZ (e.g., nrt55-*)
# - Inter-AZ devices that connect to ROOT (e.g., nrt12-12)

# Exclude:
# - Other AZ devices without direct ROOT connection
```

**Step 5: Group Devices**
```python
# Standard grouping: r1 + r2 → r[12]
# Special for ROOT DC: Keep v1 separate from r[12]

# Example:
# nrt55-55-es-mgmt-cor-r1 + r2 → nrt55-55-es-mgmt-cor-r[12]
# nrt55-55-es-mgmt-cor-v1 → nrt55-55-es-mgmt-cor-v1 (separate)
```

**Step 6: Generate draw.io XML**
```python
# Use xml.etree.ElementTree (handles HTML escaping)
# Color code: ROOT=Orange, Intra-AZ=Green, Inter-AZ=Blue, Juniper=Gray
# Remove self-connections (grouped devices to themselves)
# Deduplicate bidirectional connections
```

### ⚠️ CRITICAL RULES - NEVER SKIP

1. **NEVER use saved/cached config files**
2. **ALWAYS generate URL from site identifier**
3. **ALWAYS fetch fresh config from code.amazon.com**
4. **ALWAYS separate v1 devices for ROOT DC**
5. **ALWAYS preserve all es-mgmt-cor connections**

### 📋 Complete Example: nrt55-55

```
1. URL: https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-NRT/blobs/mainline/--/configuration/etc/brick/EC2-NRT/nrt-es-mgmt-cor.brick

2. Fetch using MCP tool

3. Parse: 42 devices total in NRT region

4. Filter: 15 devices (nrt55 AZ + nrt12-12 inter-AZ)

5. Group: 8 nodes (r[12] pairs + v1 separate)

6. Generate: nrt55-55-umn-ec2-topology.drawio
```

---

## Project Context

**Example Sites**:
- Beijing: bjs11-11
- Tokyo: nrt55-55
- Virginia: iad12-12

**Brick File Pattern**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-{REGION}/blobs/mainline/--/configuration/etc/brick/EC2-{REGION}/{region}-es-mgmt-cor.brick
```

---

## 🔗 Brick File URL Pattern

### URL Structure
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-{REGION}/blobs/mainline/--/configuration/etc/brick/EC2-{REGION}/{region}-es-mgmt-cor.brick
```

### Components
1. **Package**: `SwitchBuilderBrickDef-EC2-{REGION}`
   - REGION is uppercase (BJS, IAD, NRT, PDX, SYD, FRA, etc.)

2. **Path**: `configuration/etc/brick/EC2-{REGION}/`
   - REGION is uppercase

3. **Brick File**: `{region}-es-mgmt-cor.brick`
   - region is lowercase (bjs, iad, nrt, pdx, syd, fra, etc.)

### Examples

**Beijing (BJS)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-BJS/blobs/mainline/--/configuration/etc/brick/EC2-BJS/bjs-es-mgmt-cor.brick
```

**Virginia (IAD)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-IAD/blobs/mainline/--/configuration/etc/brick/EC2-IAD/iad-es-mgmt-cor.brick
```

**Tokyo (NRT)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-NRT/blobs/mainline/--/configuration/etc/brick/EC2-NRT/nrt-es-mgmt-cor.brick
```

**Portland (PDX)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-PDX/blobs/mainline/--/configuration/etc/brick/EC2-PDX/pdx-es-mgmt-cor.brick
```

**Sydney (SYD)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-SYD/blobs/mainline/--/configuration/etc/brick/EC2-SYD/syd-es-mgmt-cor.brick
```

**Frankfurt (FRA)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-FRA/blobs/mainline/--/configuration/etc/brick/EC2-FRA/fra-es-mgmt-cor.brick
```

### URL Generation Logic
```python
def construct_brick_url(site: str) -> str:
    """
    Construct brick file URL from site identifier
    
    Args:
        site: Site identifier (e.g., "bjs11-11", "iad12-12")
    
    Returns:
        Full URL to brick file
    """
    # Extract region code (first 3 letters)
    region_code = site[:3]  # "bjs", "iad", "nrt", etc.
    region_upper = region_code.upper()  # "BJS", "IAD", "NRT", etc.
    
    # Construct URL
    package = f"SwitchBuilderBrickDef-EC2-{region_upper}"
    path = f"configuration/etc/brick/EC2-{region_upper}"
    brick_file = f"{region_code}-es-mgmt-cor.brick"
    
    url = f"https://code.amazon.com/packages/{package}/blobs/mainline/--/{path}/{brick_file}"
    
    return url

# Examples:
# construct_brick_url("bjs11-11") → BJS brick URL
# construct_brick_url("iad12-12") → IAD brick URL
# construct_brick_url("nrt12-12") → NRT brick URL
```

### Important Notes
- ✅ Package name uses **uppercase** region code
- ✅ Path uses **uppercase** region code
- ✅ Brick filename uses **lowercase** region code
- ✅ Brick file is always `{region}-es-mgmt-cor.brick`
- ✅ Brick file is **region-specific**, not site-specific
  - All sites in BJS region use the same brick file: `bjs-es-mgmt-cor.brick`
  - All sites in IAD region use the same brick file: `iad-es-mgmt-cor.brick`

---

## Implementation Requirements

### 🔄 Standard Workflow for Any Site

**When receiving a request to create UMN EC2 topology for a site:**

**Step 0: Generate Brick URL** (FIRST STEP)
```python
# Use the URL generator utility
python3 generate_brick_url.py <site>

# Example for nrt55-55:
python3 generate_brick_url.py nrt55-55
# Output: https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-NRT/blobs/mainline/--/configuration/etc/brick/EC2-NRT/nrt-es-mgmt-cor.brick
```

**Step 1: Fetch Brick Config** (SECOND STEP)
```
use_mcp_tool(
  server_name="amzn-mcp",
  tool_name="read_internal_website",
  url="<generated URL from Step 0>"
)
```

**Step 2: Build Topology** (THIRD STEP)
```bash
# Run the topology generator with the fetched data
python3 generate_topology.py <site>
```

**CRITICAL REQUIREMENTS**:
- ✅ Brick file is **region-specific**, not site-specific
- ✅ All sites in same region use the same brick file
- ✅ URL generation is automatic - just provide site identifier
- ✅ Generator works for ANY AWS site
- ⚠️ **NEVER use saved/cached config files**
- ⚠️ **ALWAYS generate URL and fetch fresh config from code.amazon.com**
- ⚠️ **ALWAYS use MCP tool to fetch the latest brick definition**

**Why Fresh Fetch is Critical**:
- Network configurations change frequently
- Cached data may be outdated
- Topology must reflect current state
- Brick definitions are the source of truth

---

### 1. Context Management ✅
**Store request context for session recovery**
- Save all requirements and progress
- Enable retrieval if session resets
- Handle context window overflow

### 2. Project Setup ✅
**Create output folder structure**
```
/Users/anishkt/bjs11-11-umn-ec2-topology/
├── brick-configs/           # Store brick definition files
├── analysis/                # Connection analysis and statistics
└── bjs11-11-umn-ec2-topology.drawio
```

### 3. Fetch Brick Definition ✅
**Use MCP tool to retrieve brick file**
- Tool: `read_internal_website`
- URL: SwitchBuilderBrickDef-EC2-BJS brick file
- Save complete JSON response
- Extract DEVICE_DETAILS and NODES_AND_INTERFACES

### 4. Parse Device Details ⏳
**Extract device metadata from DEVICE_DETAILS section**
- Device name (e.g., bjs11-11-es-mgmt-cor-r1)
- Device type (almach, juniper)
- Device layer (mgmt_core)
- Extract AZ identifier (bjs11, bjs12, etc.)
- Extract DC identifier (11, 12, 50, etc.)
- Extract fabric type (es-mgmt, es-c1, es-e1, etc.)

### 5. Parse Connectivity ⏳
**Extract connections from NODES_AND_INTERFACES section**
- For each device:
  - Parse all interfaces (jrp*, bond*, xe-*, ae*)
  - Extract remote_device (target device)
  - Extract remote_device_interface
  - Extract interface_type (physical, virtual)
  - Extract local_ip and connection details

### 6. Build Connection Matrix ⏳
**Map complete device-to-device connections**
- Create connection list with source → target pairs
- Include interface names and types
- Preserve IP addressing information
- Track connection metadata

### 7. Identify Connection Types ⏳
**Categorize connections by network topology**

**Inter-AZ Connections** (jrp21, jrp23):
- Cross availability zone links
- Example: bjs11-11 ↔ bjs12-12
- Example: bjs11-11 ↔ bjs20-20
- Example: bjs11-11 ↔ bjs80-80

**Intra-AZ Connections** (jrp32, jrp23):
- Within same AZ, different DCs
- Example: bjs11-11 ↔ bjs11-50
- Example: bjs11-11 ↔ bjs11-51
- Example: bjs11-11 ↔ bjs11-52

**ES-C1 Connections** (bond73, bond77, jrp19, jrp20):
- To EC2 fabric devices
- Example: bjs11-11-es-mgmt-cor-r1 ↔ bjs11-11-es-c1-b11-t1-r13

**Local Connections** (jrp1, jrp2, jrp3):
- Within same DC to local fabric devices
- Example: es-mgmt-cor ↔ es-e1-mgmt
- Example: es-mgmt-cor ↔ es-c1-mgmt
- Example: es-mgmt-cor ↔ es-x1-mgmt

### 8. Remove Duplicates ⏳
**Deduplicate bidirectional connections**
- Treat A→B and B→A as single connection
- Use sorted tuple as deduplication key
- Preserve one representative connection
- Maintain connection metadata
- **CRITICAL**: Remove self-connections (when grouped devices connect to themselves)
- **CRITICAL**: Ensure NO es-mgmt-cor to es-mgmt-cor connections are missed
- **CRITICAL**: All management core interconnections must be preserved

### 9. Group Devices ⏳
**Combine device pairs into single nodes**

**Grouping Rules**:
- `{base}-r1` + `{base}-r2` → `{base}-r[12]`
- `{base}-v1` + `{base}-v2` → `{base}-v[12]`
- Keep single devices ungrouped
- **SPECIAL**: For ROOT DC, keep v1 devices separate from r1/r2 group

**Examples**:
- `bjs11-11-es-mgmt-cor-r1` + `bjs11-11-es-mgmt-cor-r2` → `bjs11-11-es-mgmt-cor-r[12]`
- `bjs11-11-es-mgmt-cor-v1` → `bjs11-11-es-mgmt-cor-v1` (separate - ROOT DC special case)
- `bjs20-20-es-mgmt-cor-r1` + `bjs20-20-es-mgmt-cor-r2` → `bjs20-20-es-mgmt-cor-r[12]`

**ROOT DC Special Handling**:
- For the ROOT DC (e.g., bjs11-11), if v1 device exists:
  - Group r1+r2 → r[12]
  - Keep v1 separate
  - Show v1 connections to r[12] and other devices
  - This provides visibility into the Juniper virtual router's role

### 10. Design Color Scheme ⏳
**Color-code devices by type and location**

**Priority Order**:
1. ROOT DC (bjs11-11) → Orange (#FFE6CC)
2. ES-C1 devices → Light Red (#F8CECC)
3. ES-E1 devices → Light Purple (#E1D5E7)
4. ES-X1 devices → Light Yellow (#FFF4E6)
5. Juniper devices → Gray (#D0D0D0)
6. Inter-AZ (different AZ) → Light Blue (#DAE8FC)
7. Intra-AZ (same AZ, different DC) → Light Green (#D5E8D4)

### 11. Generate draw.io XML ⏳
**Create fully editable topology diagram**

**XML Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile>
  <diagram name="UMN EC2 Topology">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- Device nodes -->
        <mxCell id="2" value="<b>device-name</b><br/><i>fabric-type</i>" 
                style="rounded=1;whiteSpace=wrap;html=1;fillColor=#COLOR;" 
                vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="200" height="60" as="geometry"/>
        </mxCell>
        <!-- Connections -->
        <mxCell id="N" value="" style="endArrow=none;html=1;" 
                edge="1" parent="1" source="2" target="3">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

**Requirements**:
- Plain XML (no compression)
- Correct mxGeometry for all elements
- Valid source/target references
- No orphaned nodes
- Proper cell IDs and parent references

### 12. Validate XML ⏳
**Ensure clean, editable output**
- All mxGeometry elements have `as="geometry"`
- No compression or encoding
- Proper indentation (2 spaces)
- Valid source/target cell IDs
- Compatible with draw.io desktop and web

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ Fetches brick definition from code.amazon.com
- ⏳ Parses 25 management core devices
- ⏳ Groups device pairs (r1+r2 → r[12])
- ⏳ Extracts all connections from NODES_AND_INTERFACES
- ⏳ Categorizes connections (inter-AZ, intra-AZ, es-c1, local)
- ⏳ Removes duplicate bidirectional connections
- ⏳ Generates color-coded topology
- ⏳ Creates fully editable draw.io XML

### Visual Requirements
- ⏳ Color-coded by device type and location
- ⏳ Grouped devices with clear labels
- ⏳ Clean connections (no labels)
- ⏳ Proper spacing and layout
- ⏳ HTML-formatted device labels

### Technical Requirements
- ⏳ Plain XML format (no compression)
- ⏳ Correct mxGeometry for all elements
- ⏳ Valid source/target references
- ⏳ No orphaned nodes
- ⏳ Compatible with draw.io

---

## 📊 Expected Statistics

### Devices
- **Total**: 25 devices
- **Almach**: 24 devices
- **Juniper**: 1 device
- **Grouped**: ~13 display nodes (after r1/r2 grouping)

### Connections (Estimated)
- **Inter-AZ**: ~30-40 connections
- **Intra-AZ**: ~20-30 connections
- **ES-C1**: ~10-15 connections
- **Local**: ~40-50 connections
- **Total**: ~100-135 unique connections

### Sites
- **AZs**: 5 (bjs11, bjs12, bjs20, bjs80, pkx140)
- **DCs**: 12 (11, 12, 20, 50, 51, 52, 70, 73, 74, 80, 140, 141)

---

## 🔄 Development Status

### Completed
- ✅ Project folder structure created
- ✅ Brick definition fetched from code.amazon.com
- ✅ Device details extracted (25 devices)
- ✅ Basic Python agent created
- ✅ Color scheme defined
- ✅ Device grouping logic implemented
- ✅ README documentation created

### In Progress
- ⏳ NODES_AND_INTERFACES parsing
- ⏳ Connection extraction and categorization
- ⏳ Draw.io XML generation with connections

### Pending
- ⏳ Connection deduplication
- ⏳ Full topology generation
- ⏳ XML validation
- ⏳ draw.io testing

---

## 🚀 Next Steps

1. **Complete NODES_AND_INTERFACES parsing**
   - Extract full connectivity data from MCP response
   - Save to nodes_and_interfaces.json
   - Build connection matrix

2. **Implement connection processing**
   - Parse all device interfaces
   - Extract remote_device connections
   - Categorize by type (inter-AZ, intra-AZ, es-c1, local)
   - Remove duplicates

3. **Generate complete topology**
   - Create device nodes with grouping
   - Add all connections
   - Apply color scheme
   - Generate draw.io XML

4. **Validate and test**
   - Check XML structure
   - Open in draw.io
   - Verify all devices and connections visible
   - Ensure fully editable

---

**Status**: 🚧 Initial Setup Complete - Ready for Full Implementation
**Version**: 1.0 (In Development)
**Last Updated**: 2024-11-04