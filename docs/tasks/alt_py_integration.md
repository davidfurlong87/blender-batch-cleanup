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

## Migration strategy

Old and new functionality run side-by-side until the render pipeline is fully validated.
`alt.py` is kept as a read-only reference. New code lives in `preview_renderer.py`.

### Panel layout (current state)

```
[ Import Brushes From Folders ]       ← existing, generates previews via lib_id_load_custom_preview
[ Import Brushes (No Preview)  ]      ← new stub, skips all preview logic

[ Scan Missing Previews ] [ Generate Missing Previews ]   ← existing fallback pipeline
[ Generate Previews (Render) ]        ← new stub, will call preview_renderer.generate_preview()
```

---

## TODO

### Blockers
- [ ] Obtain `BrushEditorSetup.blend` from the other developer and place in
      `addons/display_case/brushes_creator/`
- [ ] Obtain `BrushEditor_5_0_CompositingNodes.blend` and place in the same folder

### Phase 1 — preview_renderer.py internals (unblock once blend files arrive)
- [ ] Implement `_ensure_editor_scene()`: append `BrushEditScene` from the setup
      blend without switching the active window scene
- [ ] Implement `_get_compositing_node_group()`: append the Blender 5 node groups
      and rewire the Render Layers node to the editor scene
- [ ] Implement `_set_render_visibility()`: use `hide_render` only (not `hide_set`)
      so the user's viewport is unaffected
- [ ] Implement `generate_preview()`: wire up all the above, call
      `bpy.ops.render.render(write_still=True, scene=_EDITOR_SCENE_NAME)`, then
      call `lib_id_load_custom_preview` with the rendered PNG
- [ ] Expose `preview_type` (Flat / Tilted / Sphere) as a property in
      `BrushCreatorProperties` and pass it through to `generate_preview()`
- [ ] Expose displacement multiplier (VDM vs heightmap) in the panel

### Phase 2 — wire new operators to preview_renderer
- [ ] Implement `BRUSHES_OT_import_no_preview`: reuse the existing import loop
      from `BRUSHES_OT_import_from_folders` but skip `_apply_preview` entirely
- [ ] Implement `BRUSHES_OT_generate_previews_render` as a **modal operator**:
      one brush per event tick, ESC to cancel, matching `RerenderPreviewImages`
      in `alt.py` as the reference; show `{n}/{total}` progress in the header
- [ ] Add a cancel path (ESC) and `ReturnToNormalWorkspaceAndScene` equivalent
      to clean up the editor scene reference on cancel

### Phase 3 — validation and migration
- [ ] Confirm rendered previews display correctly in the Asset Browser on
      Blender 4.x and 5.x
- [ ] Once render pipeline is confirmed, wire the existing
      `Import Brushes From Folders` button to use `generate_preview()` as its
      primary path, falling back to `lib_id_load_custom_preview` / texture copy
- [ ] Remove `_generate_preview_for_brush` texture-pixel fallback once no
      longer needed
- [ ] Decide final fate of `alt.py` (keep as reference or remove)

### Quality / UX
- [ ] Show a panel warning when blend files are missing, explaining what to add
      and where (drives `BRUSHES_OT_generate_previews_render` error state)
