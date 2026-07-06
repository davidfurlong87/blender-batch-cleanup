# Blender Addon Module Reloading Guide

## The Golden Rule

**When in doubt, always remember: Reload modules BEFORE importing from them, and reload in dependency order (dependencies first, dependents last).**

## Why Module Reloading Matters

When developing Blender addons, Python caches imported modules. Without proper reloading:
- Code changes won't take effect until Blender restarts
- You'll waste time restarting Blender repeatedly
- Old class definitions persist, causing registration errors

## How Module Reloading Works Under the Hood

### The Python Module Cache

When you `import mymodule`, Python:
1. Checks if `mymodule` is in `sys.modules` (the module cache)
2. If yes: Returns the cached version (ignoring file changes)
3. If no: Loads the file, executes it, caches it in `sys.modules`, returns it

### The `locals()` Check

```python
if "bpy" in locals():
    # This is a RELOAD (addon being re-enabled)
else:
    # This is FIRST LOAD (addon being enabled for first time)
```

**Why this works:**
- On first load: `locals()` is empty, so `"bpy"` is not in it
- On reload: Previous imports are in `locals()`, including `bpy`
- This detects whether we need to reload our modules

### The `importlib.reload()` Function

```python
import importlib
importlib.reload(my_module)
```

**What it does:**
1. Re-executes the module's Python file
2. Updates the existing module object in `sys.modules`
3. **Critical:** Only updates the module object itself, not references to it

**What it doesn't do:**
- Doesn't automatically reload modules imported by that module
- Doesn't update `from module import X` references (they still point to old objects)

## The Correct Reload Pattern

### Step 1: Check if this is a reload
```python
if "bpy" in locals():
    import importlib
    # ... reload modules here
```

### Step 2: Reload in dependency order
```python
# Reload base modules first (no internal dependencies)
if "wfc_values" in locals():
    importlib.reload(wfc_values)
if "wfc_enums" in locals():
    importlib.reload(wfc_enums)

# Then modules that depend on base modules
if "wfc_classes" in locals():
    importlib.reload(wfc_classes)

# Finally, modules that depend on everything else
if "wfc_operators" in locals():
    importlib.reload(wfc_operators)
```

### Step 3: Import AFTER reloading
```python
# All reloads done, now import
from .wfc_values import CollectionNames, module_size
from .wfc_classes import WFCModule, WFCCell
```

## Common Pitfalls

### ❌ Pitfall 1: Importing before reloading
```python
# WRONG - imports happen before reload
from .wfc_classes import WFCModule

if "bpy" in locals():
    importlib.reload(wfc_classes)  # Too late!
```

### ❌ Pitfall 2: Wrong reload order
```python
# WRONG - wfc_operators depends on wfc_classes
if "wfc_operators" in locals():
    importlib.reload(wfc_operators)
if "wfc_classes" in locals():
    importlib.reload(wfc_classes)  # Should be first!
```

### ❌ Pitfall 3: Forgetting to reload a module
```python
# WRONG - wfc_plots is not reloaded
if "wfc_classes" in locals():
    importlib.reload(wfc_classes)
# wfc_plots forgotten!

from .wfc_plots import *  # Will use old cached version
```

### ❌ Pitfall 4: Duplicate reload checks
```python
# WRONG - primitive_data_actual checked twice
if "primitive_data_actual" in locals():
    importlib.reload(primitive_data_actual)
# ... other reloads ...
if "primitive_data_actual" in locals():  # Duplicate!
    importlib.reload(primitive_data_actual)
```

## Quick Reference: Reload Checklist

When adding a new module to your addon:

1. ✅ Add reload check in `__init__.py` BEFORE imports
2. ✅ Place reload in correct dependency order
3. ✅ Use exact module name (without `.py` extension)
4. ✅ Import from the module AFTER the reload block
5. ✅ For subpackages, reload the submodule, not the package

## Dependency Order for This Addon

```
Level 0 (No dependencies):
  - wfc_values
  - wfc_enums

Level 1 (Depends on Level 0):
  - wfc_materials
  - collectiontools.collection_creation

Level 2 (Depends on Level 0-1):
  - wfc_classes
  - primitive_generation_tools

Level 3 (Depends on Level 0-2):
  - primitive_data_actual
  - wfc_grid_builder
  - wfc_plots
  - wfc_plot_tools

Level 4 (Depends on Level 0-3):
  - primitive_data
  - wfc_collections
  - wfc_operators

Level 5 (Top level, depends on everything):
  - (none currently)
```

## Testing Your Reload System

1. Make a small change to a module (add a print statement)
2. In Blender: Preferences → Add-ons → Disable your addon
3. Enable your addon again
4. Trigger the code path with your change
5. Verify the change took effect (print appears)

If the change doesn't appear, check:
- Is the module in the reload block?
- Is it reloaded before modules that depend on it?
- Are you importing after the reload block?

