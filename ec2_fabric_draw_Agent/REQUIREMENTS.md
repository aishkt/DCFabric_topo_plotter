# EC2 Fabric Topology Generator - Requirements V2 (Optimized)

## Overview
Generate EC2 fabric topology diagrams showing BFC and OneFabric devices with their interconnections. **Optimized to fetch only intra-AZ neighbor YAMLs** - significantly faster!

---

## 🚀 Quick Start - Create Topology from Scratch (OPTIMIZED)

**When you receive a request to create EC2 fabric topology for ANY site:**

### Complete Workflow (5 Steps - Optimized)

**Step 1: Generate ROOT YAML URL**
```python
# Generic formula - works for ANY site
site = "{USER_PROVIDED_SITE}"  # e.g., "nrt12-12", "iad12-12", "bjs11-11", "pdx50-50", etc.
url = f"https://code.amazon.com/packages/FabricBuilderSiteConfigs/blobs/mainline/--/site-configs/{site}-es-c1.yaml"

# The formula automatically constructs the correct URL for any site
```

**Step 2: Fetch ROOT YAML (ALWAYS FRESH)**
```
use_mcp_tool(
  server_name="amzn-mcp",
  tool_name="read_internal_website",
  url="<URL from Step 1>"
)
```

**Step 3: Discover BFC/OneFabric Neighbors**
```python
# From ROOT YAML 'neighbors' section:
neighbors = yaml_data['neighbors']

# Filter for BFC and OneFabric only:
key_neighbors = [name for name, data in neighbors.items() 
                 if data.get('type') in ['bfc', 'onefabric']]

# Separate by AZ:
# - Intra-AZ: nrt12-56, nrt12-64, nrt12-72, nrt12-73 (same AZ as ROOT)
# - Inter-AZ: nrt55-55, nrt8-20, nrt7-7 (different AZ)
```

**Step 4: Fetch INTRA-AZ Neighbor YAMLs ONLY**
```python
# OPTIMIZATION: Only fetch intra-AZ neighbors
# This logic works for ANY site automatically

for neighbor in key_neighbors:
    normalized = normalize_device_name(neighbor)
    neighbor_az = extract_az(normalized)  # Extract AZ from device name
    root_az = extract_az(site)            # Extract AZ from ROOT site
    
    if neighbor_az == root_az:  # Same AZ as ROOT
        url = f"https://code.amazon.com/.../site-configs/{normalized}.yaml"
        fetch_yaml(url)  # Use MCP tool
        print(f"✓ Fetched: {normalized} (intra-AZ)")
    else:
        print(f"⏭️  Skipped: {normalized} (inter-AZ - only connects to ROOT)")

# This automatically identifies intra-AZ vs inter-AZ for ANY site
```

**Step 5: Generate Topology**
```bash
# Run generator with fetched YAMLs - works for ANY site
python3 ec2_fabric_generator.py --site {SITE} --fabric es-c1

# Output: /Users/anishkt/{SITE}-es-c1-topology/{SITE}-es-c1-topology.drawio
```

---

## 🎯 Optimization Strategy

### Why This Works

**Inter-AZ Devices (Different AZ from ROOT):**
- Typically connect ONLY to ROOT
- Generic pattern: {OTHER_AZ} → {ROOT_AZ}
- No need to fetch their YAML
- Connection already known from ROOT YAML
- **Automatically detected** by comparing AZ prefixes

**Intra-AZ Devices (Same AZ as ROOT):**
- Form a MESH topology
- Generic pattern: {SAME_AZ}-{DC1} ↔ {SAME_AZ}-{DC2} ↔ {SAME_AZ}-{DC3}
- MUST fetch their YAMLs to discover mesh connections
- These connections NOT in ROOT YAML
- **Automatically detected** by matching AZ prefixes

### Generic Example: Any Site

**ROOT YAML ({SITE}-es-c1):**
```yaml
neighbors:
  {OTHER_AZ}-{DC}-es-c1:     # Inter-AZ ← SKIP
    type: bfc
  {SAME_AZ}-{DC1}-es-c1:     # Intra-AZ ← FETCH
    type: bfc
  {SAME_AZ}-{DC2}-es-e1:     # Intra-AZ ← FETCH
    type: onefabric
```

**Fetching Strategy (Generic):**
```python
# Extract ROOT AZ
root_az = extract_az(site)  # e.g., "nrt12" from "nrt12-12"

# For each neighbor:
for neighbor in neighbors:
    neighbor_az = extract_az(neighbor)
    
    if neighbor_az == root_az:
        fetch_yaml(neighbor)  # ✅ Intra-AZ - fetch
    else:
        skip(neighbor)        # ❌ Inter-AZ - skip

# This logic works for ANY site automatically!
```

---

## 📊 Typical Results

### Generic Site Pattern

**YAMLs Fetched:** ROOT + intra-AZ neighbors
- {SITE}-es-c1 (ROOT)
- {SAME_AZ}-{DC1}-es-c1 (intra-AZ BFC)
- {SAME_AZ}-{DC2}-es-c1 (intra-AZ BFC)
- {SAME_AZ}-{DC3}-es-e1 (intra-AZ OneFabric)
- ... (all intra-AZ neighbors)

**Devices in Topology:** Varies by site
- 1 ROOT
- N Inter-AZ BFC (different AZ)
- M Intra-AZ BFC (same AZ)
- K OneFabric (same AZ)

**Connections:** Varies by site
- ROOT to inter-AZ
- ROOT to intra-AZ
- Intra-AZ mesh connections

---

## 🔑 Key Rules

### Device Naming
- **Normalize**: `nrt12-56-es-c1-b4` → `nrt12-56-es-c1`
- **Keep full name**: Don't abbreviate
- **Show fabric**: Include fabric type in label

### Fetching Strategy
- ✅ **Always fetch**: ROOT YAML
- ✅ **Fetch if same AZ**: Intra-AZ neighbors (for mesh connections)
- ❌ **Skip if different AZ**: Inter-AZ neighbors (only connect to ROOT)

### Connection Rules
- **No grouping**: Each connection is separate
- **No labels**: Don't label connection lines
- **No color coding**: All connections same color
- **Bidirectional**: Treat as single undirected edge

### Filtering Rules
- **Include**: BFC, OneFabric
- **Exclude**: Euclid (unless OneFabric), Service routers, Core routers, Console, Tarmac

---

## 📁 Output Structure

```
/Users/anishkt/{site}-{fabric}-topology/
├── yaml-configs/              # Cached YAML files (as JSON)
│   ├── nrt12-12-es-c1.json   # ROOT
│   ├── nrt12-56-es-c1.json   # Intra-AZ
│   ├── nrt12-64-es-c1.json   # Intra-AZ
│   ├── nrt12-72-es-c1.json   # Intra-AZ
│   └── nrt12-73-es-e1.json   # Intra-AZ OneFabric
├── analysis/                  # Connection analysis
│   ├── devices.json
│   └── connections.json
└── nrt12-12-es-c1-topology.drawio  # Final topology
```

---

## 🎓 Understanding the Optimization

### Why Skip Inter-AZ YAMLs?

**Inter-AZ Topology Pattern:**
```
nrt55-55 (AZ: nrt55)
    ↓
nrt12-12 (AZ: nrt12) ← ROOT
    ↓
nrt8-20 (AZ: nrt8)
```

Inter-AZ devices connect to ROOT but typically NOT to each other directly. The ROOT YAML already tells us:
- nrt55-55 connects to nrt12-12 ✓
- nrt8-20 connects to nrt12-12 ✓

We don't need nrt55-55's YAML to know this!

### Why Fetch Intra-AZ YAMLs?

**Intra-AZ Mesh Pattern:**
```
nrt12-56 ←→ nrt12-64
    ↓  ↘   ↙  ↓
nrt12-12 ←→ nrt12-72
    ↓         ↓
nrt12-73 (OneFabric)
```

Intra-AZ devices form a mesh. To discover:
- nrt12-56 ↔ nrt12-64 connection
- nrt12-73 ↔ nrt12-56 connection
- nrt12-73 ↔ nrt12-64 connection

We MUST fetch their YAMLs!

---

## ⚡ Performance Comparison

### Old Approach (Recursive)
- Fetch ROOT: 1 YAML
- Fetch all neighbors: 11 YAMLs
- Fetch neighbor's neighbors: 5+ YAMLs
- **Total: 17+ YAMLs**

### New Approach (Optimized)
- Fetch ROOT: 1 YAML
- Fetch intra-AZ only: 4 YAMLs
- **Total: 5 YAMLs (70% reduction!)**

### Result
- ✅ Same topology quality
- ✅ All connections captured
- ✅ 70% fewer API calls
- ✅ Much faster generation

---

## 🧪 Validation

### Test Case: nrt12-12

**Expected Devices:** 8
- 1 ROOT (nrt12-12-es-c1)
- 3 Inter-AZ (nrt55-55, nrt8-20, nrt7-7)
- 3 Intra-AZ (nrt12-56, nrt12-64, nrt12-72)
- 1 OneFabric (nrt12-73-es-e1)

**Expected Connections:** 15
- ROOT to inter-AZ: 3
- ROOT to intra-AZ: 4
- Intra-AZ mesh: 8

**YAMLs Fetched:** 5
- nrt12-12-es-c1 (ROOT)
- nrt12-56-es-c1 (intra-AZ)
- nrt12-64-es-c1 (intra-AZ)
- nrt12-72-es-c1 (intra-AZ)
- nrt12-73-es-e1 (intra-AZ)

✅ **Validated**: All connections captured with 70% fewer YAMLs!

---

**Status**: ✅ Optimized and Validated
**Version**: 2.0
**Last Updated**: 2024-11-10
**Optimization**: Intra-AZ only fetching (70% reduction in API calls)