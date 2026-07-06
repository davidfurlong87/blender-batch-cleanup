# Algorithm Separation Guide

## The Golden Rule
**When in doubt: If it doesn't need `import bpy`, it shouldn't have `import bpy`.**

**Algorithm logic should work without Blender. If you can't test it in a plain Python script, it's too coupled.**


## 5-Step Migration Process

### Step 1: Identify What to Separate

**Ask yourself:**
- Does this function do things which would work in any python project (outside of blender)? → Separate it
- Does this function create/modify Blender objects? → Keep it in adapter
- Does this class store algorithm state? → Separate it
- Does this class store Blender objects? → Split it

**Quick Test:**
```python
# Can you test this function without Blender running?
# YES → Should be in algorithm layer
# NO → Should be in adapter layer
```

### Step 2: Create Pure Algorithm Modules

**Create the structure:**

**Start with the simplest pure function:**

### Step 3: Create Pure Data Classes

**Extract data from Blender-dependent classes:**

### Step 4: Create Blender Adapter

**Translate between Blender and algorithm:**

### Step 5: Update Operators to Use Adapter

**Modify operators to use adapter instead of mixed code:**

## Migration Checklist

For each function/class you're migrating:

### Algorithm Functions
- [ ] Remove all `import bpy` statements
- [ ] Remove all Blender object references
- [ ] Remove all mesh operations
- [ ] Remove all collection operations
- [ ] Use pure Python data structures only
- [ ] Write unit test (without Blender)
- [ ] Verify test passes

### Data Classes
- [ ] Remove `obj_source` / `mesh_obj` attributes
- [ ] Store only IDs/names instead of Blender objects
- [ ] Remove methods that call Blender functions
- [ ] Keep only pure data and algorithm logic
- [ ] Write unit test
- [ ] Verify test passes

### Adapter Functions
- [ ] Create conversion function (Blender → Algorithm)
- [ ] Create conversion function (Algorithm → Blender)
- [ ] Create visualization function
- [ ] Test with simple case
- [ ] Verify Blender objects created correctly

### Operators
- [ ] Get adapter instance
- [ ] Call adapter methods (not algorithm directly)
- [ ] Handle UI feedback
- [ ] Test in Blender
- [ ] Verify functionality unchanged

---

## Common Scenarios

### Scenario 1: Function uses Blender objects

**Before:**
```python
def collapse_cell(cell):
    # ... algorithm logic ...
    module_obj = module.obj_source  # ❌ Blender object
    duplicate = duplicate_and_move_and_return(module_obj, location)
```

**After:**
```python
# Algorithm layer
def collapse_cell(self, x, y):
    # ... algorithm logic ...
    return selected_module  # ✅ Just return data

# Adapter layer
def collapse_cell_and_visualize(self, x, y):
    selected = self.algorithm.collapse_cell(x, y)
    self._create_object(x, y, selected.id)  # Blender code here
```

### Scenario 2: Class stores Blender objects

**Before:**
```python
class WFCModule:
    def __init__(self, name, obj_source):  # ❌ Blender object
        self.name = name
        self.obj_source = obj_source
```

**After:**
```python
# Algorithm layer
class AlgorithmModule:
    def __init__(self, module_id, weight):  # ✅ Pure data
        self.id = module_id
        self.weight = weight

# Adapter layer
class BlenderWFCAdapter:
    def __init__(self):
        self.module_map = {}  # id -> bpy.types.Object
```

### Scenario 3: Global state

**Before:**
```python
all_grid_cells = {}  # ❌ Global state

def propagate(cell):
    for key in all_grid_cells.keys():  # ❌ Uses global
        # ...
```

**After:**
```python
# Algorithm layer
class WFCAlgorithm:
    def __init__(self):
        self.grid = Grid()  # ✅ Instance state
    
    def propagate(self, x, y):
        for cell in self.grid.get_all_cells():  # ✅ Uses instance
            # ...

# Adapter layer
class BlenderWFCAdapter:
    def __init__(self):
        self.algorithm = WFCAlgorithm()  # ✅ Owns algorithm instance
```

---

## Testing Your Separation

### Test 1: Can you import the algorithm module?

```python
# In a plain Python script (no Blender)
from wfc_algorithm.core import WFCAlgorithm

# If this works, you've separated successfully!
algo = WFCAlgorithm(modules=[], grid_size=(10, 10))
```

### Test 2: Can you run algorithm tests without Blender?

```bash
# From command line (no Blender)
cd addons/blender-wfc
python -m pytest wfc_algorithm/tests/

# If tests run, you've separated successfully!
```

### Test 3: Does the Blender addon still work?

```python
# In Blender
# Click "Full Collapse" button
# If it works, you've maintained functionality!
```

---

## Troubleshooting

### Problem: "ImportError: cannot import name 'bpy'"

**Cause:** Algorithm module is trying to import bpy

**Solution:** Remove all `import bpy` from algorithm modules

### Problem: "Algorithm tests fail with 'module has no attribute obj_source'"

**Cause:** Algorithm code still references Blender objects

**Solution:** Replace Blender object references with IDs/data

### Problem: "Blender addon doesn't work after migration"

**Cause:** Adapter not properly converting between layers

**Solution:** Check adapter conversion functions, verify mappings

### Problem: "Can't test algorithm without Blender"

**Cause:** Algorithm still has Blender dependencies

**Solution:** Review algorithm code, remove all Blender imports/objects

---

## Success Criteria

You've successfully separated when:

✅ Algorithm module has zero `import bpy` statements  
✅ Algorithm tests run without Blender  
✅ Algorithm classes store no Blender objects  
✅ Adapter handles all Blender interaction  
✅ Operators use adapter, not algorithm directly  
✅ Blender addon functionality unchanged  

---

## Next Steps

1. Start with simplest function (`score_module`)
2. Write test for it
3. Move to next function
4. Repeat until all algorithm code is separated
5. Create adapter
6. Update operators
7. Test everything
8. Remove old code

See `docs/architecture/ALGORITHM_SEPARATION_GUIDE.md` for detailed explanation.



