# Topology Generator Agents - Quick Start Guide

**Location**: `/Users/anishkt/anish_topo_Agent_Project/`

---

## ⚠️ CRITICAL: Each Agent Uses DIFFERENT Data Sources

**DO NOT mix up the data sources!** Each agent type has:
- ✅ Different URL patterns
- ✅ Different file formats
- ✅ Different parsing logic
- ✅ Different connection extraction methods

---

## 📋 Agent Selection Matrix

| Fabric Type | Agent Directory | Data Source | File Format |
|------------|----------------|-------------|-------------|
| **UMN EC2** (es-mgmt-cor) | `umn_ec2_fabric_draw_Agent` | SwitchBuilder **Brick** | JSON |
| **EC2** (es-c1) | `ec2_fabric_draw_Agent` | FabricBuilder **YAML** | YAML |
| **PROD** (ws-c1) | `prod_fabric_draw_Agent` | FabricBuilder **YAML** | YAML |
| **Corp NAP** (np-cor) | `corp_nap_fabric_draw_agent` | **Network Tools** | API Response |
| **Console** (es-mgmt) | `console_fabric_draw_Agent` | SwitchBuilder **Brick** | JSON |

---

## 🚀 UMN EC2 Topology (es-mgmt-cor)

### ⚠️ UNIQUE TO UMN EC2
- **Data Source**: SwitchBuilder **Brick Definition** files
- **Package**: `SwitchBuilderBrickDef-EC2-{REGION}`
- **File Type**: `.brick` (returns JSON)
- **Key Sections**: `DEVICE_DETAILS`, `NODES_AND_INTERFACES`

### URL Pattern (SPECIFIC TO UMN EC2)
```
https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-{REGION}/blobs/mainline/--/configuration/etc/brick/EC2-{REGION}/{region}-es-mgmt-cor.brick
```

### Complete Workflow
```python
# 1. Generate URL
site = "nrt55-55"
region = site[:3]  # "nrt"
REGION = region.upper()  # "NRT"
url = f"https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-{REGION}/blobs/mainline/--/configuration/etc/brick/EC2-{REGION}/{region}-es-mgmt-cor.brick"

# 2. Fetch (ALWAYS FRESH)
use_mcp_tool(server_name="amzn-mcp", tool_name="read_internal_website", url=url)

# 3. Parse
brick_data = json.loads(mcp_response['content'])
devices = brick_data['DEVICE_DETAILS']
nodes = brick_data['NODES_AND_INTERFACES']

# 4. Extract connections (es-mgmt-cor to es-mgmt-cor only)
# 5. Filter for ROOT AZ + inter-AZ
# 6. Group: r[12] pairs (v1 separate for ROOT DC)
# 7. Generate draw.io XML
```

### Examples
- bjs11-11 → `.../EC2-BJS/.../bjs-es-mgmt-cor.brick`
- nrt55-55 → `.../EC2-NRT/.../nrt-es-mgmt-cor.brick`
- iad12-12 → `.../EC2-IAD/.../iad-es-mgmt-cor.brick`

### 📖 Full Details
[`umn_ec2_fabric_draw_Agent/REQUIREMENTS.md`](umn_ec2_fabric_draw_Agent/REQUIREMENTS.md:1)

---

## 🚀 EC2 Fabric Topology (es-c1)

### ⚠️ UNIQUE TO EC2 FABRIC
- **Data Source**: FabricBuilder **Site Configs** (YAML)
- **Package**: `FabricBuilderSiteConfigs`
- **File Type**: `.yaml` (YAML format)
- **Key Sections**: `bricks`, `neighbors`

### URL Pattern (SPECIFIC TO EC2 FABRIC)
```
https://code.amazon.com/packages/FabricBuilderSiteConfigs/blobs/mainline/--/site-configs/{site}-es-c1.yaml
```

### Complete Workflow
```python
# 1. Generate ROOT URL
site = "bjs11-11"
url = f"https://code.amazon.com/packages/FabricBuilderSiteConfigs/blobs/mainline/--/site-configs/{site}-es-c1.yaml"

# 2. Fetch ROOT YAML (ALWAYS FRESH)
use_mcp_tool(server_name="amzn-mcp", tool_name="read_internal_website", url=url)

# 3. Discover neighbors from YAML
neighbors = yaml_data['neighbors']  # BFC, OneFabric

# 4. Fetch neighbor YAMLs (recursive for intra-AZ)
for neighbor in neighbors:
    neighbor_url = f".../site-configs/{neighbor}-es-c1.yaml"
    fetch_yaml(neighbor_url)

# 5. Extract connections from 'bricks' section
# 6. Normalize device names (remove brick suffixes)
# 7. Generate draw.io XML
```

### Examples
- bjs11-11 → `.../site-configs/bjs11-11-es-c1.yaml`
- iad12-12 → `.../site-configs/iad12-12-es-c1.yaml`

### 📖 Full Details
[`ec2_fabric_draw_Agent/REQUIREMENTS.md`](ec2_fabric_draw_Agent/REQUIREMENTS.md:1)

---

## 🚀 PROD Fabric Topology (ws-c1)

### ⚠️ UNIQUE TO PROD FABRIC
- **Data Source**: FabricBuilder **Site Configs** (YAML)
- **Package**: `FabricBuilderSiteConfigs`
- **File Type**: `.yaml` (ws-c1 variant)
- **Special**: Includes `ws-cor` (workspace core) - NO YAML for ws-cor!

### URL Pattern (SPECIFIC TO PROD FABRIC)
```
https://code.amazon.com/packages/FabricBuilderSiteConfigs/blobs/mainline/--/site-configs/{site}-ws-c1.yaml
```

### Key Difference from EC2
- Uses `ws-c1` instead of `es-c1`
- Includes `ws-cor` devices (extracted from ROOT neighbors, no YAML fetch)

### 📖 Full Details
[`prod_fabric_draw_Agent/REQUIREMENTS.md`](prod_fabric_draw_Agent/REQUIREMENTS.md:1)

---

## 🚀 Corp NAP Topology (np-cor)

### ⚠️ UNIQUE TO CORP NAP
- **Data Source**: **Network Topology Tools** (NOT files!)
- **Tool**: `network_location_topology`
- **Method**: Dynamic neighbor traversal
- **NO URLs**: Uses network API

### Workflow (COMPLETELY DIFFERENT)
```python
# 1. Query network tool (NO URL generation)
location = f"{site}-np-cor-r101"
topology = network_location_topology(location)

# 2. Extract neighbors from response
# 3. Traverse neighbors recursively
# 4. Build topology dynamically
# 5. Generate draw.io XML
```

### ⚠️ Critical Rules
- ❌ NEVER use cached discovery data
- ✅ ALWAYS query network tools fresh
- ✅ NO file fetching - uses network API

### 📖 Full Details
[`corp_nap_fabric_draw_agent/REQUIREMENTS.md`](corp_nap_fabric_draw_agent/REQUIREMENTS.md:1)

---

## 🚀 Console Fabric Topology (es-mgmt)

### ⚠️ UNIQUE TO CONSOLE
- **Data Source**: SwitchBuilder **Brick Definition** files
- **Package**: `SwitchBuilderBrickDef-EC2-{REGION}`
- **File Type**: `.brick` (similar to UMN EC2)
- **Focus**: Console management fabric

### Similar to UMN EC2 but different fabric focus

### 📖 Full Details
[`console_fabric_draw_Agent/AGENT_REQUIREMENTS.md`](console_fabric_draw_Agent/AGENT_REQUIREMENTS.md:1)

---

## 🎯 Summary: Data Source Differences

### File-Based Agents

**1. UMN EC2 & Console** (Brick files):
```
Package: SwitchBuilderBrickDef-EC2-{REGION}
File: {region}-es-mgmt-cor.brick
Format: JSON
Sections: DEVICE_DETAILS, NODES_AND_INTERFACES
```

**2. EC2 & PROD** (YAML files):
```
Package: FabricBuilderSiteConfigs
File: {site}-{es-c1|ws-c1}.yaml
Format: YAML
Sections: bricks, neighbors
```

### Tool-Based Agents

**3. Corp NAP** (Network tools):
```
Tool: network_location_topology
Input: {site}-np-cor-r101
Format: API Response
Method: Dynamic traversal
```

---

## ⚠️ Common Mistakes to Avoid

1. ❌ Using EC2 YAML URLs for UMN EC2 (wrong - UMN uses brick files!)
2. ❌ Using brick files for EC2 fabric (wrong - EC2 uses YAML!)
3. ❌ Looking for Corp NAP files (wrong - uses network tools!)
4. ❌ Using cached/saved data (wrong - always fetch fresh!)
5. ❌ Mixing up package names (each agent has specific package)

---

## ✅ Correct Approach

**When you get a request**:
1. ✅ Identify fabric type from request
2. ✅ Select correct agent
3. ✅ Use that agent's SPECIFIC URL pattern/tool
4. ✅ Fetch fresh data using correct method
5. ✅ Follow that agent's specific parsing logic
6. ✅ Generate topology

**Each agent is self-contained** - read its REQUIREMENTS.md for complete instructions.

---

**Version**: 1.0
**Last Updated**: 2024-11-04
**Status**: ✅ Complete Guide for All 5 Agents