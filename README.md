# AWS Network Topology Generator Agents

## 🎯 Overview

Collection of 7 specialized agents for generating AWS network topology diagrams from various data sources. Each agent is self-contained with complete documentation and can work independently.

## 🎭 Agent Role Definition

### Role: "File-Based Topology Info Extractor, Parser and Topology Generator"

**Core Pattern**: URL Generation → File Fetch → Parse → Extract → Generate Topology

**Applies to**: ALL 7 Agents (UMN EC2, EC2 Fabric, PROD Fabric, UMN PROD, Console, DSN, Corp NAP)

**Unified Workflow**:
1. **Generate URL** from site identifier using agent-specific URL pattern
2. **Fetch configuration file** via MCP tools (amzn-mcp or builder-mcp)  
3. **Parse file structure** based on format:
   - JSON for SwitchBuilder .brick files
   - YAML for FabricBuilder .yaml files
   - Key-Value for GenevaBuilder .attr files
4. **Extract device connections** and relationships from parsed data
5. **Run Python generator script** to create draw.io XML topology diagram

**Data Sources by Agent**:

| Agent | Package | File Type | Format | MCP Server |
|-------|---------|-----------|--------|------------|
| UMN EC2 | SwitchBuilderBrickDef-EC2 | .brick | JSON | amzn-mcp |
| UMN PROD | SwitchBuilderBrickDef-PROD | .brick | JSON | amzn-mcp |
| Console | SwitchBuilderBrickDef-EC2 | .brick | JSON | amzn-mcp |
| EC2 Fabric | FabricBuilderSiteConfigs | .yaml | YAML | amzn-mcp |
| PROD Fabric | FabricBuilderSiteConfigs | .yaml | YAML | amzn-mcp |
| DSN | GenevaBuilderDCNE | .attr | Key-Value | builder-mcp |
| Corp NAP | GenevaBuilderDCNE | .attr | Key-Value | builder-mcp |

**Key Principle**: All agents follow the same fundamental pattern - fetch a configuration file, parse it, and generate topology. The only differences are the specific URL patterns, file formats, and parsing logic for each data source.

---

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

## ⚠️ Important: Keyword Matching Rules for AI Agents

**Clear, unambiguous rules for agent selection:**

### Default Interpretations (When "UMN" NOT mentioned)

| User Says | Agent to Use | Reasoning |
|-----------|--------------|-----------|
| "EC2 fabric" | **EC2 Fabric** (BFC/OneFabric) | Default EC2 = BFC fabric |
| "EC2 diagram" | **EC2 Fabric** (BFC/OneFabric) | Default EC2 = BFC fabric |
| "PROD fabric" | **PROD Fabric** (BFC) | Default PROD = BFC fabric |
| "PROD diagram" | **PROD Fabric** (BFC) | Default PROD = BFC fabric |
| "Corp fabric" | **Corp NAP** | Corp = NAP fabric |
| "NAP fabric" | **Corp NAP** | NAP = Corp NAP fabric |

### Explicit UMN Requests (When "UMN" IS mentioned)

| User Says | Agent to Use | Reasoning |
|-----------|--------------|-----------|
| "UMN EC2" | **UMN EC2** (Management Core) | Explicit UMN request |
| "EC2 UMN" | **UMN EC2** (Management Core) | Explicit UMN request |
| "UMN PROD" | **UMN PROD** (Management Core) | Explicit UMN request |
| "PROD UMN" | **UMN PROD** (Management Core) | Explicit UMN request |

### Summary Rules

**Simple rule for AI agents:**
- ✅ "EC2" alone → EC2 Fabric (BFC/OneFabric)
- ✅ "PROD" alone → PROD Fabric (BFC)
- ✅ "Corp" or "NAP" → Corp NAP
- ✅ "UMN EC2" or "EC2 UMN" → UMN EC2 (Management Core)
- ✅ "UMN PROD" or "PROD UMN" → UMN PROD (Management Core)

**NO ambiguity. NO clarification needed. Just match keywords and select agent.**

---

## 🤖 For AI Agents (Roo/Claude)

### How to Find Agent Requirements

When a user requests a topology, follow this discovery process:

**Step 1: Identify Topology Type from User Prompt**

Match keywords in user request using these CLEAR rules:

**Default Mappings (when "UMN" NOT mentioned):**
- "EC2" → `ec2_fabric_draw_Agent/` (BFC/OneFabric)
- "PROD" → `prod_fabric_draw_Agent/` (BFC)
- "Corp" or "NAP" → `corp_nap_fabric_draw_agent/`
- "DSN" → `dsn_fabric_draw_agent/`
- "Console" → `console_fabric_draw_Agent/`

**Explicit UMN Mappings (when "UMN" IS mentioned):**
- "UMN EC2" or "EC2 UMN" → `umn_ec2_fabric_draw_Agent/` (Management Core)
- "UMN PROD" or "PROD UMN" → `umn_prod_fabric_draw_Agent/` (Management Core)

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

### Topology Type Keywords (UNAMBIGUOUS)

| User Input | Agent Selected | Data Source | Devices Shown |
|------------|----------------|-------------|---------------|
| "EC2" (alone) | **EC2 Fabric** | FabricBuilder YAML | BFC + OneFabric (es-c1, es-e1) |
| "EC2 fabric" | **EC2 Fabric** | FabricBuilder YAML | BFC + OneFabric (es-c1, es-e1) |
| "UMN EC2" | **UMN EC2** | SwitchBuilder brick | Management core (es-mgmt-cor) |
| "EC2 UMN" | **UMN EC2** | SwitchBuilder brick | Management core (es-mgmt-cor) |
| "PROD" (alone) | **PROD Fabric** | FabricBuilder YAML | PROD BFC devices |
| "PROD fabric" | **PROD Fabric** | FabricBuilder YAML | PROD BFC devices |
| "UMN PROD" | **UMN PROD** | SwitchBuilder brick | PROD management core |
| "PROD UMN" | **UMN PROD** | SwitchBuilder brick | PROD management core |
| "Corp" or "Corp fabric" | **Corp NAP** | GenevaBuilder | NAP fabric |
| "NAP" or "NAP fabric" | **Corp NAP** | GenevaBuilder | NAP fabric |
| "DSN" | **DSN** | GenevaBuilder | DSN fabric |
| "Console" | **Console** | ConsoleSiteDef | Console fabric |

**⚠️ Key Rule:**
- **Default (no "UMN")**: EC2 = BFC fabric, PROD = BFC fabric
- **Explicit "UMN"**: UMN EC2 = Management core, UMN PROD = Management core

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
    
    # UNAMBIGUOUS keyword matching - clear priority order
    
    # Check for UMN explicitly (management core)
    if "umn ec2" in prompt_lower or "ec2 umn" in prompt_lower:
        return f"{base_path}/umn_ec2_fabric_draw_Agent/REQUIREMENTS.md"
    
    elif "umn prod" in prompt_lower or "prod umn" in prompt_lower:
        return f"{base_path}/umn_prod_fabric_draw_Agent/REQUIREMENTS.md"
    
    # Default EC2/PROD (without "UMN") = BFC fabric
    elif "ec2" in prompt_lower:
        return f"{base_path}/ec2_fabric_draw_Agent/REQUIREMENTS.md"
    
    elif "prod" in prompt_lower:
        return f"{base_path}/prod_fabric_draw_Agent/REQUIREMENTS.md"
    
    # Corp NAP
    elif "corp" in prompt_lower or "nap" in prompt_lower:
        return f"{base_path}/corp_nap_fabric_draw_agent/REQUIREMENTS.md"
    
    # Other topologies
    elif "dsn" in prompt_lower:
        return f"{base_path}/dsn_fabric_draw_agent/REQUIREMENTS.md"
    
    elif "console" in prompt_lower:
        return f"{base_path}/console_fabric_draw_Agent/REQUIREMENTS.md"
    
    else:
        # Unknown topology type
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

## 🚀 Quick Agent Selection Guide (UNAMBIGUOUS)

**Simple matching rules - NO clarification needed:**

| User Input | Agent Selected | Type |
|------------|----------------|------|
| "EC2" | EC2 Fabric | BFC/OneFabric |
| "EC2 fabric" | EC2 Fabric | BFC/OneFabric |
| "EC2 diagram" | EC2 Fabric | BFC/OneFabric |
| "UMN EC2" or "EC2 UMN" | UMN EC2 | Management Core |
| "PROD" | PROD Fabric | BFC |
| "PROD fabric" | PROD Fabric | BFC |
| "PROD diagram" | PROD Fabric | BFC |
| "UMN PROD" or "PROD UMN" | UMN PROD | Management Core |
| "Corp" or "Corp fabric" | Corp NAP | NAP fabric |
| "NAP" or "NAP fabric" | Corp NAP | NAP fabric |
| "DSN" | DSN | DSN fabric |
| "Console" | Console | Console fabric |

**Key Rule:**
- **Without "UMN"**: EC2 = BFC fabric, PROD = BFC fabric
- **With "UMN"**: Explicitly requests management core topology

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