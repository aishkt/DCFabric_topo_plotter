# Corp NAP Fabric Topology Generator - Requirements

## Overview
Generate Corp NAP fabric topology diagrams from GenevaBuilderDCNE .attr configuration files. This agent parses router-specific configuration files to extract device connections and relationships.

---

## 🚀 Quick Start - Create Corp NAP Topology from Scratch

**When you receive a request to create Corp NAP topology for ANY site:**

### Complete Workflow (Self-Contained)

**Step 1: Generate URL**
```python
# Formula - uses GenevaBuilderDCNE .attr file
site = "bjs11-11"  # User provides
region = site[:3]  # Extract region code (e.g., "bjs")

url = f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/nap-{region}/{site}-np-cor-r/{site}-np-cor-r101/routerspecific.attr"

# Examples:
# bjs11-11 → .../nap-bjs/bjs11-11-np-cor-r/bjs11-11-np-cor-r101/routerspecific.attr
# nrt55-62 → .../nap-nrt/nrt55-62-np-cor-r/nrt55-62-np-cor-r101/routerspecific.attr
# iad12-12 → .../nap-iad/iad12-12-np-cor-r/iad12-12-np-cor-r101/routerspecific.attr
```

**Step 2: Fetch Config (ALWAYS FRESH)**
```
# Use builder-mcp for GenevaBuilderDCNE
use_mcp_tool(
  server_name="builder-mcp",
  tool_name="ReadInternalWebsites",
  inputs=["<URL from Step 1>"]
)
```

**Step 3: Parse .attr File - REQUIRED Sections**

⚠️ **CRITICAL: Only parse these specific sections**

```python
attr_content = mcp_response['content']

# REQUIRED SECTIONS TO PARSE:
# 1. # customer lags - CUSTOMERLAG lines with DESC
# 2. # customer interfaces - CUSTOMERINTF lines with DESC  
# 3. #RING Interfaces - RINGINTF lines with DESC
# 4. #RING Lag Interfaces - RINGLAG lines with DESC
# 5. Inter-region connections - Look for patterns like "# NAP CONNECTION BJS AND PEK"
#    - Parse NAPBJSPEK PEER or similar patterns
#    - Parse NAPBJSPEK FWPEER for firewall connections
#    - Connection names vary by site (not always BJS-PEK)

# ❌ EXCLUDE THESE SECTIONS:
# - IBGPNEIGH (iBGP connections)
# - EBGPNEIGH (eBGP connections)
# - RRCLIENTNEIGH (Route reflector clients)
```

**Step 4: Extract Connections**
```python
import re

connections = []
devices = set()

# Get current device from HOSTNAME
current_device = None
for line in attr_content.split('\n'):
    if line.startswith('HOSTNAME'):
        current_device = line.split()[1]
        devices.add(current_device)

# 1. CUSTOMERLAG - Connections to co-cor and co-agg
for line in attr_content.split('\n'):
    if 'CUSTOMERLAG' in line and 'DESC' in line:
        parts = line.split()
        customer_device = parts[-1]
        devices.add(customer_device)
        connections.append({
            'source': current_device,
            'target': customer_device,
            'type': 'customer'
        })

# 2. RINGLAG - Ring connections to other np-cor sites
for line in attr_content.split('\n'):
    if 'RINGLAG' in line and 'DESC' in line:
        parts = line.split()
        ring_device = parts[-1]
        devices.add(ring_device)
        connections.append({
            'source': current_device,
            'target': ring_device,
            'type': 'ring'
        })

# 3. Inter-region NAP connections (pattern varies by site)
# Look for lines like "NAPBJSPEK PEER" or similar patterns
for line in attr_content.split('\n'):
    if 'PEER' in line and 'NAP' in line.upper():
        parts = line.split()
        if len(parts) >= 3:
            peer_device = parts[-1]
            devices.add(peer_device)
            connections.append({
                'source': current_device,
                'target': peer_device,
                'type': 'nap_inter_region'
            })
    # Also check for firewall peers
    if 'FWPEER' in line:
        parts = line.split()
        fw_device = parts[-1]
        devices.add(fw_device)
        connections.append({
            'source': current_device,
            'target': fw_device,
            'type': 'nap_firewall'
        })
```

**Step 5: Group Devices**
```python
# Group r101+r102 → r10[12]
# Group r1+r2 → r[12] (for co-cor, co-agg)

def group_devices(devices):
    from collections import defaultdict
    groups = defaultdict(list)
    
    for device in devices:
        if device.endswith('-r101'):
            base = device[:-5]
            groups[base].append(device)
        elif device.endswith('-r102'):
            base = device[:-5]
            groups[base].append(device)
        elif device.endswith('-r1'):
            base = device[:-3]
            groups[base].append(device)
        elif device.endswith('-r2'):
            base = device[:-3]
            groups[base].append(device)
        else:
            groups[device] = [device]
    
    grouped = {}
    for base, members in groups.items():
        if len(members) == 2:
            if any('-r101' in m for m in members):
                grouped_name = f"{base}-r10[12]"
            else:
                grouped_name = f"{base}-r[12]"
            for member in members:
                grouped[member] = grouped_name
        else:
            grouped[members[0]] = members[0]
    
    return grouped
```

**Step 6: Remove Duplicates**
```python
def deduplicate_connections(connections, device_groups):
    unique = {}
    for conn in connections:
        src = device_groups.get(conn['source'], conn['source'])
        tgt = device_groups.get(conn['target'], conn['target'])
        
        # Skip self-connections
        if src == tgt:
            continue
        
        # Normalize key (alphabetically sorted)
        key = tuple(sorted([src, tgt])) + (conn['type'],)
        if key not in unique:
            unique[key] = {'source': src, 'target': tgt, 'type': conn['type']}
    
    return list(unique.values())
```

**Step 7: File Output Location**

⚠️ **CRITICAL: Output files MUST be saved OUTSIDE the project folder**

```python
import os

# CORRECT: Save to Desktop
desktop_path = os.path.expanduser("~/Desktop")
output_file = os.path.join(desktop_path, f"{site}_corp_nap_topology.drawio")

# WRONG: Never save inside project folder
# /Users/anishkt/anish_topo_Agent_Project/corp_nap_fabric_draw_agent/
```

**File naming convention**: `{site}_corp_nap_topology.drawio`
- Example: `bjs11-11_corp_nap_topology.drawio`
- Location: `/Users/anishkt/Desktop/bjs11-11_corp_nap_topology.drawio`

**Step 8: Generate draw.io XML**
```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Use ElementTree (handles HTML escaping)
# Color code by device type
# Remove self-connections
# Deduplicate edges
```

### ⚠️ CRITICAL RULES

1. **ALWAYS fetch fresh data** from code.amazon.com
2. **NEVER cache .attr files** - always use builder-mcp
3. **Parse ONLY required sections**:
   - ✅ # customer lags (CUSTOMERLAG with DESC)
   - ✅ # customer interfaces (CUSTOMERINTF with DESC)
   - ✅ #RING Interfaces (RINGINTF with DESC)
   - ✅ #RING Lag Interfaces (RINGLAG with DESC)
   - ✅ Inter-region NAP connections (e.g., NAPBJSPEK PEER, FWPEER)
   - ❌ IBGPNEIGH (iBGP - EXCLUDE)
   - ❌ EBGPNEIGH (eBGP - EXCLUDE)
   - ❌ RRCLIENTNEIGH (Route reflector - EXCLUDE)
4. **Group devices** (r101+r102 → r10[12], r1+r2 → r[12])
5. **Remove duplicates** after grouping
6. **Save output files OUTSIDE project folder** (to Desktop)

---

## User Input

User provides **ONLY the site identifier**:
- Example: `bjs11-11`, `iad12-12`, `pdx50-50`

Agent automatically constructs the URL and fetches data.

---

## URL Construction Pattern

### Generic URL Structure

**Base URL** (Common for all):
```
https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--
```

**Variable Path** (Changes based on site):
```
/targetspec/nap-{region}/{site}-np-cor-r/{site}-np-cor-r101/routerspecific.attr
```

### Construction Rules

**Pattern**:
```
{BASE_URL}/targetspec/nap-{region}/{site}-np-cor-r/{site}-np-cor-r101/routerspecific.attr
```

**Variables**:
- `{region}`: Extracted from site (e.g., bjs11-11 → bjs)
- `{site}`: User-provided site identifier (e.g., bjs11-11, iad12-12)

### Examples

**BJS11-11**:
```
Input: bjs11-11
Region: bjs
URL: https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/nap-bjs/bjs11-11-np-cor-r/bjs11-11-np-cor-r101/routerspecific.attr
```

**IAD12-12**:
```
Input: iad12-12
Region: iad
URL: https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/nap-iad/iad12-12-np-cor-r/iad12-12-np-cor-r101/routerspecific.attr
```

**NRT55-62**:
```
Input: nrt55-62
Region: nrt
URL: https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/nap-nrt/nrt55-62-np-cor-r/nrt55-62-np-cor-r101/routerspecific.attr
```

### Implementation

```python
def construct_attr_url(site: str) -> str:
    # Extract region (first letters before numbers)
    region = site.split('-')[0]  # e.g., bjs11-11 → bjs
    
    # Construct URL
    base_url = "https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--"
    path = f"/targetspec/nap-{region}/{site}-np-cor-r/{site}-np-cor-r101/routerspecific.attr"
    
    return base_url + path
```

### Key Points

1. **Base URL is constant** - never changes
2. **Region is extracted** from site identifier (first 3 letters)
3. **Site is used multiple times** in the path
4. **Device is always r101** for configuration file
5. **File is always routerspecific.attr**

---

## Data Source Format

### .attr File Structure

The routerspecific.attr file contains key-value configuration pairs:

```
HOSTNAME bjs11-11-np-cor-r101
PRIMARYIP 10.191.28.4

# customer lags
CUSTOMERLAG ae40 DESC bjs11-11-co-cor-r1
CUSTOMERLAG ae41 DESC bjs11-11-co-agg-r1

# customer interfaces
CUSTOMERINTF xe-0/0/72 DESC bjs11-11-co-cor-r1
CUSTOMERINTF xe-0/0/72 LAG ae40

#RING Lag Interfaces
RINGLAG ae1 DESC bjs10-10-np-cor-r101
RINGLAG ae2 DESC bjs12-12-np-cor-r101

#RING Interfaces
RINGINTF xe-0/0/0 DESC bjs10-10-np-cor-r101
RINGINTF xe-0/0/0 LAG ae1

# NAP CONNECTION BJS AND PEK (inter-region)
NAPBJSPEK PEER pek50-50-np-cor-r101
NAPBJSPEK FWPEER pek50-50-np-cor-fw2
```

---

## Connection Parsing Rules

### ✅ INCLUDE These Sections

1. **Customer LAGs** (`# customer lags`)
   - Parse: `CUSTOMERLAG` lines with `DESC`
   - Extracts: Connections to co-cor and co-agg devices
   - Example: `CUSTOMERLAG ae40 DESC bjs11-11-co-cor-r1`

2. **Customer Interfaces** (`# customer interfaces`)
   - Parse: `CUSTOMERINTF` lines with `DESC`
   - Extracts: Physical interface connections
   - Example: `CUSTOMERINTF xe-0/0/72 DESC bjs11-11-co-cor-r1`

3. **Ring LAG Interfaces** (`#RING Lag Interfaces`)
   - Parse: `RINGLAG` lines with `DESC`
   - Extracts: Ring connections to other np-cor sites
   - Example: `RINGLAG ae1 DESC bjs10-10-np-cor-r101`

4. **Ring Interfaces** (`#RING Interfaces`)
   - Parse: `RINGINTF` lines with `DESC`
   - Extracts: Physical ring interface connections
   - Example: `RINGINTF xe-0/0/0 DESC bjs10-10-np-cor-r101`

5. **Inter-Region NAP Connections**
   - Look for comment patterns like `# NAP CONNECTION BJS AND PEK`
   - Parse: Lines with `PEER` keyword (e.g., `NAPBJSPEK PEER`)
   - Parse: Lines with `FWPEER` keyword for firewall connections
   - **Important**: Connection names vary by site (not always BJS-PEK)
   - Example: `NAPBJSPEK PEER pek50-50-np-cor-r101`
   - Example: `NAPBJSPEK FWPEER pek50-50-np-cor-fw2`

### ❌ EXCLUDE These Sections

1. **IBGPNEIGH** - iBGP neighbor connections (BGP peering only)
2. **EBGPNEIGH** - eBGP neighbor connections (BGP peering only)
3. **RRCLIENTNEIGH** - Route reflector clients (BGP peering only)

---

## Implementation Steps

### Step 1: URL Generation
```python
site = "bjs11-11"  # User input
region = site[:3]   # Extract first 3 letters
url = f"https://code.amazon.com/packages/GenevaBuilderDCNE/blobs/mainline/--/targetspec/nap-{region}/{site}-np-cor-r/{site}-np-cor-r101/routerspecific.attr"
```

### Step 2: Fetch Configuration
```python
# Use builder-mcp ReadInternalWebsites tool
# ALWAYS fetch fresh - never use cached data
```

### Step 3: Parse Connections
```python
def parse_attr_content(content):
    devices = set()
    connections = []
    
    # Get HOSTNAME
    current_device = None
    for line in content.split('\n'):
        if line.startswith('HOSTNAME'):
            current_device = line.split()[1]
            devices.add(current_device)
    
    # Parse CUSTOMERLAG
    for line in content.split('\n'):
        if 'CUSTOMERLAG' in line and 'DESC' in line:
            parts = line.split()
            customer = parts[-1]
            devices.add(customer)
            connections.append({
                'source': current_device,
                'target': customer,
                'type': 'customer'
            })
    
    # Parse RINGLAG
    for line in content.split('\n'):
        if 'RINGLAG' in line and 'DESC' in line:
            parts = line.split()
            ring_peer = parts[-1]
            devices.add(ring_peer)
            connections.append({
                'source': current_device,
                'target': ring_peer,
                'type': 'ring'
            })
    
    # Parse inter-region NAP connections
    for line in content.split('\n'):
        if 'PEER' in line and not line.startswith('#'):
            parts = line.split()
            if len(parts) >= 3:
                peer = parts[-1]
                devices.add(peer)
                connections.append({
                    'source': current_device,
                    'target': peer,
                    'type': 'nap_inter_region'
                })
    
    return list(devices), connections
```

### Step 4: Group Devices
```python
def group_devices(devices):
    from collections import defaultdict
    groups = defaultdict(list)
    
    for device in devices:
        if device.endswith('-r101'):
            base = device[:-5]
            groups[base].append(device)
        elif device.endswith('-r102'):
            base = device[:-5]
            groups[base].append(device)
        elif device.endswith('-r1'):
            base = device[:-3]
            groups[base].append(device)
        elif device.endswith('-r2'):
            base = device[:-3]
            groups[base].append(device)
        else:
            groups[device] = [device]
    
    grouped = {}
    for base, members in groups.items():
        if len(members) == 2:
            if any('-r101' in m for m in members):
                grouped_name = f"{base}-r10[12]"
            else:
                grouped_name = f"{base}-r[12]"
            for member in members:
                grouped[member] = grouped_name
        else:
            grouped[members[0]] = members[0]
    
    return grouped
```

### Step 5: Remove Duplicates
```python
def deduplicate_connections(connections, device_groups):
    unique = {}
    for conn in connections:
        src = device_groups.get(conn['source'], conn['source'])
        tgt = device_groups.get(conn['target'], conn['target'])
        
        # Skip self-connections
        if src == tgt:
            continue
        
        # Normalize key (alphabetically sorted)
        key = tuple(sorted([src, tgt])) + (conn['type'],)
        if key not in unique:
            unique[key] = {'source': src, 'target': tgt, 'type': conn['type']}
    
    return list(unique.values())
```

### Step 6: File Output Location

⚠️ **CRITICAL: Output files MUST be saved OUTSIDE the project folder**

```python
import os

# CORRECT: Save to Desktop
desktop_path = os.path.expanduser("~/Desktop")
output_file = os.path.join(desktop_path, f"{site}_corp_nap_topology.drawio")

# WRONG: Never save inside project folder
# /Users/anishkt/anish_topo_Agent_Project/corp_nap_fabric_draw_agent/
```

**File naming convention**: `{site}_corp_nap_topology.drawio`
- Example: `bjs11-11_corp_nap_topology.drawio`
- Location: `/Users/anishkt/Desktop/bjs11-11_corp_nap_topology.drawio`

### Step 7: Generate draw.io XML
```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_drawio_xml(devices, connections, site):
    # Create XML structure using ElementTree
    # Color code by device type
    # Layout in grid
    # Add connections with proper colors
    pass
```

---

## Color Scheme

| Device Type | Color | Hex Code | Description |
|------------|-------|----------|-------------|
| np-cor | Light Orange | #FFE6CC | NAP core routers |
| co-cor | Light Green | #D5E8D4 | Corp core routers |
| co-agg | Light Blue | #DAE8FC | Corp aggregation |
| fw | Light Red | #F8CECC | Firewalls |

| Connection Type | Color | Hex Code | Description |
|----------------|-------|----------|-------------|
| customer | Blue | #0066CC | Customer connections |
| ring | Green | #009900 | Ring connections |
| nap_inter_region | Red | #CC0000 | Inter-region NAP |
| nap_firewall | Red | #CC0000 | Firewall connections |

---

## Example: BJS11-11

### Input
```
Site: bjs11-11
```

### Expected Output

**Devices (after grouping)**:
- bjs11-11-np-cor-r10[12] (grouped from r101+r102)
- bjs11-11-co-cor-r1
- bjs11-11-co-agg-r1
- bjs10-10-np-cor-r10[12]
- bjs12-12-np-cor-r10[12]
- bjs20-20-np-cor-r10[12]
- bjs80-80-np-cor-r10[12]
- bjs9-9-np-cor-r10[12]
- bjs11-51-np-cor-r101
- bjs11-52-np-cor-r101
- pek50-50-np-cor-r101
- pek50-50-np-cor-fw2

**Connections**:
- Customer: 2 (to co-cor-r1, co-agg-r1)
- Ring: 6 (to other np-cor sites)
- Inter-region NAP: 2 (to pek50-50 router and firewall)

---

## Validation Checklist

- [ ] URL generation works for any site
- [ ] Fresh data fetched from code.amazon.com
- [ ] Only required sections parsed (customer, ring, inter-region NAP)
- [ ] iBGP and eBGP connections excluded
- [ ] Device grouping (r101+r102 → r10[12])
- [ ] Duplicates removed
- [ ] Output saved to Desktop (outside project folder)
- [ ] Color coding by device type
- [ ] Plain XML output
- [ ] Fully editable in draw.io

---

## Key Features

### Self-Sufficient
- ✅ Works from scratch with just site identifier
- ✅ Automatic URL generation
- ✅ Fresh data fetching (never uses cache)
- ✅ Complete documentation

### Smart Grouping
- ✅ Device pair grouping (r101+r102 → r10[12])
- ✅ Device pair grouping (r1+r2 → r[12])
- ✅ Handles single devices (fw2, r101 only)
- ✅ Preserves device naming conventions

### Clean Output
- ✅ Color-coded by device type
- ✅ Plain XML (no compression)
- ✅ Fully editable in draw.io
- ✅ No self-connections
- ✅ Deduplicated edges
- ✅ Saved outside project folder

---

**Status**: Requirements Updated
**Data Source**: GenevaBuilderDCNE .attr files
**Output Location**: Desktop (outside project folder)