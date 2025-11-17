# DSN Fabric Topology Generator Agent

## Overview

Automated agent for generating **DSN (Datacenter Segmented Network)** topology diagrams from GenevaBuilderDCNE configuration files. This agent processes corporate aggregation (co-agg) devices and their DSN interconnections.

---

## 🚀 Quick Start - Create DSN Topology from Scratch

**When you receive a request to create DSN topology for ANY site:**

### Complete Workflow (Self-Contained)

**Step 1: Generate URL with Fallback Logic**
```python
# Formula with fallback (different sites use different device numbers)
site = "nrt55-55"  # User provides
region = site[:3]  # Extract: "nrt"

# Try in order: r3 → r1 → r2
urls_to_try = [
    f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r3/dsn.attr",
    f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r1/dsn.attr",
    f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r2/dsn.attr"
]

# Site-specific patterns:
# BJS sites: Use r3 (bjs11-11-co-agg-r3)
# NRT sites: Use r1 (nrt55-55-co-agg-r1)
# Other sites: Try r3 first, then r1, then r2
```

**Step 2: Fetch Config (ALWAYS FRESH)**
```
# Use builder-mcp (not amzn-mcp) for GenevaBuilderDCNE
use_mcp_tool(
  server_name="builder-mcp",
  tool_name="ReadInternalWebsites",
  inputs=["<URL from Step 1>"]
)

# If 404, try next URL in fallback list
```

**Step 3: Parse DSN File**
```python
# DSN file is text format with key-value pairs
dsn_content = mcp_response['content']

# Key sections:
# 1. DSN PARENT-CHILD-INTF - Physical connections
# 2. DSN NAME {network} IBGP-NEIGH - BGP peers
# 3. DSN NAME {network} PARENT/CHILD - Network connections
```

**Step 4: Extract Connections**
```python
# Parse DSN PARENT-CHILD-INTF lines:
# Pattern: "DSN PARENT-CHILD-INTF xe-0/0/XX DESC ... <--> {target_device}"

connections = []
for line in dsn_content.split('\n'):
    if 'DSN PARENT-CHILD-INTF' in line:
        match = re.search(r'<--> ([a-z0-9-]+)', line)
        if match:
            target = match.group(1)
            connections.append((source_device, target))
    
    # Also extract IBGP-NEIGH for device pairs
    if 'IBGP-NEIGH' in line:
        match = re.search(r'IBGP-NEIGH ([a-z0-9-]+)', line)
        if match:
            peer = match.group(1)
            connections.append((source_device, peer))
```

**Step 5: Group Devices**
```python
# Group device pairs:
# r1 + r2 → r[12]
# r3 + r4 → r[34]

# Example:
# nrt55-55-co-agg-r1 + r2 → nrt55-55-co-agg-r[12]
# bjs11-11-co-agg-r3 + r4 → bjs11-11-co-agg-r[34]
```

**Step 6: Generate draw.io XML**
```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Use ElementTree (handles HTML escaping)
# Color code: ROOT=Orange, Intra-AZ=Green, Inter-AZ=Blue
# Deduplicate connections
```

### ⚠️ CRITICAL RULES FOR AI AGENTS

#### 🚨 DO's

1. ✅ **USE existing Python scripts** - `dsn_fabric_generator.py` is already in this directory
2. ✅ **ALWAYS fetch fresh config** from code.amazon.com using builder-mcp
3. ✅ **ALWAYS generate URL** from site identifier (never hardcode)
4. ✅ **Use builder-mcp** (NOT amzn-mcp) for GenevaBuilderDCNE package
5. ✅ **Try r3 → r1 → r2** fallback logic for different sites
6. ✅ **Parse text format** (.attr files are plain text, not JSON/YAML)
7. ✅ **Save output to Desktop** (outside project folder)
8. ✅ **Follow the workflow** in REQUIREMENTS.md

#### 🚫 DON'Ts

1. ❌ **NEVER create new Python generator scripts** - use existing `dsn_fabric_generator.py`
2. ❌ **NEVER use cached/saved config files** - always fetch fresh
3. ❌ **NEVER hardcode URLs** - generate dynamically from site identifier
4. ❌ **NEVER use amzn-mcp** for GenevaBuilderDCNE - use builder-mcp
5. ❌ **NEVER assume device number** - use fallback strategy (r3 → r1 → r2)
6. ❌ **NEVER save output inside project folder** - save to Desktop
7. ❌ **NEVER skip URL fallback** - different sites use different device numbers

### 📋 Complete Examples

**BJS11-11** (uses r3):
```
1. URL: .../dc-corp-bjs/bjs11-11-co-agg-r/bjs11-11-co-agg-r3/dsn.attr
2. Fetch using builder-mcp
3. Parse: DSN PARENT-CHILD-INTF lines
4. Connections: 6 parent-child + 1 IBGP peer
5. Group: r3+r4 → r[34]
6. Generate: 7 nodes, 6 connections
```

**NRT55-55** (uses r1):
```
1. URL: .../dc-corp-nrt/nrt55-55-co-agg-r/nrt55-55-co-agg-r1/dsn.attr
2. Fetch using builder-mcp
3. Parse: DSN PARENT-CHILD-INTF lines
4. Connections: 1 parent-child + 1 IBGP peer
5. Group: r1+r2 → r[12]
6. Generate: 2 nodes, 1 connection
```

---

## 📊 Generated Topologies

**BJS11-11 DSN** ✅
- File: `/Users/anishkt/bjs11-11-dsn-topology/bjs11-11-dsn-topology.drawio`
- 7 nodes, 6 connections
- Device: co-agg-r[34]

**NRT55-55 DSN** ✅
- File: `/Users/anishkt/nrt55-55-dsn-topology/nrt55-55-dsn-topology.drawio`
- 2 nodes, 1 connection
- Device: co-agg-r[12]

---

## 🎨 Visual Design

### Color Scheme
| Device Type | Color | Hex Code |
|------------|-------|----------|
| ROOT DC | Orange | #FFE6CC |
| Intra-AZ | Light Green | #D5E8D4 |
| Inter-AZ | Light Blue | #DAE8FC |

### Device Grouping
- r1 + r2 → r[12]
- r3 + r4 → r[34]
- Label format: `<b>device-name</b><br/><i>co-agg</i>`

---

## 📝 DSN File Format

**Key Sections**:
1. `DSN PARENT-CHILD-INTF` - Physical parent-child connections
2. `DSN NAME {network} IBGP-NEIGH` - BGP peer information
3. `DSN NAME {network} PARENT/CHILD` - Network-specific connections
4. `DSN NAME {network} SWITCH INTF` - Switch interface connections

**Example Lines**:
```
DSN PARENT-CHILD-INTF xe-0/0/14 DESC "... <--> bjs11-50-co-agg-r1"
DSN NAME DSN-EC2 IBGP-NEIGH bjs11-11-co-agg-r4 IP 8.2.136.3
DSN NAME DSN-WIRE SWITCH INTF xe-0/0/45 DESC "... --> bjs11-dc-wifi-rsw1"
```

---

## ✅ Self-Sufficient

An agent can create DSN topology for ANY site by:
1. ✅ Extracting region from site identifier
2. ✅ Generating URLs with fallback (r3 → r1 → r2)
3. ✅ Fetching fresh config using builder-mcp
4. ✅ Parsing DSN PARENT-CHILD-INTF lines
5. ✅ Extracting IBGP-NEIGH connections
6. ✅ Grouping devices (r[12] or r[34])
7. ✅ Generating draw.io XML

**No manual intervention needed** - fully automated!

---

**Version**: 1.0
**Status**: ✅ Operational
**Tested**: bjs11-11 (r3), nrt55-55 (r1)
**Last Updated**: 2024-11-05
**Location**: `/Users/anishkt/anish_topo_Agent_Project/dsn_fabric_draw_agent/`