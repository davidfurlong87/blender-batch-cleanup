# Quick Start: Adding a New Module

## The Simple Steps

When you create a new Python file in the addon, follow these steps:

### 1. Determine Dependencies

Ask yourself: **"What does my new module import from other addon modules?"**

Example:
```python
# my_new_module.py
from .wfc_values import module_size  # Depends on wfc_values
from .wfc_classes import WFCCell     # Depends on wfc_classes
```

This module depends on `wfc_values` and `wfc_classes`.

### 2. Find the Reload Level

Look at `__init__.py` and find where your dependencies are reloaded:
- `wfc_values` is in **Level 0**
- `wfc_classes` is in **Level 2**

Your module must be reloaded **AFTER** both, so it goes in **Level 3 or higher**.

### 3. Add Reload Entry

In `__init__.py`, add your module to the appropriate level:

```python
# Level 3: Modules that depend on Level 0-2
if "my_new_module" in locals():
    importlib.reload(my_new_module)
```

**Important:** Use the module name WITHOUT the `.py` extension!

### 4. Add Import Statement

After the reload block (after the "Imports" comment), add your import:

```python
from .my_new_module import MyClass, my_function
```

### 5. Test It

1. Make a small change to your new module (add a print statement)
2. In Blender: Preferences → Add-ons → Disable "wfc"
3. Enable "wfc" again
4. Trigger your code
5. Verify the print statement appears

## Common Scenarios

### Scenario 1: Pure utility module (no addon imports)

```python
# my_utils.py
import math

def calculate_something(x):
    return math.sqrt(x)
```

**Action:** Add to **Level 0** (no dependencies)

### Scenario 2: Uses only base modules

```python
# my_connector_helper.py
from .wfc_enums import CONNECTORS
from .wfc_values import module_size
```

**Action:** Add to **Level 1** (depends only on Level 0)

### Scenario 3: Uses classes

```python
# my_cell_processor.py
from .wfc_classes import WFCCell
from .wfc_values import module_size
```

**Action:** Add to **Level 3** (depends on wfc_classes which is Level 2)

### Scenario 4: Uses everything

```python
# my_complex_operator.py
from .wfc_classes import WFCCell
from .primitive_data import build_default_primitives
from .wfc_grid_builder import build_wfc_grid
```

**Action:** Add to **Level 4** (depends on Level 3 modules)

## Troubleshooting

### Problem: Changes don't appear after reload

**Check:**
1. Is your module in the reload block?
2. Is it reloaded BEFORE modules that import from it?
3. Did you import AFTER the reload block?

### Problem: "Module not found" error

**Check:**
1. Is the filename correct? (no `.py` extension in reload)
2. Is the file in the correct directory?
3. Did you use relative import (`.module_name`)?

### Problem: Circular import error

**Solution:** You have a circular dependency. Refactor to break the cycle:
- Move shared code to a lower-level module
- Use late imports (import inside functions)
- Restructure your code

## The Dependency Levels (Current State)

```
Level 0: wfc_values, wfc_enums
Level 1: wfc_materials, collectiontools.collection_creation
Level 2: wfc_classes, primitive_generation_tools, helper_functions
Level 3: primitive_data_actual, wfc_grid_builder, wfc_plots, wfc_plot_tools
Level 4: primitive_data, wfc_collections, wfc_operators
```

## Remember

✅ **DO:** Reload before importing
✅ **DO:** Reload in dependency order
✅ **DO:** Test after adding

❌ **DON'T:** Import before reloading
❌ **DON'T:** Forget to add new modules
❌ **DON'T:** Reload in wrong order

