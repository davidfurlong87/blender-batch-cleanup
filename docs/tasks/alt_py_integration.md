# alt.py Integration Analysis

## What alt.py does

`alt.py` is a render-based brush preview pipeline from a separate developer. Instead of
using Blender's built-in asset preview generator, it **physically renders the brush texture
as a displaced mesh** and uses that render as the brush icon.

### Core mechanism

1. Appends a dedicated editor scene from `BrushEditorSetup.blend`, which contains:
   - Pre-built preview meshes: `PreviewSphere`, `PreviewPlane`
   - Cameras: `BrushPreviewCameraFlat`, `BrushPreviewCameraTilted`, `BrushPreviewCamereSphere`
   - A `TextureDisplacement` geometry nodes modifier already wired up on those meshes
2. Feeds the brush texture image into the geometry nodes (`Input_2`) and adjusts
   displacement strength/bias via the other node inputs
3. Renders at **256×256 using Workbench** (fast, no samples, no ray tracing)
4. For Blender 5, loads a compositing node group (`BrushPreview`) from
   `BrushEditor_5_0_CompositingNodes.blend` to handle background transparency
5. Loads the rendered PNG as the asset preview via `lib_id_load_custom_preview`
   (Blender ≥ 4.3) or `use_custom_icon` / `icon_filepath` (older Blender)

The result is a proper brush stroke preview — deformed geometry — rather than a flat
texture swatch.

---

## External dependencies (currently missing from repo)

| File | Purpose |
|---|---|
| `BrushEditorSetup.blend` | Editor scene, preview meshes, cameras, `TextureDisplacement` node group |
| `BrushEditor_5_0_CompositingNodes.blend` | Blender 5 compositing node groups (`BrushPreview`, `Heightmap`) |

Both files must live in the addon directory alongside `alt.py`. Without them, none of
the rendering functions (`render_preview_image`, `render_heightmap`, `render_vdm`) can run.

---

## Integration points with the current batch import workflow

### 1. `render_preview_image()` replaces `_generate_preview_for_brush()`
The function at line 1666 takes a brush, its texture image, and displacement settings,
renders the preview, and calls `lib_id_load_custom_preview` at the end. This is a
direct drop-in replacement for the `lib_id_generate_preview` primary path in the
current helper — producing a significantly higher-quality result.

Any call must be wrapped in `OpenEditorSceneAndWorkspace` / `ReturnToNormalWorkspaceAndScene`
to set up and tear down the temporary editor scene.

### 2. Modal operator pattern — critical for batch use
The current `BRUSHES_OT_generate_missing_previews` is a **synchronous** operator that
blocks Blender for the full batch. Alt.py uses a **modal** pattern — one brush per
event tick, returning `RUNNING_MODAL` between each — keeping Blender responsive.
`RerenderPreviewImages` (line 1405) is essentially the same operator as the generate
button and should be used as the model for the replacement.

### 3. Fallback chain
Brushes with no texture image cannot be rendered this way.
The existing `lib_id_generate_preview` call should remain as a secondary fallback
for those cases.

---

## TODO

### Blockers
- [ ] Obtain `BrushEditorSetup.blend` from the other developer and add to addon directory
- [ ] Obtain `BrushEditor_5_0_CompositingNodes.blend` and add to addon directory

### Integration
- [ ] Move `OpenEditorSceneAndWorkspace` and `ReturnToNormalWorkspaceAndScene` to shared
      scope so both `alt.py` and `__init__.py` can call them
- [ ] Replace the body of `_generate_preview_for_brush` with a call to
      `render_preview_image`, wrapped in the open/close scene helpers
- [ ] Convert `BRUSHES_OT_generate_missing_previews` from a plain operator to a modal
      operator, using `RerenderPreviewImages` as the reference implementation
- [ ] Keep `lib_id_generate_preview` as a fallback for brushes with no texture image

### Quality / UX
- [ ] Expose preview type (Flat / Tilted / Sphere) as a user-facing property in the
      batch import panel, mirroring the setting in alt.py's `BrushImportSettings`
- [ ] Expose displacement multiplier per brush type (VDM vs heightmap) in the panel
- [ ] Show per-brush progress feedback during modal generation (e.g. `{n}/{total}` in
      the header or status bar)
- [ ] Add a cancel path (ESC) to the modal generate operator, matching alt.py's pattern

### Cleanup
- [ ] Decide whether `alt.py` remains a standalone file or is fully merged into
      `__init__.py` once the blend files are available
- [ ] Remove the now-redundant texture pixel fallback in `_generate_preview_for_brush`
      once the render pipeline is confirmed working
