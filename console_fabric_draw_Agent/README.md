# Console Topology Generator Agent

## Overview

Automated agent for generating AWS Console Fabric (es-mgmt-cor) topology diagrams.

---

## 🚀 Quick Start

### Usage

```bash
cd /Users/anishkt/anish_topo_Agent_Project
python3 topology_generator_agent.py --site <SITE> --fabric es-mgmt-cor
```

### Examples

```bash
# Beijing AZ 11, DC 11
python3 topology_generator_agent.py --site bjs11-11 --fabric es-mgmt-cor

# Beijing AZ 12, DC 12
python3 topology_generator_agent.py --site bjs12-12 --fabric es-mgmt-cor

# Beijing AZ 20, DC 73
python3 topology_generator_agent.py --site bjs20-73 --fabric es-mgmt-cor

# Tokyo AZ 12, DC 12
python3 topology_generator_agent.py --site nrt12-12 --fabric es-mgmt-cor
```

---

## 📁 Project Structure

```
anish_topo_Agent_Project/
├── topology_generator_agent.py    # Main agent
├── AGENT_REQUIREMENTS.md          # Technical requirements
└── README.md                       # This file
```

**Output folders** (created in home directory):
```
/Users/anishkt/{site}-{fabric}-topology/
  ├── brick-data.json
  ├── {site}-{fabric}-topology.drawio
  └── analysis files
```

---

## ✨ Features

### Topology Generation
✅ Root-based discovery (centered on target DC)
✅ 2-layer es-mgmt-cor neighbor discovery
✅ ALL r1/r2 pairs grouped
✅ Inter-DC BFC (ES-C1) grouped by DC
✅ All solid lines (no dashes)
✅ BFC connections highlighted (blue, thick)
✅ Beautified design (shadows, HTML labels, enhanced spacing)
✅ Plain XML, fully editable in draw.io

### Generic Design
✅ Works for ANY AWS location (BJS, NRT, IAD, PDX, etc.)
✅ Works for ANY AZ and DC combination
✅ Automatic brick URL construction
✅ Proper device categorization and grouping
✅ Clean output management (outside agent folder)

---

## 📊 What It Does

### Input
- **Site**: {location}{az}-{dc} (e.g., bjs11-11, nrt12-12)
- **Fabric**: es-mgmt-cor (console fabric)

### Process
1. Constructs brick file URL for the location
2. Reads brick data (NODES_AND_INTERFACES)
3. Discovers root device and neighbors
4. Groups devices by type and DC
5. Generates beautified draw.io topology

### Output
- **Topology file**: {site}-{fabric}-topology.drawio
- **Location**: /Users/anishkt/{site}-{fabric}-topology/
- **Format**: Plain XML, fully editable

---

## 🎯 Key Concepts

### Console Fabric
The management network layer (es-mgmt-cor) providing console access across AWS data centers.

### BFC (ES-C1)
Bare metal FinalCat devices (NOT compute).

### Root Device
The es-mgmt-cor device for the target DC - starting point for topology discovery.

### Location Format
**Pattern**: {LOCATION}{AZ}-{DC}
- BJS11-11 = Beijing, AZ 11, DC 11
- BJS20-73 = Beijing, AZ 20, DC 73
- NRT12-12 = Tokyo, AZ 12, DC 12

### Brick File Pattern
**Single file per location** (region-specific, not site-specific):
- BJS (all BJS sites): `SwitchBuilderBrickDef-EC2-BJS` → `bjs-es-mgmt-cor.brick`
- NRT (all NRT sites): `SwitchBuilderBrickDef-EC2-NRT` → `nrt-es-mgmt-cor.brick`
- IAD (all IAD sites): `SwitchBuilderBrickDef-EC2-IAD` → `iad-es-mgmt-cor.brick`

**Note**: One brick file covers ALL DCs in that location (e.g., bjs-es-mgmt-cor.brick contains bjs11-11, bjs12-12, bjs20-73, etc.)

---

## 🔧 Grouping Rules

### Intra-DC Devices (Target DC)
- **Aggressive grouping** to simplify topology
- All BFC (ES-C1) devices → Single `{site}-es-c1` node
- All Edge Management → Single `{site}-es-[e1,e2]-mgmt` node
- r1/r2 pairs → `device-r[1,2]` notation

### Inter-DC Devices (Other DCs)
- **Group r1/r2 pairs** within each DC
- **Keep DCs separate** (don't group across DCs)
- Group BFC by DC: `{site}-es-c1`

---

## 🎨 Visual Design

### Device Colors

| Device Type | Color | Hex |
|------------|-------|-----|
| Management Core (all es-mgmt-cor) | Orange | #FFE6CC |
| Virtual Management (es-mgmt-cor-v) | Orange | #FFE6CC |
| Edge Services Core | Green | #D5E8D4 |
| BFC (ES-C1) | Blue | #DAE8FC |
| Edge Management | Yellow | #FFF2CC |
| X1 Management | Red | #F8CECC |
| Transit Access | Pink | #E6D0DE |
| Inter-DC | Gray | #E8E8E8 |

**Note**: All es-mgmt-cor devices (including virtual) use the same orange color for consistency.

### Connection Styles

| Type | Color | Width | Style |
|------|-------|-------|-------|
| Intra-DC | Black (#333) | 2.5px | Solid |
| BFC (ES-C1) | Blue (#0066CC) | 4px | Solid |
| Inter-DC | Gray (#999) | 2.5px | Solid |

**All connections are solid lines** (no dashes)

---

## 📋 Output Management

### Clean Separation

**Agent Folder** (stays clean):
```
/Users/anishkt/anish_topo_Agent_Project/
├── topology_generator_agent.py
├── AGENT_REQUIREMENTS.md
└── README.md
```

**Output Folders** (created on demand, can be deleted):
```
/Users/anishkt/bjs11-11-es-mgmt-cor-topology/
/Users/anishkt/bjs12-12-es-mgmt-cor-topology/
/Users/anishkt/bjs20-73-es-mgmt-cor-topology/
```

### Cleanup

```bash
# Delete output folder when done
rm -rf /Users/anishkt/bjs11-11-es-mgmt-cor-topology/

# Agent folder remains intact
```

---

## 🤖 Using with Q CLI

### Simple Request

```
"Use the topology generator agent in anish_topo_Agent_Project to generate console topology for BJS11-11"
```

### With Brick Data Fetching

```
"Run topology_generator_agent.py for BJS11-11 and fetch the brick data from code.amazon.com"
```

### Batch Generation

```
"Use my topology agent to generate console topologies for BJS11-11, BJS12-12, and BJS20-73"
```

---

## 📚 Technical Details

See `AGENT_REQUIREMENTS.md` for:
- Complete requirements and best practices
- Grouping strategies
- Connection logic
- Visual design specifications
- Implementation checklist

---

## ✅ Requirements

### System
- Python 3.x
- Access to code.amazon.com
- Midway authentication

### For Q CLI
- MCP tool access (amzn-mcp)
- File system access
- Command execution capability

---

## 🎓 Examples

### Example 1: BJS11-11

**Input**:
```bash
python3 topology_generator_agent.py --site bjs11-11 --fabric es-mgmt-cor
```

**Output**:
- Folder: `/Users/anishkt/bjs11-11-es-mgmt-cor-topology/`
- File: `bjs11-11-es-mgmt-cor-topology.drawio`
- Nodes: ~7 grouped BJS11-11 devices + ~9 inter-DC groups
- Connections: All verified, solid lines, BFC highlighted

### Example 2: BJS12-12

**Input**:
```bash
python3 topology_generator_agent.py --site bjs12-12 --fabric es-mgmt-cor
```

**Output**:
- Folder: `/Users/anishkt/bjs12-12-es-mgmt-cor-topology/`
- File: `bjs12-12-es-mgmt-cor-topology.drawio`
- Nodes: ~4 grouped BJS12-12 devices + ~6 inter-DC groups
- Connections: All verified, solid lines, BFC highlighted

---

## 🆘 Troubleshooting

### Issue: "Brick data not found"
**Solution**: The agent will show the brick URL. Fetch it manually or ask Q to fetch it via MCP.

### Issue: "No devices found"
**Solution**: Check that the site name matches the brick file format (e.g., bjs11-11, not BJS11-11).

### Issue: "Output folder exists"
**Solution**: Delete the old output folder or the agent will use existing data.

---

## 📞 Support

For questions or issues:
1. Check `AGENT_REQUIREMENTS.md` for technical details
2. Review example outputs
3. Verify brick data is available

---

**Version**: 2.0
**Status**: Production Ready
**Last Updated**: 2025-10-01
**Location**: `/Users/anishkt/anish_topo_Agent_Project/`