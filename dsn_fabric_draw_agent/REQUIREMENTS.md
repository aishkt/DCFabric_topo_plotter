# DSN Fabric Topology Generator - Requirements

## 🚀 Quick Start - Create DSN Topology from Scratch

**When you receive a request to create DSN topology for ANY site:**

### Complete Workflow (Self-Contained)

**Step 1: Generate URL with Smart Fallback**
```python
# Different sites use different device numbers!
site = "nrt55-55"  # User provides
region = site[:3]  # "nrt"

# Try in order until successful:
urls = [
    # Try r3 first (common for BJS)
    f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r3/dsn.attr",
    
    # Try r1 next (common for NRT)
    f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r1/dsn.attr",
    
    # Try r2 as last resort
    f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r2/dsn.attr"
]

# Fetch first successful URL
```

**Step 2: Fetch Config (ALWAYS FRESH)**
```
# Use builder-mcp (NOT amzn-mcp) for GenevaBuilderDCNE
use_mcp_tool(
  server_name="builder-mcp",
  tool_name="ReadInternalWebsites",
  inputs=["<URL from Step 1>"]
)

# If 404, try next URL in fallback list
```

**Step 3: Parse DSN File**
```python
# DSN file is plain text with key-value pairs
dsn_content = mcp_response['content']

# Key patterns to look for:
# - DSN PARENT-CHILD-INTF xe-0/0/XX DESC "... <--> {target}"
# - DSN NAME {network} IBGP-NEIGH {device} IP {ip}
# - DSN NAME {network} SWITCH INTF xe-0/0/XX DESC "... --> {switch}"
```

**Step 4: Extract Connections**
```python
import re

connections = []

# 1. Extract parent-child connections
for line in dsn_content.split('\n'):
    if 'DSN PARENT-CHILD-INTF' in line:
        match = re.search(r'<--> ([a-z0-9-]+)', line)
        if match:
            target = match.group(1)
            connections.append((source_device, target))

# 2. Extract IBGP peer connections
for line in dsn_content.split('\n'):
    if 'IBGP-NEIGH' in line and 'IP' in line:
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

def group_devices(devices):
    groups = defaultdict(list)
    for device in devices:
        base = re.sub(r'-r\d+$', '', device)
        groups[base].append(device)
    
    grouped = {}
    for base, devs in groups.items():
        if len(devs) > 1:
            nums = ''.join([d.split('-r')[-1] for d in sorted(devs)])
            grouped[f"{base}-r[{nums}]"] = devs
        else:
            grouped[devs[0]] = devs
    
    return grouped
```

**Step 6: Generate draw.io XML**
```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Use ElementTree (auto-escapes HTML)
# Color code: ROOT=Orange, Intra-AZ=Green, Inter-AZ=Blue
# Remove self-connections
# Deduplicate edges
```

### ⚠️ CRITICAL RULES

1. **NEVER use saved/cached config files**
2. **ALWAYS generate URL from site identifier**
3. **ALWAYS fetch fresh config from code.amazon.com**
4. **Use builder-mcp** (not amzn-mcp) for GenevaBuilderDCNE
5. **Try r3 → r1 → r2** (fallback logic for different sites)
6. **Parse text format** (not JSON/YAML)

### 📋 Complete Examples

**BJS11-11** (uses r3):
```
1. URL: .../dc-corp-bjs/bjs11-11-co-agg-r/bjs11-11-co-agg-r3/dsn.attr
2. Fetch: builder-mcp ReadInternalWebsites
3. Parse: 6 PARENT-CHILD-INTF + 1 IBGP-NEIGH
4. Devices: 8 (bjs11-11, bjs11-50/51/52, bjs10-10, pek4-7, pek50-50)
5. Group: r3+r4 → r[34]
6. Generate: 7 nodes, 6 connections
```

**NRT55-55** (uses r1):
```
1. URL: .../dc-corp-nrt/nrt55-55-co-agg-r/nrt55-55-co-agg-r1/dsn.attr
2. Fetch: builder-mcp ReadInternalWebsites
3. Parse: 1 PARENT-CHILD-INTF + 1 IBGP-NEIGH
4. Devices: 3 (nrt55-55, nrt12-12)
5. Group: r1+r2 → r[12]
6. Generate: 2 nodes, 1 connection
```

---

## 🔍 URL Pattern Analysis

### Base Pattern
```
https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/dc-corp-{region}/{site}-co-agg-r/{site}-co-agg-r{N}/dsn.attr
```

### Components
- **Package**: GenevaBuilderDCNE (fixed)
- **Region**: First 3 letters of site (bjs, nrt, iad, pdx)
- **Site**: Full site identifier (bjs11-11, nrt55-55)
- **Device**: co-agg-r{N} where N = 3, 1, or 2 (varies by site!)
- **File**: dsn.attr (fixed)

### Fallback Strategy
```python
# Try these in order:
1. {site}-co-agg-r3/dsn.attr  # Common for BJS
2. {site}-co-agg-r1/dsn.attr  # Common for NRT
3. {site}-co-agg-r2/dsn.attr  # Fallback

# Stop at first successful fetch (non-404)
```

---

## 📝 DSN File Structure

### Key Sections

**1. Physical Connections**:
```
DSN PARENT-CHILD-INTF xe-0/0/14 DESC "DSN USE ONLY {source} <--> {target}"
```

**2. BGP Peers**:
```
DSN NAME {network} IBGP-NEIGH {peer_device} IP {ip_address}
```

**3. Network Configs**:
```
DSN NAME {network} VLAN {vlan_id} DESC "{description}"
DSN NAME {network} PARENT xe-0/0/XX DESC "... <--> {target}"
DSN NAME {network} CHILD xe-0/0/XX DESC "... <--> {target}"
```

**4. Switch Connections**:
```
DSN NAME {network} SWITCH INTF xe-0/0/XX DESC "... --> {switch}"
```

### DSN Networks
Common DSN network names found:
- DSN-EC2, DSN-PRD, DSN-EPMS, DSN-IVT
- DSN-ATS, DSN-RFTS, DSN-DCSS
- DSN-WIRE, DSN-CLUB, DSN-INTERNET
- DSN-LENEL, DSN-DRAWB, DSN-MONITORING

---

## 🎯 Success Criteria

- ✅ Works for any AWS site
- ✅ Handles different device numbers (r1, r2, r3, r4)
- ✅ Fetches fresh config with fallback
- ✅ Parses text format correctly
- ✅ Groups device pairs
- ✅ Generates valid draw.io XML
- ✅ No self-connections
- ✅ All connections preserved

---

**Status**: ✅ Operational
**Version**: 1.0
**Tested**: bjs11-11 (r3), nrt55-55 (r1)
**Last Updated**: 2024-11-05