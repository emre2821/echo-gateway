# Eden Gateway MCP Server - Canonized Structure

This is the **canonized** version of the Eden Gateway MCP Server, organized according to Eden's trifold zoning model.

## 🜂 District Structure

### 🔥 ROOT (Identity & Memory)
- **Purpose**: Identity, memory, lore, ritual, governance
- **Rules**: Read-only by default, never executed, never auto-refactored
- **Contains**:
  - `lore/` - Core documentation and project history
  - `rituals/` - Configuration templates and ceremonial files
  - `concepts/` - Architectural concepts and design patterns
  - `research/` - Technical research and exploratory documents
  - `cosmology/` - Project cosmology and worldview

### ⚡ SPARK (Runtime Engine)
- **Purpose**: Runtime engine and production systems
- **Rules**: Must run, must be auditable, allowed to change, versioned and test-bound
- **Contains**:
  - `src/` - Source code and core implementations
  - `services/` - Production services and servers
  - `tests/` - Test suites and validation
  - `scripts/` - Build and deployment scripts
  - `applications/` - Complete applications
  - `core/` - Core system components
  - `tools/` - Production tools and utilities
  - `mcp/` - MCP-specific implementations
  - `gateway/` - Gateway and bridge components

### 🌊 DELTA (Change Space)
- **Purpose**: Change-space and incubation zone
- **Rules**: Never trusted as source of truth, never production dependency, free to mutate
- **Contains**:
  - `experiments/` - Experimental features and prototypes
  - `drafts/` - Draft implementations and temporary files
  - `prototypes/` - Prototype systems and abandoned structures
  - `rewrites/` - Rewrite attempts and alternative implementations
  - `abandoned/` - Deprecated and abandoned code

## 📋 Flow Constraint

```
root → delta → spark
```

No reverse movement without explicit dreambearer consent.

## 🔗 Canon Binding

See `canon_binding.json` for the complete project binding configuration.

## 🚀 Quick Start

1. Navigate to `spark/services/` for production servers
2. Check `root/lore/` for project documentation
3. Experiment in `delta/` without affecting production systems

---

*This structure follows Eden's trifold governance model and project cohesion canon binding v25-5*
