# Team Setup Guide - AWS Network Topology Generator Agents

## 🎯 For Team Members

This guide explains how to set up and use the AWS Network Topology Generator Agents on your machine.

---
## 🚀 Quick Setup (5 Minutes)

### Step 1: Clone the Repository

```bash
# Clone to your preferred location
git clone https://github.com/aishkt/DCFabric_topo_plotter.git

# Navigate to the project
cd DCFabric_topo_plotter
```

## 📚 How to Use the Agents

### With Roo (AI Agent) - Recommended

**Step 1: Give Roo Context** (First time only)
```
"Go over readme file in /Users/<homefolder>/DCFabric_topo_plotter and understand the context"
```

**Step 2: Request Topology** (For any site)
```
"Create EC2 fabric diagram for nrt12-12"
"Create UMN EC2 topology for iad12-12"
"Generate DSN topology for bjs11-11"
```

**That's it!** Roo will:
- ✅ Automatically identify which agent to use
- ✅ Read the agent's REQUIREMENTS.md
- ✅ Fetch required YAML/config files using MCP tools
- ✅ Generate the topology diagram
- ✅ Save to the correct output location


### Always Pull Latest Changes before using agent

```bash
cd DCFabric_topo_plotter
git pull origin main
```

### Check for Updates

```bash
git fetch origin
git status
# Shows if your local is behind remote
```



