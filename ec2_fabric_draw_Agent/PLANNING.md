# EC2 Fabric Topology Generator - Planning Document

## Overview
Generic agent to generate EC2 fabric (es-c1) topology diagrams for ANY AWS region/AZ.

---

## Data Source Analysis

### YAML File Pattern
```
https://code.amazon.com/packages/FabricBuilderSiteConfigs/blobs/mainline/--/site-configs/{site}-es-c1.yaml
```

**Examples**:
- BJS11-11: `bjs11-11-es-c1.yaml`
- BJS12-12: `bjs12-12-es-c1.yaml`
- IAD12-12: `iad12-12-es-c1.yaml`
- NRT12-12: `nrt12-12-es-c1.yaml`

### YAML Structure
```yaml
site:
    name: {site}-es-c1
    region: EC2-{REGION}
    topology: bfc-{config}
    
bricks:
    brick1:
        neighbors:
            {neighbor-name}:
                brick_number: X
                positions: [...]
    brick2:
        ...
    
neighbors:
    {neighbor-name}:
        type: bfc|euclid|single|...
        topology: ...
        peer_group: ...
        bgp_asn: ...
```

---

## Generic Design Strategy

### 1. Input Parameters
```bash
python3 ec2_fabric_generator.py --site bjs11-11 --fabric es-c1
python3 ec2_fabric_generator.py --site iad12-12 --fabric es-c1
```

### 2. URL Construction (Generic)
```python
def construct_yaml_url(site: str, fabric: str) -> str:
    """
    Construct URL for any site/fabric combination
    
    Examples:
        bjs11-11, es-c1 → .../bjs11-11-es-c1.yaml
        iad12-12, es-c1 → .../iad12-12-es-c1.yaml
    """
    url = f"https://code.amazon.com/packages/FabricBuilderSiteConfigs/blobs/mainline/--/site-configs/{site}-{fabric}.yaml"
    return url
```

### 3. Device Discovery Strategy

#### From YAML Structure
```
Target Site (bjs11-11-es-c1)
├── Bricks (brick1, brick2, ..., brick11)
│   └── Each brick has T1 devices (r13-r28 typically)
│
└── Neighbors (discovered from brick connections)
    ├── BFC Neighbors (other es-c1 fabrics)
    │   ├── Inter-AZ: bjs12-12-es-c1, bjs20-20-es-c1, bjs80-80-es-c1
    │   └── Intra-AZ: bjs11-50-es-c1, bjs11-51-es-c1
    │
    ├── Edge Neighbors (Euclid)
    │   ├── bjs11-11-es-e1
    │   ├── bjs11-11-es-e2
    │   └── bjs11-52-es-e1
    │
    ├── Service Neighbors (es-svc)
    │   ├── PUB: r113-r136
    │   ├── VPC: r205-r216, r311-r312, r321-r324
    │   └── AP: r601-r620
    │
    ├── Core Neighbors
    │   └── bjs11-11-es-cor
    │
    ├── Console Fabric
    │   └── bjs11-11-es-mgmt-cor-r1
    │
    └── Tarmac
        └── bjs11-11-es-tar-r201
```

---

## Visualization Strategy

### Option A: Brick-Centric View (Recommended)
**Focus**: Show bricks as primary nodes, neighbors as secondary

```
Layout:
┌─────────────────────────────────────────────────────────┐
│  Target Site BFC (bjs11-11-es-c1)                       │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │Brick 1 │ │Brick 2 │ │Brick 3 │ │Brick 4 │ ...      │
│  └────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  BFC Neighbors (Inter-AZ)                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │bjs12-12-es-c1│ │bjs20-20-es-c1│ │bjs80-80-es-c1│   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  BFC Neighbors (Intra-AZ)                               │
│  ┌──────────────┐ ┌──────────────┐                     │
│  │bjs11-50-es-c1│ │bjs11-51-es-c1│                     │
│  └──────────────┘ └──────────────┘                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Edge Neighbors                                          │
│  ┌──────────────┐ ┌──────────────┐                     │
│  │bjs11-11-es-e1│ │bjs11-11-es-e2│                     │
│  └──────────────┘ └──────────────┘                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Service Routers (Grouped)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │PUB (r113-│ │VPC (r205-│ │AP (r601- │               │
│  │  r136)   │ │  r324)   │ │  r620)   │               │
│  └──────────┘ └──────────┘ └──────────┘               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Other Neighbors                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │bjs11-11-es-  │ │bjs11-11-es-  │ │bjs11-11-es-  │   │
│  │   cor        │ │ mgmt-cor-r1  │ │  tar-r201    │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Option B: Simplified View
**Focus**: Abstract bricks, show only neighbor relationships

```
┌──────────────────┐
│  bjs11-11-es-c1  │ (Target BFC - all bricks grouped)
│   (11 bricks)    │
└──────────────────┘
         │
         ├─→ Inter-AZ BFC: bjs12-12, bjs20-20, bjs80-80
         ├─→ Intra-AZ BFC: bjs11-50, bjs11-51
         ├─→ Edge: es-e1, es-e2
         ├─→ Service: es-svc (grouped)
         ├─→ Core: es-cor
         ├─→ Console: es-mgmt-cor
         └─→ Tarmac: es-tar
```

---

## Generic Implementation Plan

### Phase 1: Core Functionality
```python
class EC2FabricTopologyGenerator:
    def __init__(self, site: str, fabric: str):
        self.site = site          # e.g., "bjs11-11"
        self.fabric = fabric      # e.g., "es-c1"
        
    def construct_yaml_url(self) -> str:
        """Generic URL construction for any site"""
        return f".../{self.site}-{self.fabric}.yaml"
    
    def parse_yaml(self, yaml_content: str) -> Dict:
        """Parse YAML and extract topology data"""
        # Extract bricks, neighbors, connections
        
    def categorize_neighbor(self, neighbor_name: str, neighbor_data: Dict) -> str:
        """Categorize neighbor by type"""
        # BFC, Edge, Service, Core, Console, Tarmac
        
    def group_neighbors(self, neighbors: Dict) -> Dict:
        """Group neighbors by category"""
        # Inter-AZ BFC, Intra-AZ BFC, Edge, Service, etc.
```

### Phase 2: Visualization
- Color coding by neighbor type
- Brick-centric or simplified view
- Connection highlighting (Inter-AZ, Intra-AZ, Edge, Core)

### Phase 3: Generic Features
- Works for ANY AWS region (BJS, IAD, NRT, PDX, etc.)
- Works for ANY AZ/DC combination
- Automatic YAML URL construction
- Proper neighbor categorization

---

## Key Design Decisions Needed

### 1. Visualization Granularity
**Question**: How detailed should the diagram be?

**Options**:
- **High Detail**: Show all 11 bricks + all neighbors individually
  - Pros: Complete picture
  - Cons: Very large diagram (100+ nodes)
  
- **Medium Detail**: Show bricks grouped, neighbors categorized
  - Pros: Balanced view
  - Cons: Some detail lost
  
- **Low Detail**: Show target BFC + neighbor categories only
  - Pros: Clean, simple
  - Cons: Missing brick-level detail

**Recommendation**: Start with Medium Detail, add flag for High Detail

### 2. Service Router Handling
**Question**: How to handle 40+ es-svc routers?

**Options**:
- Show all individually (40+ nodes)
- Group by type (PUB, VPC, AP) → 3 nodes
- Group by range (r113-r120, r121-r128, etc.) → 8 nodes

**Recommendation**: Group by type (PUB, VPC, AP)

### 3. Connection Types
**Question**: Which connections to highlight?

**Priority**:
1. ⭐ Inter-AZ BFC (thick blue)
2. ⭐ Intra-AZ BFC (thick green)
3. Edge connections (medium orange)
4. Core connections (medium purple)
5. Service connections (thin gray)
6. Console connections (thin orange)

### 4. Generic Patterns
**Question**: How to make it work for any site?

**Strategy**:
```python
# Extract region from site
site = "bjs11-11"
region = site.split('-')[0].upper()  # "BJS"

# Construct URL
url = f".../site-configs/{site}-es-c1.yaml"

# Parse YAML
yaml_data = parse_yaml(fetch_url(url))

# Extract topology
topology_type = yaml_data['site']['topology']  # "bfc-32_2_0"
bricks = yaml_data['bricks']
neighbors = yaml_data['neighbors']

# Categorize neighbors automatically
for neighbor_name, neighbor_data in neighbors.items():
    category = categorize_neighbor(neighbor_name, neighbor_data)
    # BFC, Edge, Service, Core, Console, Tarmac
```

---

## Implementation Checklist

### Must Have
- [ ] Generic URL construction (works for any site)
- [ ] YAML parsing (handle any brick count)
- [ ] Neighbor categorization (BFC, Edge, Service, etc.)
- [ ] Automatic grouping (by type, not hardcoded)
- [ ] Color coding by category
- [ ] Connection highlighting (Inter-AZ, Intra-AZ)
- [ ] Plain XML output (editable in draw.io)

### Nice to Have
- [ ] Multiple detail levels (--detail high|medium|low)
- [ ] Custom grouping rules (--group-services)
- [ ] Export to multiple formats
- [ ] Validation mode

---

## Next Steps

1. **Finalize visualization approach** (brick-centric vs simplified)
2. **Define grouping rules** (how to handle 40+ service routers)
3. **Implement generic parser** (works for any YAML structure)
4. **Create color scheme** (by neighbor category)
5. **Build layout engine** (automatic positioning)
6. **Test with multiple sites** (BJS, IAD, NRT)

---

## Questions for User

1. **Detail Level**: Should we show all bricks individually or group them?
2. **Service Routers**: Show all 40+ individually or group by type (PUB/VPC/AP)?
3. **Layout**: Horizontal (bricks in rows) or vertical (tiers in layers)?
4. **Connections**: Which types are most important to highlight?
5. **Brick Devices**: Show T1 devices (r13-r28) individually or as "Brick X"?

---

**Status**: Planning Phase
**Next**: Gather requirements and finalize design