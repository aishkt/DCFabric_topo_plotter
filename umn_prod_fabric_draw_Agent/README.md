# UMN PROD Fabric Topology Generator Agent

## Overview

Automated agent for generating **UMN PROD (Workspace) fabric** topology diagrams from SwitchBuilder brick definition files. This agent processes workspace management core (ws-mgmt-cor) devices and their interconnections.

---

## 🎯 Purpose

Generate comprehensive topology diagrams showing:
- ✅ Workspace management core devices (ws-mgmt-cor)
- ✅ Inter-AZ connections (cross availability zone)
- ✅ Intra-AZ connections (within availability zone)
- ✅ WS-C1 fabric connections (workspace compute)
- ✅ Device grouping (r1 + r2 → r[12], v1 separate)
- ✅ Color-coded by device type and location

---

## 🔗 Data Source

**SwitchBuilder Brick Definition Files** (PROD variant)

### URL Pattern
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-{REGION}/blobs/mainline/--/configuration/etc/brick/PROD-{REGION}/{region}-ws-mgmt-cor.brick
```

### Key Differences from UMN EC2
| Aspect | UMN EC2 | UMN PROD |
|--------|---------|----------|
| Package | SwitchBuilderBrickDef-**EC2**-{REGION} | SwitchBuilderBrickDef-**PROD**-{REGION} |
| Path | EC2-{REGION} | PROD-{REGION} |
| Filename | {region}-**es**-mgmt-cor.brick | {region}-**ws**-mgmt-cor.brick |
| Fabric | EC2 compute (es-c1) | Workspace compute (ws-c1) |
| Purpose | EC2 instances | Internal AWS workspaces |

---

## 🚀 Quick Start

### Step 1: Generate URL
```python
site = "bjs11-11"  # or any site
region = site[:3]  # "bjs"
REGION = region.upper()  # "BJS"

url = f"https://code.amazon.com/packages/SwitchBuilderBrickDef-PROD-{REGION}/blobs/mainline/--/configuration/etc/brick/PROD-{REGION}/{region}-ws-mgmt-cor.brick"
```

### Step 2: Fetch Config (ALWAYS FRESH)
```
use_mcp_tool(
  server_name="amzn-mcp",
  tool_name="read_internal_website",
  url="<URL from Step 1>"
)
```

### Step 3: Generate Topology
Use the same generator logic as UMN EC2, just with ws-mgmt instead of es-mgmt.

---

## 📊 Example: BJS11-11

### Generated Topology
- **File**: `/Users/anishkt/bjs11-11-umn-prod-topology/bjs11-11-umn-prod-topology.drawio`
- **Nodes**: 14 (from 25 devices)
- **Connections**: 17
- **v1 Devices**: 3 (bjs11-11, bjs12-12, bjs20-20)

### Device Structure
**ROOT DC (bjs11-11)** - Orange:
- `bjs11-11-ws-mgmt-cor-r[12]` (Almach pair)
- `bjs11-11-ws-mgmt-cor-v1` (Juniper - separate)

**Intra-AZ (bjs11)** - Light Green:
- bjs11-50, bjs11-51, bjs11-52

**Inter-AZ** - Light Blue:
- bjs12-12 (r[12] + v1)
- bjs12-60
- bjs20-20 (r[12] + v1)
- bjs20-70, bjs20-73, bjs20-74
- bjs80-80

---

## ⚠️ CRITICAL RULES FOR AI AGENTS

#### 🚨 DO's

1. ✅ **USE existing Python scripts** - `umn_prod_topology_generator.py` is in this directory
2. ✅ **ALWAYS fetch fresh config** from code.amazon.com using amzn-mcp
3. ✅ **ALWAYS generate URL** from site identifier (never hardcode)
4. ✅ **Use amzn-mcp** (NOT builder-mcp) for SwitchBuilderBrickDef packages
5. ✅ **Parse JSON format** (.brick files are JSON, not text)
6. ✅ **Separate v1 devices** for ROOT DC (keep v1 separate from r[12])
7. ✅ **Save output to Desktop** (outside project folder)
8. ✅ **Follow the workflow** in REQUIREMENTS.md

#### 🚫 DON'Ts

1. ❌ **NEVER create new Python generator scripts** - use existing `umn_prod_topology_generator.py`
2. ❌ **NEVER use cached/saved config files** - always fetch fresh
3. ❌ **NEVER hardcode URLs** - generate dynamically from site identifier
4. ❌ **NEVER use builder-mcp** for SwitchBuilderBrickDef - use amzn-mcp
5. ❌ **NEVER group v1 with r[12]** for ROOT DC - keep separate
6. ❌ **NEVER save output inside project folder** - save to Desktop
7. ❌ **NEVER skip NODES_AND_INTERFACES** - required for connections

---

## 🎨 Visual Design

### Color Scheme
| Device Type | Color | Hex Code |
|------------|-------|----------|
| ROOT DC | Orange | #FFE6CC |
| Intra-AZ | Light Green | #D5E8D4 |
| Inter-AZ | Light Blue | #DAE8FC |
| Juniper v1 | Gray | #D0D0D0 |

### Device Grouping
- r1 + r2 → r[12] (all sites)
- v1 devices → separate nodes (when present)
- Label format: `<b>device-name</b><br/><i>ws-mgmt</i>`

---

## 📁 Project Structure

```
umn_prod_fabric_draw_Agent/
├── README.md                    # This file
└── (generators to be added)

Output:
/Users/anishkt/{site}-umn-prod-topology/
├── brick-configs/
├── analysis/
└── {site}-umn-prod-topology.drawio
```

---

## ✅ Success Criteria

- ✅ Works for any AWS site
- ✅ Fetches fresh brick data
- ✅ Groups r[12] pairs correctly
- ✅ Separates v1 devices
- ✅ Includes all ws-mgmt-cor connections
- ✅ Generates valid draw.io XML
- ✅ No self-connections
- ✅ No missing connections

---

**Version**: 1.0
**Status**: ✅ Operational
**Last Updated**: 2024-11-05
**Location**: `/Users/anishkt/anish_topo_Agent_Project/umn_prod_fabric_draw_Agent/`