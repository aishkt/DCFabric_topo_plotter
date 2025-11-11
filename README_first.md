# AWS Network Topology Generator Agents

## 🎯 Overview

Collection of 7 specialized agents for generating AWS network topology diagrams from various data sources. Each agent is self-contained with complete documentation and can work independently.

---

## 📁 Project Structure

```
anish_topo_Agent_Project/
├── README.md                          # This file - main project overview
├── QUICK_START_GUIDE.md              # Master guide for all agents
├── umn_ec2_fabric_draw_Agent/        # UMN EC2 fabric topologies
├── umn_prod_fabric_draw_Agent/       # UMN PROD fabric topologies
├── dsn_fabric_draw_agent/            # DSN fabric topologies
├── console_fabric_draw_Agent/        # Console fabric topologies
├── ec2_fabric_draw_Agent/            # EC2 fabric topologies (FabricBuilder)
├── prod_fabric_draw_Agent/           # PROD fabric topologies (FabricBuilder)
└── corp_nap_fabric_draw_agent/       # Corp NAP fabric topologies
```

---

## ⚠️ Important: EC2 vs UMN EC2 Disambiguation

**When user says "EC2 fabric" or just "EC2", clarify which they mean:**

### UMN EC2 (Management Core)
- **Keywords**: "UMN EC2", "UMN EC2 fabric"
- **Data Source**: SwitchBuilderBrickDef-EC2
- **Devices**: Management core routers (es-mgmt-cor-r1, es-mgmt-cor-r2)
- **Use Case**: Console/management network topology
- **Agent**: `umn_ec2_fabric_draw_Agent/`

### EC2 Fabric (BFC/OneFabric)
- **Keywords**: "EC2 fabric", "EC2 BFC", "FabricBuilder EC2"
- **Data Source**: FabricBuilderSiteConfigs
- **Devices**: BFC fabric (es-c1) and OneFabric (es-e1)
- **Use Case**: Compute fabric topology
- **Agent**: `ec2_fabric_draw_Agent/`

**Quick Decision:**
- User mentions "UMN" → Use UMN EC2 agent
- User mentions "BFC" or "OneFabric" → Use EC2 fabric agent
- User says just "EC2" → **Ask them to clarify!**

---

## 🤖 For AI Agents (Roo/Claude)

### How to Find Agent Requirements

When a user requests a topology, follow this discovery process:

**Step 1: Identify Topology Type from User Prompt**

Match keywords in user request:

**IMPORTANT: "EC2" is ambiguous - clarify which type:**

- "UMN EC2" or "UMN EC2 fabric" → `umn_ec2_fabric_draw_Agent/`
  - Uses: SwitchBuilder brick files
  - Shows: Management core devices (es-mgmt-cor)
  
- "EC2 fabric" or "EC2 BFC" or "FabricBuilder EC2" → `ec2_fabric_draw_Agent/`
  - Uses: FabricBuilder YAML files
  - Shows: BFC and OneFabric devices (es-c1, es-e1)

**Other topologies:**
- "UMN PROD" or "PROD fabric" → `umn_prod_fabric_draw_Agent/`
- "DSN" → `dsn_fabric_draw_agent/`
- "Console" → `console_fabric_draw_Agent/`
- "PROD site" or "FabricBuilder PROD" → `prod_fabric_draw_Agent/`
- "Corp NAP" or "NAP fabric" → `corp_nap_fabric_draw_agent/`

**Step 2: Navigate to Agent Directory**

```
/Users/anishkt/anish_topo_Agent_Project/{agent_directory}/
```

**Step 3: Read REQUIREMENTS.md**

Each agent directory contains:
- `REQUIREMENTS.md` - Complete implementation guide with Quick Start
- `README.md` - Usage documentation and examples
- Generator scripts (`.py` files)

**Step 4: Follow Quick Start Section**

Every REQUIREMENTS.md has a "🚀 Quick Start" section with:
- URL generation formula
- Data fetching instructions
- Parsing rules
- Complete workflow

### Example Discovery Flow

**User says**: "Create UMN EC2 topology for bjs11-11"

**Agent should**:
1. Identify: "UMN EC2" → `umn_ec2_fabric_draw_Agent/`
2. Read: `/Users/anishkt/anish_topo_Agent_Project/umn_ec2_fabric_draw_Agent/REQUIREMENTS.md`
3. Follow: Quick Start section in REQUIREMENTS.md
4. Generate: Topology using the documented workflow

---

## 📝 Recommended User Prompts

### Clear and Specific Prompts

**Format**: `Create {TOPOLOGY_TYPE} topology for {SITE}`

**Examples**:
- ✅ "Create UMN EC2 topology for bjs11-11"
- ✅ "Generate PROD fabric topology for nrt55-62"
- ✅ "Create DSN topology for iad12-12"
- ✅ "Generate Console topology for BJS11"
- ✅ "Create Corp NAP topology for bjs11-11"

### Topology Type Keywords (CLARIFIED)

| Topology | Keywords | Data Source | Devices Shown |
|----------|----------|-------------|---------------|
| **UMN EC2** | "UMN EC2", "UMN EC2 fabric" | SwitchBuilder brick | Management core (es-mgmt-cor) |
| **EC2 BFC** | "EC2 fabric", "EC2 BFC", "FabricBuilder EC2" | FabricBuilder YAML | BFC + OneFabric (es-c1, es-e1) |
| UMN PROD | "UMN PROD", "PROD fabric" | SwitchBuilder brick | PROD management core |
| PROD BFC | "PROD site", "FabricBuilder PROD" | FabricBuilder YAML | PROD BFC devices |
| DSN | "DSN" | GenevaBuilder | DSN fabric |
| Console | "Console" | ConsoleSiteDef | Console fabric |
| Corp NAP | "Corp NAP", "NAP fabric" | GenevaBuilder | NAP fabric |

**⚠️ Key Distinction:**
- **"UMN EC2"** = Management core topology (SwitchBuilder)
- **"EC2 fabric"** or **"EC2 BFC"** = BFC/OneFabric topology (FabricBuilder)

---

## 🔍 Agent Discovery Algorithm

```python
def find_agent_requirements(user_prompt: str) -> str:
    """
    Determine which agent to use based on user prompt
    Returns path to REQUIREMENTS.md
    """
    prompt_lower = user_prompt.lower()
    base_path = "/Users/anishkt/anish_topo_Agent_Project"
    
    # Keyword matching with priority order to avoid confusion
    
    # Check for UMN first (more specific)
    if "umn ec2" in prompt_lower:
        return f"{base_path}/umn_ec2_fabric_draw_Agent/REQUIREMENTS.md"
    
    elif "umn prod" in prompt_lower:
        return f"{base_path}/umn_prod_fabric_draw_Agent/REQUIREMENTS.md"
    
    # Then check for FabricBuilder EC2/PROD
    elif "ec2 fabric" in prompt_lower or "ec2 bfc" in prompt_lower or "fabricbuilder ec2" in prompt_lower:
        return f"{base_path}/ec2_fabric_draw_Agent/REQUIREMENTS.md"
    
    elif "prod fabric" in prompt_lower or "fabricbuilder prod" in prompt_lower:
        return f"{base_path}/prod_fabric_draw_Agent/REQUIREMENTS.md"
    
    # Other topologies
    elif "dsn" in prompt_lower:
        return f"{base_path}/dsn_fabric_draw_agent/REQUIREMENTS.md"
    
    elif "console" in prompt_lower:
        return f"{base_path}/console_fabric_draw_Agent/REQUIREMENTS.md"
    
    elif "corp nap" in prompt_lower or "nap fabric" in prompt_lower:
        return f"{base_path}/corp_nap_fabric_draw_agent/REQUIREMENTS.md"
    
    # Ambiguous "EC2" or "PROD" alone
    elif "ec2" in prompt_lower and "umn" not in prompt_lower:
        # Ask user to clarify: UMN EC2 or EC2 BFC?
        return None
    
    elif "prod" in prompt_lower and "umn" not in prompt_lower:
        # Ask user to clarify: UMN PROD or PROD BFC?
        return None
    
    else:
        # Ambiguous - ask user to clarify
        return None
```

---

## 📚 Documentation Structure

Each agent directory contains:

```
{agent_directory}/
├── REQUIREMENTS.md          # ⭐ START HERE - Complete implementation guide
│   ├── Quick Start section
│   ├── URL generation formula
│   ├── Data fetching instructions
│   ├── Parsing rules
│   └── Complete workflow
├── README.md                # Usage documentation and examples
└── *.py                     # Generator scripts
```

---

## ⚠️ Critical Rules for AI Agents (Roo/Claude)

### 🚨 MOST IMPORTANT: Use Existing Scripts

**NEVER create new Python scripts!** Each agent directory already contains working generator scripts:

- `umn_ec2_fabric_draw_Agent/` → Use existing `.py` files
- `ec2_fabric_draw_Agent/` → Use `ec2_fabric_generator.py`
- `corp_nap_fabric_draw_agent/` → Use `nap_fabric_generator.py`
- `umn_prod_fabric_draw_Agent/` → Use existing `.py` files
- `prod_fabric_draw_Agent/` → Use `prod_fabric_generator.py`
- `dsn_fabric_draw_agent/` → Use existing `.py` files
- `console_fabric_draw_Agent/` → Use existing `.py` files

**Your job as AI agent:**
1. ✅ Identify correct agent directory
2. ✅ Read REQUIREMENTS.md for workflow
3. ✅ Fetch configuration files using MCP tools
4. ✅ Run existing Python scripts with fetched data
5. ❌ **NEVER write new generator scripts**

### Other Critical Rules

1. **Always fetch fresh data** - never use cached files
2. **Follow REQUIREMENTS.md** - each agent has specific rules
3. **Use MCP tools** - amzn-mcp or builder-mcp for fetching
4. **Use existing scripts** - they're already tested and working
5. **Save to specified location** - check agent's REQUIREMENTS.md

---

## 🚀 Quick Agent Selection Guide

**User mentions**:
- **"UMN EC2"** → UMN EC2 agent (management core)
- **"EC2 fabric"** or **"EC2 BFC"** → EC2 fabric agent (BFC/OneFabric)
- **"UMN PROD"** → UMN PROD agent (PROD management core)
- **"PROD fabric"** → PROD fabric agent (PROD BFC)
- "DSN" → DSN agent
- "Console" → Console agent
- "NAP" or "Corp NAP" → Corp NAP agent

**⚠️ If user just says "EC2" or "PROD":**
Ask them to clarify:
- "Do you want UMN EC2 (management core) or EC2 fabric (BFC/OneFabric)?"
- "Do you want UMN PROD (management core) or PROD fabric (BFC)?"

---

## 📊 Agent Capabilities

| Agent | Data Source | Devices Shown | Output Location |
|-------|-------------|---------------|-----------------|
| **UMN EC2** | SwitchBuilderBrickDef-EC2 | Management core (es-mgmt-cor) | `{site}-umn-ec2-topology/` |
| **EC2 Fabric** | FabricBuilderSiteConfigs | BFC + OneFabric (es-c1, es-e1) | `{site}-es-c1-topology/` |
| UMN PROD | SwitchBuilderBrickDef-PROD | PROD management core | `{site}-umn-prod-topology/` |
| PROD Fabric | FabricBuilderSiteConfigs | PROD BFC devices | `{site}-es-prod-topology/` |
| DSN | GenevaBuilderDCNE | DSN fabric | `{site}-dsn-topology/` |
| Console | ConsoleSiteDef | Console fabric | `{site}-console-topology/` |
| Corp NAP | GenevaBuilderDCNE | NAP fabric | `{site}-nap-topology/` |

**Note:** Output directories are created in user's home directory, not Desktop

---

## 🎓 For New AI Agents (Roo/Claude)

**First Time Using These Agents?**

1. ✅ Read this README.md (you're here!)
2. ✅ When user requests topology, identify type using keywords
3. ✅ Navigate to appropriate agent directory
4. ✅ Read REQUIREMENTS.md in that directory
5. ✅ Fetch configuration files using MCP tools
6. ✅ **Use existing Python scripts** in that directory
7. ✅ Run scripts with fetched data
8. ❌ **DO NOT create new scripts**

**Key Insights:**
- Each REQUIREMENTS.md is self-contained with complete workflow
- Each agent directory has working Python scripts
- Your role: orchestrate the workflow, don't rewrite the code
- The scripts are generic and work for any site

**Example Workflow:**
```
User: "Create EC2 fabric for nrt12-12"
  ↓
Roo: Identifies ec2_fabric_draw_Agent/
  ↓
Roo: Reads REQUIREMENTS.md
  ↓
Roo: Fetches nrt12-12-es-c1.yaml using MCP
  ↓
Roo: Saves to yaml-configs/ directory
  ↓
Roo: Runs existing ec2_fabric_generator.py script
  ↓
Roo: Returns topology file location to user
```

---

**Version**: 1.0
**Status**: ✅ All 7 Agents Operational
**Last Updated**: 2024-11-10
**Location**: `/Users/anishkt/anish_topo_Agent_Project/`