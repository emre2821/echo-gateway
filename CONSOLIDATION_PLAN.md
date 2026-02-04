# Eden Gateway MCP Server Consolidation Plan

## Problem Analysis
The CodeWolf Project Health Report reveals critical structural issues:
- **Overall Score: 81/100** with **67% CodeWolf Compliance**
- **19 critical files (0/100 scores)** exceeding 500+ lines
- **Extensive file duplication** across multiple directories
- **Violation of Eden trifold zoning model**

## Duplicate Files Identified

### Critical Duplicates (0/100 CodeWolf scores)
1. **server.js** (890 lines) - 4 locations:
   - `/server.js` ❌ REMOVE
   - `/MCP_server/server.js` ❌ REMOVE  
   - `/CLEAN_STRUCTURE/delta/drafts/server.js` ❌ REMOVE
   - `/CLEAN_STRUCTURE/spark/services/server.js` ✅ KEEP

2. **server-gateway.js** (528 lines) - 4 locations:
   - `/server-gateway.js` ❌ REMOVE
   - `/MCP_server/server-gateway.js` ❌ REMOVE
   - `/CLEAN_STRUCTURE/delta/drafts/server-gateway.js` ❌ REMOVE
   - `/CLEAN_STRUCTURE/spark/gateway/server-gateway.js` ✅ KEEP

3. **edenos_mcp_server_bundle.py** (881 lines) - 2 locations:
   - `/edenos_mcp_server_bundle.py` ❌ REMOVE
   - `/CLEAN_STRUCTURE/spark/services/edenos_mcp_server_bundle.py` ✅ KEEP

### Moderate Duplicates
4. **mcp-gateway.js** (362 lines) - 5 locations:
   - `/mcp-gateway.js` ❌ REMOVE
   - `/gateway/mcp-gateway.js` ❌ REMOVE
   - `/MCP_server/gateway/mcp-gateway.js` ❌ REMOVE
   - `/CLEAN_STRUCTURE/delta/drafts/mcp-gateway.js` ❌ REMOVE
   - `/CLEAN_STRUCTURE/spark/gateway/mcp-gateway.js` ✅ KEEP

5. **archive_tools.py** (442 lines) - 5 locations:
   - `/archive_tools.py` ❌ REMOVE
   - `/tools/archive_tools.py` ❌ REMOVE
   - `/MCP_server/tools/archive_tools.py` ❌ REMOVE
   - `/CLEAN_STRUCTURE/delta/drafts/archive_tools.py` ❌ REMOVE
   - `/CLEAN_STRUCTURE/spark/tools/archive_tools.py` ✅ KEEP

6. **organizer_tools.py** (383 lines) - 5 locations:
   - `/organizer_tools.py` ❌ REMOVE
   - `/tools/organizer_tools.py` ❌ REMOVE
   - `/MCP_server/tools/organizer_tools.py` ❌ REMOVE
   - `/CLEAN_STRUCTURE/delta/drafts/organizer_tools.py` ❌ REMOVE
   - `/CLEAN_STRUCTURE/spark/tools/organizer_tools.py` ✅ KEEP

## Eden Trifold Zoning Structure

### Root District (identity, memory, lore - READ-ONLY)
- `/lore/` - Documentation, rituals, concepts
- `/research/` - Research findings, cosmology
- `/governance/` - Rules, policies, compliance reports

### Spark District (runtime engine - PRODUCTION SYSTEMS)
- `/CLEAN_STRUCTURE/spark/` ✅ **CANONICAL LOCATION**
- `/services/` - Core MCP servers
- `/gateway/` - Gateway routing
- `/tools/` - Production tools
- Must be: auditable, versioned, test-bound

### Delta District (change-space - INCUBATION)
- `/CLEAN_STRUCTURE/delta/` ✅ **INCUBATION ZONE**
- `/drafts/` - Experimental code
- `/experiments/` - Prototypes
- Never trusted as source of truth

## Consolidation Strategy

### Phase 1: Remove Duplicates
1. Create backup of current structure
2. Remove all duplicate files, keeping only CLEAN_STRUCTURE versions
3. Update any references to removed files

### Phase 2: Refactor Monolithic Files
1. **mcp_server_hub.py** (1351 lines) → Split into:
   - `hub-core.py` - Core hub logic
   - `context-manager.py` - Context window management
   - `chaos-handler.py` - CHAOS file processing
   - `permission-manager.py` - Permission system

2. **index.js** (759 lines) → Split into:
   - `file-reader-core.js` - Core reading logic
   - `format-handlers/` - Individual format parsers
   - `dependency-manager.js` - Lazy loading

### Phase 3: Establish Canonical Structure
1. Move all production code to `/CLEAN_STRUCTURE/spark/`
2. Move documentation to `/lore/`
3. Move experiments to `/CLEAN_STRUCTURE/delta/`
4. Create `canon_binding.json` for project cohesion

## Expected Results
- **Eliminate 25+ duplicate files**
- **Reduce codebase size by ~40%**
- **Improve CodeWolf compliance from 67% to 85%+**
- **Establish proper Eden governance structure**
- **Enable proper testing and auditing**

## Safety Measures
- Full backup before any deletions
- Step-by-step verification
- Preserve all functionality
- Maintain backward compatibility where possible
