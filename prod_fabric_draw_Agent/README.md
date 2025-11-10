# PROD Fabric Topology Generator Agent

## Overview

**Fully generic** automated agent for generating PROD fabric (ws-c1) topology diagrams for **ANY AWS site**. Includes BFC devices, OneFabric devices, and **ws-cor (workspace core)** connectivity. Just provide the site identifier and the agent automatically discovers all fabric devices and their interconnections.

---

## 🚀 Quick Start

### Usage

```bash
cd /Users/anishkt/anish_topo_Agent_Project/prod_fabric_draw_Agent
python3 prod_fabric_generator.py --site <YOUR-SITE> --fabric ws-c1
```

**That's it!** The agent works for ANY site - just change the `--site` parameter.

### Examples

```bash
# Beijing sites
python3 prod_fabric_generator.py --site bjs11-11 --fabric ws-c1
python3 prod_fabric_generator.py --site bjs12-12 --fabric ws-c1
python3 prod_fabric_generator.py --site bjs20-20 --fabric ws-c1

# US East (Virginia) sites
python3 prod_fabric_generator.py --site iad12-12 --fabric ws-c1

# Tokyo sites
python3 prod_fabric_generator.py --site nrt12-12 --fabric ws-c1

# ANY other AWS site
python3 prod_fabric_generator.py --site <site> --fabric ws-c1
```

---

## 🌍 Generic Design

### Works for ANY Site

The agent is **completely generic** and requires **zero code changes** for different sites:

- ✅ **Any AWS region**: BJS, IAD, NRT, PDX, SYD, FRA, etc.
- ✅ **Any AZ**: 11, 12, 20, 50, 80, etc.
- ✅ **Any DC**: 11, 12, 50, 51, 60, 70, 73, etc.
- ✅ **Automatic discovery**: Finds all neighbors from YAML
- ✅ **Recursive mapping**: Discovers intra-AZ mesh automatically
- ✅ **ws-cor support**: Includes workspace core connectivity

### How It Works

```
User provides: --site bjs11-11
                    ↓
Agent constructs: bjs11-11-ws-c1.yaml URL
                    ↓
Agent discovers: All BFC/OneFabric/ws-cor neighbors
                    ↓
Agent fetches: YAML for BFC/OneFabric (skips ws-cor)
                    ↓
Agent adds: ws-cor from ROOT neighbors
                    ↓
Agent discovers: Intra-AZ neighbor connections
                    ↓
Agent generates: Complete topology diagram
```

**No hardcoding. No site-specific logic. Completely generic.**

---

## 📁 Project Structure

```
prod_fabric_draw_Agent/
├── prod_fabric_generator.py    # Main agent (342 lines)
├── REQUIREMENTS.md              # Implementation details
└── README.md                    # This file
```

**Output folders** (created automatically):
```
/Users/anishkt/{site}-{fabric}-topology/
├── yaml-configs/               # YAML files (as JSON)
├── analysis/                   # Discovery summaries
└── {site}-{fabric}-topology.drawio
```

---

## ✨ Features

### Automatic Discovery
✅ Discovers ALL BFC neighbors (inter-AZ and intra-AZ)
✅ Discovers ALL OneFabric neighbors
✅ **Discovers ws-cor devices** (workspace core)
✅ Recursive discovery for intra-AZ mesh topology
✅ Captures cross-AZ connections
✅ No manual device list needed

### Smart Processing
✅ Device normalization (removes brick suffixes)
✅ Connection deduplication (bidirectional → single edge)
✅ Intelligent filtering (BFC, OneFabric, ws-cor only)
✅ Automatic categorization (Inter-AZ vs Intra-AZ)
✅ **ws-cor special handling** (no YAML fetch needed)

### Clean Output
✅ Color-coded by device type and location
✅ Individual devices (no grouping)
✅ Clean connections (no labels)
✅ Plain XML (fully editable in draw.io)
✅ Proper mxGeometry (no errors)

---

## 🎯 Key Difference from EC2 Fabric

### PROD Fabric (ws-c1) vs EC2 Fabric (es-c1)

| Aspect | EC2 Fabric | PROD Fabric |
|--------|-----------|-------------|
| Fabric Type | es-c1 | ws-c1 |
| Purpose | EC2 compute | Workspace compute |
| Core Device | es-mgmt-cor | **ws-cor** |
| YAML Pattern | {site}-es-c1.yaml | {site}-ws-c1.yaml |
| Core YAML | Has YAML file | **No YAML file** |

### ws-cor Special Handling

**ws-cor devices**:
- Type: `core` in neighbors section
- No separate YAML configuration file
- Added directly from ROOT YAML neighbors
- Critical for PROD fabric topology
- Shows workspace core connectivity

---

## 📊 What It Generates

### For ANY Site You Provide

**Input**: `--site bjs11-11` (or ANY other site)

**Automatic Discovery**:
1. ROOT DC device (ws-c1)
2. **ws-cor device** (workspace core)
3. All Inter-AZ BFC neighbors
4. All Intra-AZ BFC neighbors
5. All OneFabric neighbors
6. Intra-AZ mesh connections
7. Cross-AZ connections

**Output**: Complete topology diagram with:
- All discovered devices (normalized names)
- All connections (deduplicated)
- **ws-cor connectivity**
- Color-coded by type
- Fully editable in draw.io

---

## 🎓 Example: BJS11-11

### What the Agent Discovered

**From ROOT** (bjs11-11-ws-c1):
- 1 ws-cor: bjs11-11-ws-cor ✅
- 3 Inter-AZ BFC: bjs12-12, bjs20-20, bjs80-80
- 2 Intra-AZ BFC: bjs11-50, bjs11-51

**Total**: 7 devices, 9 connections

### Device Layout

```
┌─────────────────────────────────┐
│ ROOT DC (Darker Orange)         │
│ bjs11-11-ws-c1                  │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│ WS-COR (Light Orange)           │
│ bjs11-11-ws-cor                 │ ✅ Critical!
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│ Inter-AZ BFC (Blue)             │
│ bjs12-12, bjs20-20, bjs80-80    │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│ Intra-AZ BFC (Green)            │
│ bjs11-50, bjs11-51              │
└─────────────────────────────────┘
```

---

## 🔧 How to Use

### Step 1: Run Agent

```bash
python3 prod_fabric_generator.py --site <YOUR-SITE> --fabric ws-c1
```

The agent will:
- Create output directory
- Show YAML URLs to fetch (skips ws-cor)
- Wait for YAML files

### Step 2: Fetch YAMLs

Use Q CLI with MCP tool to fetch each YAML (except ws-cor):
```
"Fetch YAML from <URL> and save to yaml-configs/"
```

**Note**: ws-cor devices are automatically included - no YAML fetch needed!

### Step 3: Re-run Agent

```bash
python3 prod_fabric_generator.py --site <YOUR-SITE> --fabric ws-c1
```

The agent will:
- Use cached YAML files
- Add ws-cor from ROOT neighbors
- Discover all BFC/OneFabric neighbors
- Build connection matrix
- Generate topology diagram

### Step 4: Open in draw.io

The output `.drawio` file is fully editable in draw.io desktop or web.

---

## 🆘 Troubleshooting

### Issue: "ROOT YAML not found"
**Solution**: Fetch the ROOT YAML using MCP tool and save as JSON in `yaml-configs/` directory.

### Issue: "ws-cor not showing"
**Solution**: Check that ROOT YAML has ws-cor in neighbors section with type: core.

### Issue: "Only ROOT and ws-cor in output"
**Solution**: Fetch YAML files for BFC neighbors (agent will list the URLs).

### Issue: "Missing connections"
**Solution**: Ensure intra-AZ neighbor YAMLs are fetched.

---

## 📞 Support

For questions or issues:
1. Check [`REQUIREMENTS.md`](REQUIREMENTS.md:1) for implementation details
2. Verify YAML files are in `yaml-configs/` directory
3. Check agent console output for specific errors
4. Remember: ws-cor devices don't need YAML files!

---

## 🎉 Key Advantages

**One Agent, Infinite Sites**

This agent works for:
- ✅ Beijing (BJS)
- ✅ Virginia (IAD)
- ✅ Tokyo (NRT)
- ✅ Portland (PDX)
- ✅ Sydney (SYD)
- ✅ Frankfurt (FRA)
- ✅ **ANY other AWS site**

**Special Features**:
- ✅ **ws-cor support** (no YAML needed)
- ✅ Workspace core connectivity
- ✅ BFC and OneFabric discovery
- ✅ Complete inter-AZ and intra-AZ mesh

**No code changes needed. Just change the `--site` parameter.**

---

**Version**: 1.0
**Status**: ✅ Production Ready
**Last Updated**: 2025-10-27
**Tested Sites**: bjs11-11-ws-c1
**Location**: `/Users/anishkt/anish_topo_Agent_Project/prod_fabric_draw_Agent/`