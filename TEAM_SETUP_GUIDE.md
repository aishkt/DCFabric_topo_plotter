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
"Go over readme file in /Users/anishkt/DCFabric_topo_plotter and understand the context"
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

### Example Prompts for Any Site

```
"Create EC2 fabric diagram for {YOUR_SITE}"
"Create UMN EC2 topology for {YOUR_SITE}"
"Generate PROD fabric topology for {YOUR_SITE}"
"Create DSN topology for {YOUR_SITE}"
"Generate Console topology for {YOUR_SITE}"
```

**Replace `{YOUR_SITE}` with any AWS site identifier:**
- nrt12-12, nrt55-55, nrt8-20 (Tokyo)
- iad12-12, iad50-50 (Virginia)
- bjs11-11, bjs20-20 (Beijing)
- pdx50-50 (Portland)
- syd6-6 (Sydney)
- etc.

### Manual Usage (Without Roo)

If you prefer to run agents manually:

1. **Navigate to agent directory**
   ```bash
   cd DCFabric_topo_plotter/ec2_fabric_draw_Agent
   ```

2. **Read REQUIREMENTS.md** for that agent

3. **Follow the Quick Start** section in REQUIREMENTS.md



## 🔄 Keeping Up to Date

### Pull Latest Changes

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

---

## 👥 Contributing Changes

If you improve an agent or fix a bug:

### Step 1: Make Your Changes
Edit files as needed

### Step 2: Commit
```bash
git add -A
git commit -m "Description of your changes"
```

### Step 3: Push
```bash
git push origin main
```

Or create a pull request if you prefer code review.

---

