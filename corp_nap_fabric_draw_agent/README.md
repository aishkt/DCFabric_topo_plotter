# Corp NAP Fabric Topology Generator Agent

## Overview

Automated agent for generating **Corp NAP (Network Access Point)** topology diagrams from GenevaBuilderDCNE configuration files. This agent processes corporate network access point (np-cor) devices and their interconnections.

---

## 🎯 Purpose

Generate Corp NAP topology diagrams showing:
- ✅ Network access point devices (np-cor)
- ✅ Corporate core connections (co-cor, co-agg)
- ✅ Ring connections between sites
- ✅ Inter-region NAP connections
- ✅ Firewall connections
- ✅ Device grouping (r101 + r102 → r10[12])
- ✅ Color-coded by device type
- ❌ **Excludes iBGP and eBGP connections**

---

## 🔗 Data Source

**GenevaBuilderDCNE Configuration Files** (.attr format)

### URL Pattern
```
https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/nap-{region}/{site}-np-cor-r/{site}-np-cor-r101/routerspecific.attr
```

### URL Generation Formula
```python
site = "bjs11-11"  # User provides
region = site[:3]  # Extract first 3 letters (e.g., "bjs")

url = f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/nap-{region}/{site}-np-cor-r/{site}-np-cor-r101/routerspecific.attr"
```

---

## 🚀 Quick Start

### Step 1: Generate URL
```python
site = "bjs11-11"
region = site[:3]
url = f"...GenevaBuilderDCNE/.../nap-{region}/{site}-np-cor-r/{site}-np-cor-r101/routerspecific.attr"
```

### Step 2: Fetch Config (ALWAYS FRESH)
```
use_mcp_tool(
  server_name="builder-mcp",
  tool_name="ReadInternalWebsites",
  inputs=["<URL from Step 1>"]
)
```

### Step 3: Parse Required Sections
Extract connections from:
- ✅ **# customer lags** (CUSTOMERLAG with DESC)
- ✅ **# customer interfaces** (CUSTOMERINTF with DESC)
- ✅ **#RING Interfaces** (RINGINTF with DESC)
- ✅ **#RING Lag Interfaces** (RINGLAG with DESC)
- ✅ **Inter-region NAP** (e.g., NAPBJSPEK PEER, FWPEER)
- ❌ **IBGPNEIGH** (iBGP - EXCLUDE)
- ❌ **EBGPNEIGH** (eBGP - EXCLUDE)
- ❌ **RRCLIENTNEIGH** (Route reflector - EXCLUDE)

### Step 4: Generate Topology
- Group devices (r101+r102 → r10[12])
- Remove duplicates
- Generate draw.io XML
- **Save to Desktop** (outside project folder)

---

## 📊 Example: BJS11-11

### Generated Topology
- **File**: `/Users/anishkt/Desktop/bjs11-11_corp_nap_topology.drawio`
- **Nodes**: 11 devices
- **Connections**: 10 (2 customer, 6 ring, 2 inter-region NAP)

### Device Structure
**NAP Core** (Light Orange):
- bjs11-11-np-cor-r101
- bjs10-10-np-cor-r101
- bjs11-51-np-cor-r101
- bjs11-52-np-cor-r101
- bjs12-12-np-cor-r101
- bjs20-20-np-cor-r101
- bjs80-80-np-cor-r101
- pek50-50-np-cor-r101

**Corp Core** (Light Green):
- bjs11-11-co-cor-r1

**Corp Aggregation** (Light Blue):
- bjs11-11-co-agg-r1

**Firewall** (Light Red):
- pek50-50-np-cor-fw2

### Connection Types
- **Customer** (Blue): 2 connections to co-cor and co-agg
- **Ring** (Green): 6 connections to other np-cor sites
- **Inter-region NAP** (Red): 1 connection to pek50-50 router
- **Firewall** (Red): 1 connection to pek50-50 firewall

---

## ⚠️ Critical Requirements

- ❌ **NEVER use saved/cached config files**
- ✅ **ALWAYS generate URL from site identifier**
- ✅ **ALWAYS fetch fresh config from code.amazon.com**
- ✅ **Use builder-mcp** for GenevaBuilderDCNE
- ✅ **Parse .attr format** (text file with key-value pairs)
- ✅ **Exclude iBGP and eBGP** connections
- ✅ **Save output to Desktop** (outside project folder)

---

## 🎨 Visual Design

### Color Scheme
| Device Type | Color | Hex Code | Description |
|------------|-------|----------|-------------|
| np-cor | Light Orange | #FFE6CC | NAP core routers |
| co-cor | Light Green | #D5E8D4 | Corp core routers |
| co-agg | Light Blue | #DAE8FC | Corp aggregation |
| fw | Light Red | #F8CECC | Firewalls |

### Connection Colors
| Connection Type | Color | Hex Code | Description |
|----------------|-------|----------|-------------|
| customer | Blue | #0066CC | Customer connections |
| ring | Green | #009900 | Ring connections |
| nap_inter_region | Red | #CC0000 | Inter-region NAP |
| nap_firewall | Red | #CC0000 | Firewall connections |

### Device Grouping
- r101 + r102 → r10[12]
- r1 + r2 → r[12]
- Single devices remain unchanged (fw2, r101 only)

---

## 📝 File Format

**Corp NAP .attr file** contains key-value configuration pairs:

**Parsed Sections**:
```
# customer lags
CUSTOMERLAG ae40 DESC bjs11-11-co-cor-r1

# customer interfaces  
CUSTOMERINTF xe-0/0/72 DESC bjs11-11-co-cor-r1

#RING Lag Interfaces
RINGLAG ae1 DESC bjs10-10-np-cor-r101

#RING Interfaces
RINGINTF xe-0/0/0 DESC bjs10-10-np-cor-r101

# NAP CONNECTION BJS AND PEK
NAPBJSPEK PEER pek50-50-np-cor-r101
NAPBJSPEK FWPEER pek50-50-np-cor-fw2
```

**Excluded Sections**:
```
IBGPNEIGH bjs9-9-np-cor-r101 IP 10.191.28.6    # iBGP - EXCLUDED
EBGPNEIGH bjs11-11-co-cor-r1 IP 10.191.28.205  # eBGP - EXCLUDED
RRCLIENTNEIGH bjs11-51-np-cor-r101 IP 10.191.28.12  # RR - EXCLUDED
```

---

## 📂 Output Location

⚠️ **CRITICAL: Files MUST be saved OUTSIDE the project folder**

**Correct Location**:
```
/Users/anishkt/Desktop/{site}_corp_nap_topology.drawio
```

**Example**:
```
/Users/anishkt/Desktop/bjs11-11_corp_nap_topology.drawio
```

**NEVER save to**:
```
/Users/anishkt/anish_topo_Agent_Project/corp_nap_fabric_draw_agent/
```

---

## ✅ Self-Sufficient

An agent can create Corp NAP topology for ANY site by:
1. ✅ Extracting region from site identifier
2. ✅ Generating URL
3. ✅ Fetching fresh config using builder-mcp
4. ✅ Parsing required sections (customer, ring, inter-region NAP)
5. ✅ Excluding iBGP and eBGP
6. ✅ Grouping devices (r10[12])
7. ✅ Generating draw.io XML
8. ✅ Saving to Desktop

**No manual intervention needed** - fully automated!

---

## 🔧 Scripts

### generate_bjs11_corp_nap.py
Example script for BJS11-11 with embedded sample data

### nap_fabric_generator.py
Generic generator that accepts site as command-line argument

**Usage**:
```bash
python3 nap_fabric_generator.py <site>
```

---

**Version**: 1.0
**Status**: ✅ Operational
**Tested**: bjs11-11
**Last Updated**: 2024-11-10
**Location**: `/Users/anishkt/anish_topo_Agent_Project/corp_nap_fabric_draw_agent/`