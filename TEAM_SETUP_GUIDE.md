# Team Setup Guide - AWS Network Topology Generator Agents

## 🎯 For Team Members

This guide explains how to set up and use the AWS Network Topology Generator Agents on your machine.

---
## 🚀 Quick Setup (5 Minutes)

### Option 1: Using Brazil Workspace (Recommended)

```bash
# Create a workspace
mkdir -p ~/workspace
cd ~/workspace

# Create Brazil workspace
brazil ws create -n my-topology-workspace

# Navigate to workspace
cd my-topology-workspace

# Use the version set
brazil ws use --vs DCLC_GenAITools/development

# Add the package to your workspace
brazil ws use --package Dclcagentpackage

# Navigate to the package
cd src/Dclcagentpackage

# Switch to the branch with all agents (until merged to mainline)
git checkout add-topology-agents

# Now you have all 7 agents and can use them!
```

### Option 2: Direct Git Clone (Alternative)

```bash
# Clone directly from code.amazon.com
git clone ssh://git.amazon.com/pkg/Dclcagentpackage

# Navigate to the project
cd Dclcagentpackage

# Checkout the branch with all agents
git checkout add-topology-agents

# Note: Once CR is merged, you can use 'mainline' branch instead:
# git checkout mainline
```

## 📚 How to Use the Agents

### With Roo (AI Agent) - Recommended

**Step 1: Give Roo Context** (First time only)
provide the below prompt :

```
"Go over readme file in ~/workspace/my-topology-workspace/src/Dclcagentpackage and understand the context"
```

**Step 2: Prompt to Request Topology** (For any site)
```
"Create EC2 fabric diagram for nrt12-12"
or
"Create UMN EC2 topology for iad12-12"
or
"Generate DSN topology for bjs11-11"
```

**That's it!** Roo will:
- ✅ Automatically identify which agent to use
- ✅ Read the agent's REQUIREMENTS.md
- ✅ Fetch required YAML/config files using MCP tools
- ✅ Generate the topology diagram
- ✅ Save to the correct output location


### Always Pull Latest Changes Before Using Agent

**If using Brazil workspace:**
```bash
cd ~/workspace/my-topology-workspace/src/Dclcagentpackage
git pull origin add-topology-agents
```

**If using direct git clone:**
```bash
cd Dclcagentpackage
git pull origin add-topology-agents
```

## 📦 Package Information

- **Package Name**: Dclcagentpackage
- **Code Repository**: https://code.amazon.com/packages/Dclcagentpackage
- **Version Set**: DCLC_GenAITools/development
- **Bindle**: amzn1.bindle.resource.oq4sp5h6cgvqfbo6txoa
- **Mailing List**: dclc-all@amazon.com

## 🔗 Quick Links

- **Package Page**: https://code.amazon.com/packages/Dclcagentpackage
- **Mainline Branch**: https://code.amazon.com/packages/Dclcagentpackage/trees/mainline
- **Code Reviews**: https://code.amazon.com/packages/Dclcagentpackage/reviews

## 📧 Support

For questions or issues, contact: anishkt@amazon.com or dclc-all@amazon.com



