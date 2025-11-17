# UMN PROD Fabric Topology Generator - Requirements

## 🚀 Quick Start - Create UMN PROD Topology from Scratch

**When you receive a request to create UMN PROD topology for ANY site:**

### Complete Workflow (Self-Contained)

**Step 1: Generate Brick URL**
```python
# Formula for UMN PROD (workspace management core)
site = "bjs11-11"  # User provides
region = site[:3]  # Extract: "bjs"
REGION = region.upper()  # "BJS"

# Construct URL
url = f"https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-{REGION}/blobs/mainline/--/configuration/etc/brick/PROD-{REGION}/{region}-ws-mgmt-cor.brick"

# Examples:
# bjs11-11 → .../SwitchBuilderBrickDef-PROD-BJS/.../bjs-ws-mgmt-cor.brick
# iad12-12 → .../SwitchBuilderBrickDef-PROD-IAD/.../iad-ws-mgmt-cor.brick
# nrt55-55 → .../SwitchBuilderBrickDef-PROD-NRT/.../nrt-ws-mgmt-cor.brick
```

**Step 2: Fetch Brick Config (ALWAYS FRESH)**
```
# Use amzn-mcp (NOT builder-mcp) for SwitchBuilderBrickDef
use_mcp_tool(
  server_name="amzn-mcp",
  tool_name="read_internal_website",
  url="<URL from Step 1>"
)
```

**Step 3: Parse Brick JSON**
```python
# MCP returns JSON with two key sections:
brick_data = json.loads(mcp_response['content'])

# 1. DEVICE_DETAILS - Device metadata
devices = brick_data['DEVICE_DETAILS']
# Format: {device_name: {device_type, device_layer}}

# 2. NODES_AND_INTERFACES - Connectivity data
connections = brick_data['NODES_AND_INTERFACES']
# Format: {device: {interface: {remote_device, remote_device_interface, ...}}}
```

**Step 4: Filter for Target Site**
```python
# Include devices from:
# 1. ROOT AZ (e.g., bjs11-* for bjs11-11)
# 2. Inter-AZ devices that connect to ROOT

# Example for bjs11-11:
# Include: bjs11-11, bjs11-50, bjs11-51, bjs11-52 (intra-AZ)
# Include: bjs12-12, bjs20-20, bjs80-80 (inter-AZ with connections)
# Exclude: Other AZ devices without direct ROOT connection
```

**Step 5: Extract Connections**
```python
# Parse NODES_AND_INTERFACES
for source_device, interfaces in nodes_and_interfaces.items():
    for interface_name, interface_data in interfaces.items():
        target_device = interface_data.get('remote_device')
        if target_device:
            connections.append({
                'source': source_device,
                'target': target_device,
                'interface': interface_name,
                'remote_interface': interface_data.get('remote_device_interface')
            })
```

**Step 6: Group Devices**
```python
# Standard grouping: r1 + r2 → r[12]
# Special for ROOT DC: Keep v1 separate from r[12]

# Example:
# bjs11-11-ws-mgmt-cor-r1 + r2 → bjs11-11-ws-mgmt-cor-r[12]
# bjs11-11-ws-mgmt-cor-v1 → bjs11-11-ws-mgmt-cor-v1 (separate)
```

**Step 7: Generate draw.io XML**
```python
import xml.etree.ElementTree as ET

# Color code: ROOT=Orange, Intra-AZ=Green, Inter-AZ=Blue, Juniper=Gray
# Remove self-connections (grouped devices to themselves)
# Deduplicate bidirectional connections
```

### ⚠️ CRITICAL RULES FOR AI AGENTS

#### 🚨 DO's

1. ✅ **USE existing Python scripts** - Generator scripts are in this directory
2. ✅ **ALWAYS fetch fresh config** from code.amazon.com using amzn-mcp
3. ✅ **ALWAYS generate URL** from site identifier (never hardcode)
4. ✅ **Use amzn-mcp** (NOT builder-mcp) for SwitchBuilderBrickDef packages
5. ✅ **Parse JSON format** (.brick files are JSON, not text)
6. ✅ **Separate v1 devices** for ROOT DC (keep v1 separate from r[12])
7. ✅ **Save output to Desktop** (outside project folder)
8. ✅ **Follow the workflow** in this REQUIREMENTS.md

#### 🚫 DON'Ts

1. ❌ **NEVER create new Python generator scripts** - use existing scripts
2. ❌ **NEVER use cached/saved config files** - always fetch fresh
3. ❌ **NEVER hardcode URLs** - generate dynamically from site identifier
4. ❌ **NEVER use builder-mcp** for SwitchBuilderBrickDef - use amzn-mcp
5. ❌ **NEVER group v1 with r[12]** for ROOT DC - keep separate
6. ❌ **NEVER save output inside project folder** - save to Desktop
7. ❌ **NEVER skip NODES_AND_INTERFACES** - required for connections

### 📋 Complete Example: BJS11-11

```
1. URL: https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-BJS/blobs/mainline/--/configuration/etc/brick/PROD-BJS/bjs-ws-mgmt-cor.brick

2. Fetch using amzn-mcp ReadInternalWebsites

3. Parse JSON:
   - DEVICE_DETAILS: 25 devices
   - NODES_AND_INTERFACES: Connectivity data

4. Filter: 14 devices (bjs11 AZ + inter-AZ with connections)

5. Group: 
   - bjs11-11-ws-mgmt-cor-r[12] (Almach pair)
   - bjs11-11-ws-mgmt-cor-v1 (Juniper - separate)
   - Other device pairs

6. Generate: bjs11-11-umn-prod-topology.drawio
```

---

## 🔗 URL Pattern Analysis

### Base Pattern
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-{REGION}/blobs/mainline/--/configuration/etc/brick/PROD-{REGION}/{region}-ws-mgmt-cor.brick
```

### Components
- **Package**: SwitchBuilderBrickDef-PROD-{REGION} (uppercase)
- **Path**: configuration/etc/brick/PROD-{REGION}/ (uppercase)
- **Filename**: {region}-ws-mgmt-cor.brick (lowercase)
- **Fabric**: ws-mgmt (workspace management, not es-mgmt)

### Key Differences from UMN EC2

| Aspect | UMN EC2 | UMN PROD |
|--------|---------|----------|
| Package | SwitchBuilderBrickDef-**EC2**-{REGION} | SwitchBuilderBrickDef-**PROD**-{REGION} |
| Path | EC2-{REGION} | PROD-{REGION} |
| Filename | {region}-**es**-mgmt-cor.brick | {region}-**ws**-mgmt-cor.brick |
| Fabric | EC2 compute (es-c1) | Workspace compute (ws-c1) |
| Purpose | EC2 instances | Internal AWS workspaces |
| MCP Server | amzn-mcp | amzn-mcp |

### URL Examples

**Beijing (BJS)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-BJS/blobs/mainline/--/configuration/etc/brick/PROD-BJS/bjs-ws-mgmt-cor.brick
```

**Virginia (IAD)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-IAD/blobs/mainline/--/configuration/etc/brick/PROD-IAD/iad-ws-mgmt-cor.brick
```

**Tokyo (NRT)**:
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-NRT/blobs/mainline/--/configuration/etc/brick/PROD-NRT/nrt-ws-mgmt-cor.brick
```

---

## 📝 Brick File Structure

### JSON Format
```json
{
  "BRICK": "cor",
  "FABRIC": "bjs-ws-mgmt",
  "TYPE": "L3_AGG_UMN",
  "DEVICE_DETAILS": {
    "bjs11-11-ws-mgmt-cor-r1": {
      "device_layer": "mgmt_core",
      "device_type": "almach"
    },
    "bjs11-11-ws-mgmt-cor-v1": {
      "device_type": "juniper"
    }
  },
  "NODES_AND_INTERFACES": {
    "bjs11-11-ws-mgmt-cor-r1": {
      "jrp21-0": {
        "remote_device": "bjs12-12-ws-mgmt-cor-r1",
        "remote_device_interface": "jrp21-0",
        "interface_type": "physical"
      }
    }
  }
}
```

### Key Sections

**DEVICE_DETAILS**:
- Device name → device_type (almach/juniper)
- Device name → device_layer (mgmt_core)

**NODES_AND_INTERFACES**:
- Source device → interfaces → remote_device
- Interface types: jrp* (inter-connect), bond* (LAG), xe-*, ae-*

---

## 🎨 Visual Design

### Color Scheme
| Device Type | Color | Hex Code | Description |
|------------|-------|----------|-------------|
| ROOT DC | Orange | #FFE6CC | bjs11-11 devices |
| Intra-AZ | Light Green | #D5E8D4 | Same AZ, different DC |
| Inter-AZ | Light Blue | #DAE8FC | Different AZ |
| Juniper v1 | Gray | #D0D0D0 | Virtual routers |

### Device Grouping Rules
- r1 + r2 → r[12] (all sites)
- v1 devices → separate nodes (when present)
- **SPECIAL**: For ROOT DC, keep v1 separate from r[12]
- Label format: `<b>device-name</b><br/><i>ws-mgmt (device-type)</i>`

---

## 🎯 Success Criteria

- ✅ Works for any AWS site
- ✅ Fetches fresh brick data from code.amazon.com
- ✅ Parses DEVICE_DETAILS and NODES_AND_INTERFACES
- ✅ Groups r[12] pairs correctly
- ✅ Separates v1 devices for ROOT DC
- ✅ Includes all ws-mgmt-cor connections
- ✅ Generates valid draw.io XML
- ✅ No self-connections
- ✅ No missing connections
- ✅ Color-coded by device type and location

---

## 📊 Expected Output

### For BJS11-11
**Devices** (after grouping):
- bjs11-11-ws-mgmt-cor-r[12] (Almach pair)
- bjs11-11-ws-mgmt-cor-v1 (Juniper - separate)
- bjs11-50-ws-mgmt-cor-r[12]
- bjs11-51-ws-mgmt-cor-r[12]
- bjs11-52-ws-mgmt-cor-r[12]
- bjs12-12-ws-mgmt-cor-r[12]
- bjs12-60-ws-mgmt-cor-r[12]
- bjs20-20-ws-mgmt-cor-r[12]
- bjs20-20-ws-mgmt-cor-v1
- bjs20-70-ws-mgmt-cor-r[12]
- bjs20-73-ws-mgmt-cor-r[12]
- bjs20-74-ws-mgmt-cor-r[12]
- bjs80-80-ws-mgmt-cor-r[12]

**Connections**:
- Inter-AZ: Cross availability zone links
- Intra-AZ: Within bjs11, different DCs
- WS-C1: To workspace compute fabric

**Output File**: `/Users/anishkt/Desktop/{site}_umn_prod_topology.drawio`

---

## 🔍 Implementation Notes

### Device Naming Convention
- **Pattern**: `{site}-ws-mgmt-cor-{suffix}`
- **Suffixes**: r1, r2 (Almach pairs), v1 (Juniper virtual)
- **Example**: bjs11-11-ws-mgmt-cor-r1

### Connection Interfaces
- **jrp21, jrp23**: Inter-AZ connections
- **jrp32, jrp23**: Intra-AZ connections
- **bond73, bond77**: WS-C1 fabric connections
- **jrp1, jrp2, jrp3**: Local fabric connections

### Parsing Strategy
1. Load JSON from MCP response
2. Extract DEVICE_DETAILS for device metadata
3. Extract NODES_AND_INTERFACES for connectivity
4. Filter devices relevant to target site
5. Group device pairs (r1+r2 → r[12])
6. Keep v1 separate for ROOT DC
7. Generate draw.io XML with color coding

---

**Status**: ✅ Operational
**Version**: 1.0
**Data Source**: SwitchBuilderBrickDef-PROD-{REGION}
**Output Location**: Desktop (outside project folder)
**Last Updated**: 2024-11-17