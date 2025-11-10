# UMN EC2 Fabric Topology Generator Agent

## Overview

Automated agent for generating **UMN (Unified Management Network) EC2 fabric** topology diagrams from SwitchBuilder brick definition files. This agent processes management core (es-mgmt-cor) devices and their interconnections across AWS sites.

---

## 🎯 Purpose

Generate comprehensive topology diagrams showing:
- ✅ Management core devices (es-mgmt-cor)
- ✅ Inter-AZ connections (cross availability zone)
- ✅ Intra-AZ connections (within availability zone)
- ✅ ES-C1 fabric connections
- ✅ Device grouping (r1 + r2 → r[12])
- ✅ Color-coded by device type and location

---

## 📋 Requirements

### Input
**Parent AZ**: bjs11
**Root DC**: bjs11-11
**Source File**: SwitchBuilder brick definition
- URL: `https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-BJS/blobs/mainline/--/configuration/etc/brick/EC2-BJS/bjs-es-mgmt-cor.brick`
- Format: JSON with DEVICE_DETAILS and NODES_AND_INTERFACES sections

### Key Sections
1. **DEVICE_DETAILS**: Device metadata (type, layer)
2. **NODES_AND_INTERFACES**: Complete connectivity information

---

## 🏗️ Architecture

### Device Types Discovered
- **Almach devices** (24): Management core routers (es-mgmt-cor-r1/r2)
- **Juniper devices** (1): Management core virtual router (es-mgmt-cor-v1)

### Connection Types
1. **Inter-AZ** (jrp21, jrp23): Cross availability zone links
2. **Intra-AZ** (jrp32): Within same AZ connections
3. **ES-C1** (bond73, bond77, jrp19, jrp20): EC2 fabric connections
4. **Local** (jrp1, jrp2, jrp3): Local fabric management connections

### Sites Covered
- **AZs**: bjs11, bjs12, bjs20, bjs80, pkx140
- **DCs**: 11, 12, 20, 50, 51, 52, 70, 73, 74, 80, 140, 141

---

## 🎨 Visual Design

### Color Scheme
| Device Type | Color | Hex Code | Description |
|------------|-------|----------|-------------|
| ROOT DC | Orange | #FFE6CC | bjs11-11 management core |
| Inter-AZ | Light Blue | #DAE8FC | Cross-AZ management cores |
| Intra-AZ | Light Green | #D5E8D4 | Same-AZ management cores |
| ES-C1 | Light Red | #F8CECC | EC2 fabric devices |
| ES-E1 | Light Purple | #E1D5E7 | OneFabric devices |
| ES-X1 | Light Yellow | #FFF4E6 | Extended fabric |
| Juniper | Gray | #D0D0D0 | Juniper virtual routers |

### Device Grouping
- **Pattern**: `{base-name}-r[12]` for paired devices
- **Example**: `bjs11-11-es-mgmt-cor-r1` + `bjs11-11-es-mgmt-cor-r2` → `bjs11-11-es-mgmt-cor-r[12]`
- **Label Format**: `<b>device-name</b><br/><i>fabric-type (device-type)</i>`

### Connection Display
- ✅ No link labels (clean visualization)
- ✅ Uniform connection color
- ✅ Deduplicated bidirectional links
- ✅ Visible connections between all devices

---

## 📁 Project Structure

```
/Users/anishkt/anish_topo_Agent_Project/umn_ec2_fabric_draw_Agent/
├── umn_ec2_topology_generator.py    # Main agent script
├── README.md                         # This file
└── REQUIREMENTS.md                   # Detailed requirements

/Users/anishkt/bjs11-11-umn-ec2-topology/
├── brick-configs/
│   ├── bjs-es-mgmt-cor.json         # Device details
│   ├── nodes_and_interfaces.json    # Connectivity data
│   └── parse_mcp_response.py        # Data extraction tool
├── analysis/
│   ├── connectivity_summary.json    # Connection statistics
│   └── extract_connections.py       # Connection extraction
└── bjs11-11-umn-ec2-topology.drawio # Generated topology
```

---

## 🚀 Usage

### Step 1: Fetch Brick Data
```bash
# Use MCP tool to fetch brick definition
use_mcp_tool(
  server_name="amzn-mcp",
  tool_name="read_internal_website",
  url="https://code.amazon.com/packages/SwitchBuilderBrickDef-EC2-BJS/blobs/mainline/--/configuration/etc/brick/EC2-BJS/bjs-es-mgmt-cor.brick"
)
```

### Step 2: Run Generator
```bash
cd /Users/anishkt/anish_topo_Agent_Project/umn_ec2_fabric_draw_Agent
python3 umn_ec2_topology_generator.py \
  /Users/anishkt/bjs11-11-umn-ec2-topology/brick-configs/bjs-es-mgmt-cor.json \
  /Users/anishkt/bjs11-11-umn-ec2-topology
```

### Step 3: Open in draw.io
The generated `.drawio` file is fully editable in draw.io desktop or web.

---

## 🔧 Implementation Steps

1. ✅ **Context Management**: Store request for session recovery
2. ✅ **Project Setup**: Create output folder structure
3. ✅ **Fetch Brick Data**: Use MCP tool to get brick definition
4. ⏳ **Parse Device Details**: Extract device metadata
5. ⏳ **Parse Connectivity**: Extract NODES_AND_INTERFACES
6. ⏳ **Build Connection Matrix**: Map all device connections
7. ⏳ **Categorize Connections**: Identify inter-AZ, intra-AZ, es-c1
8. ⏳ **Remove Duplicates**: Deduplicate bidirectional connections
9. ⏳ **Group Devices**: Combine r1/r2 pairs
10. ⏳ **Generate XML**: Create draw.io topology
11. ⏳ **Validate**: Ensure clean XML with proper mxGeometry

---

## 📊 Expected Output

### Devices (Grouped)
```
ROOT DC:
- bjs11-11-es-mgmt-cor-r[12] (Orange)
- bjs11-11-es-mgmt-cor-v1 (Gray)

Inter-AZ Management Cores:
- bjs12-12-es-mgmt-cor-r[12] (Light Blue)
- bjs20-20-es-mgmt-cor-r[12] (Light Blue)
- bjs80-80-es-mgmt-cor-r[12] (Light Blue)
- pkx140-140-es-mgmt-cor-r[12] (Light Blue)
- pkx140-141-es-mgmt-cor-r[12] (Light Blue)

Intra-AZ Management Cores:
- bjs11-50-es-mgmt-cor-r[12] (Light Green)
- bjs11-51-es-mgmt-cor-r[12] (Light Green)
- bjs11-52-es-mgmt-cor-r[12] (Light Green)
- bjs20-70-es-mgmt-cor-r[12] (Light Green)
- bjs20-73-es-mgmt-cor-r[12] (Light Green)
- bjs20-74-es-mgmt-cor-r[12] (Light Green)
```

### Connection Types
- **Inter-AZ**: Cross availability zone (jrp21, jrp23 interfaces)
- **Intra-AZ**: Within AZ, cross DC (jrp32 interfaces)
- **ES-C1**: To EC2 fabric devices (bond73, bond77, jrp19, jrp20)
- **Local**: Within same DC (jrp1, jrp2, jrp3 interfaces)

---

## 🔍 Key Differences from Regular EC2 Agent

### Data Source
- **EC2 Agent**: FabricBuilderSiteConfigs YAML files
- **UMN Agent**: SwitchBuilderBrickDef brick files

### Device Focus
- **EC2 Agent**: BFC and OneFabric devices
- **UMN Agent**: Management core (es-mgmt-cor) devices

### Grouping Strategy
- **EC2 Agent**: Normalizes brick suffixes (b3, b4 → base name)
- **UMN Agent**: Groups device pairs (r1 + r2 → r[12])

### Connection Analysis
- **EC2 Agent**: Discovers neighbors recursively from YAML
- **UMN Agent**: Extracts all connections from single brick file

---

## 🆘 Troubleshooting

### Issue: "NODES_AND_INTERFACES not found"
**Solution**: Ensure the complete brick file includes connectivity data

### Issue: "No connections generated"
**Solution**: Verify NODES_AND_INTERFACES section is properly parsed

### Issue: "Device grouping incorrect"
**Solution**: Check device naming pattern matches r1/r2 or v1/v2 format

### Issue: "XML errors in draw.io"
**Solution**: Validate mxGeometry elements have `as="geometry"` attribute

---

## 📞 Support

For questions or issues:
1. Check [`REQUIREMENTS.md`](REQUIREMENTS.md:1) for detailed implementation
2. Review brick data in `brick-configs/` directory
3. Check analysis output in `analysis/` directory
4. Verify agent console output for specific errors

---

**Version**: 1.0 (In Development)
**Status**: 🚧 Initial Setup Complete
**Last Updated**: 2024-11-04
**Location**: `/Users/anishkt/anish_topo_Agent_Project/umn_ec2_fabric_draw_Agent/`