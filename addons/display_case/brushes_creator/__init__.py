import bpy
from bpy.props import BoolProperty, StringProperty, FloatProperty, EnumProperty, PointerProperty
import pathlib
import os
import uuid as _uuid_mod

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tga', 'webp', 'hdr'}

# Ordered list of stroke methods cycled by the hotkey operator.
STROKE_METHOD_CYCLE = ('SPACE', 'DOTS', 'DRAG_DOT', 'AIRBRUSH', 'ANCHORED', 'LINE', 'CURVE')

_CATS_HEADER = (
    "# This is an Asset Catalog Definition file for Blender.\n"
    "#\n"
    "# Empty lines and lines starting with `#` will be ignored.\n"
    '# The remaining lines are of the format "UUID:catalog/path/for/assets:simple catalog name"\n'
    "\n"
    "VERSION 1\n"
    "\n"
)

# Sentinel identifiers used in EnumProperty values.
_CURRENT_FILE = "__current_file__"
_NEW_CATALOG  = "__new__"

# Module-level caches — Blender requires enum item lists to stay alive in
# memory between draws, otherwise it can crash or show garbage strings.
_library_enum_cache: list = []
_catalog_enum_cache: list = []


def _read_catalog_file(cats_file: str) -> dict:
    """Parse a blender_assets.cats.txt and return {catalog_path: uuid}."""
    catalog_map: dict[str, str] = {}
    if not os.path.exists(cats_file):
        return catalog_map
    with open(cats_file, 'r', encoding='utf-8') as fh:
        for raw in fh:
            line = raw.rstrip('\n')
            if line.startswith('#') or not line.strip() or line.startswith('VERSION'):
                continue
            parts = line.split(':', 2)
            if len(parts) == 3:
                cat_uuid, cat_path, _ = parts
                catalog_map[cat_path] = cat_uuid
    return catalog_map


def _ensure_catalog_in_file(catalog_path: str, cats_file: str) -> str:
    """Ensure *catalog_path* (and all its ancestors) exist in *cats_file*.
    Creates the file with a standard header if it does not exist yet.
    Returns the UUID of the leaf catalog."""
    catalog_map = _read_catalog_file(cats_file)

    segments = catalog_path.split('/')
    new_entries: list[str] = []
    for depth in range(1, len(segments) + 1):
        ancestor = '/'.join(segments[:depth])
        if ancestor not in catalog_map:
            new_uuid = str(_uuid_mod.uuid4())
            catalog_map[ancestor] = new_uuid
            new_entries.append(f"{new_uuid}:{ancestor}:{segments[depth - 1]}")

    if new_entries:
        if not os.path.exists(cats_file):
            with open(cats_file, 'w', encoding='utf-8') as fh:
                fh.write(_CATS_HEADER)
        with open(cats_file, 'a', encoding='utf-8') as fh:
            fh.write('\n'.join(new_entries) + '\n')

    return catalog_map[catalog_path]


def _library_enum_items(self, context):
    global _library_enum_cache
    items = [(_CURRENT_FILE, "Current File",
              "Keep assets in the currently open .blend file (no library required)")]
    try:
        for lib in context.preferences.filepaths.asset_libraries:
            abs_path = os.path.abspath(bpy.path.abspath(lib.path))
            items.append((abs_path, lib.name, abs_path))
    except Exception as e:
        print(f"[brushes_creator] Could not read asset library list: {e}")
    _library_enum_cache = items
    return _library_enum_cache


def _catalog_enum_items(self, context):
    global _catalog_enum_cache
    items = [(_NEW_CATALOG, "+ New Catalog…",
              "Type a new catalog path in the field below")]
    lib_path = self.selected_library
    if lib_path and lib_path != _CURRENT_FILE:
        cats_file = os.path.join(lib_path, "blender_assets.cats.txt")
        catalog_map = _read_catalog_file(cats_file)
        for cat_path in sorted(catalog_map.keys()):
            items.append((catalog_map[cat_path], cat_path, cat_path))
    _catalog_enum_cache = items
    return _catalog_enum_cache


# ==========================================================
# Properties
# ==========================================================

class BrushCreatorProperties(bpy.types.PropertyGroup):
    textures_dir: StringProperty(
        name="Images Folder",
        subtype='DIR_PATH',
        description="Folder containing texture image files to import as brushes"
    ) # type: ignore
    thumbs_dir: StringProperty(
        name="Thumbnails Folder",
        subtype='DIR_PATH',
        description="Folder with preview images matched by filename stem (optional)"
    ) # type: ignore
    use_name_prepost: BoolProperty(
        name="Use Prefix / Suffix",
        default=False,
        description="Prepend/append strings to generated brush names"
    ) # type: ignore
    name_pre: StringProperty(
        name="Prefix", 
        description="Prepend to brush names"
        ) # type: ignore
    name_post: StringProperty(name="Suffix", description="Append to brush names") # type: ignore
    brush_type: EnumProperty(
        name="Brush Type",
        items=[
            ('TEXTURE_PAINT', "Texture Paint", "Create texture paint brushes"),
            ('SCULPT', "Sculpt", "Create sculpt brushes"),
            ('BOTH', "Both", "Create both brush types"),
        ],
        default='BOTH'
    ) # type: ignore
    stroke_type: EnumProperty(
        name="Stroke Type",
        items=[
            ('SPACE', "Space", "Use Space stroke method"),
            ('ANCHORED', "Anchored", "Use Anchored stroke method"),
            ('BOTH', "Both", "Create one brush per stroke method"),
        ],
        default='SPACE'
    ) # type: ignore
    tp_strength: FloatProperty(name="Paint Strength", default=1.0, min=0.0, max=2.0)
    sculpt_strength: FloatProperty(name="Sculpt Strength", default=0.3, min=0.0, max=2.0)
    texture_map_mode: EnumProperty(
        name="Texture Mapping",
        description="How the texture is mapped onto the brush stroke",
        items=[
            ('VIEW_PLANE', "View Plane", "Project texture onto the view plane"),
            ('AREA_PLANE', "Area Plane", "Project texture onto the area plane (sculpt only)"),
            ('TILED', "Tiled", "Tile the texture across the surface"),
            ('RANDOM', "Random", "Randomize texture position per dab"),
            ('STENCIL', "Stencil", "Use the texture as a stencil (texture paint only)"),
            ('3D', "3D", "Use 3D texture coordinates (sculpt only)"),
        ],
        default='RANDOM'
    ) # type: ignore

    sculpt_front_faces_only: BoolProperty(
        name="Front Faces Only",
        description="Only apply the sculpt brush to front-facing faces (sculpt brushes only)",
        default=True,
    ) # type: ignore

    selected_library: EnumProperty(
        name="Library",
        description="Asset library to add the brushes to",
        items=_library_enum_items,
    )  # type: ignore

    selected_catalog: EnumProperty(
        name="Catalog",
        description="Catalog within the selected library",
        items=_catalog_enum_items,
    )  # type: ignore

    new_catalog_path: StringProperty(
        name="New Catalog Path",
        description="Path for the new catalog (e.g. 'Brushes' or 'Brushes/Sculpt')",
        default="Brushes",
    )  # type: ignore

    # Internal texture settings (not exposed in panel)
    img_use_existing: BoolProperty(default=True) # type: ignore
    texture_calculate_alpha: BoolProperty(default=True) # type: ignore
    texture_fake_user: BoolProperty(default=True) # type: ignore
    texture_interpolation: BoolProperty(default=True) # type: ignore


# ==========================================================
# Operator
# ==========================================================

class BRUSHES_OT_import_from_folders(bpy.types.Operator):
    bl_idname = "brushes.import_from_folders"
    bl_label = "Import Brushes From Folders"
    bl_description = "Create brushes from all images in the selected textures folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.brush_creator_props

        tex_dir = bpy.path.abspath(props.textures_dir) if props.textures_dir else None
        thumb_dir = bpy.path.abspath(props.thumbs_dir) if props.thumbs_dir else None

        if not tex_dir or not os.path.isdir(tex_dir):
            self.report({'ERROR'}, "Images folder is invalid or not set")
            return {'CANCELLED'}

        files = sorted(
            f for f in os.listdir(tex_dir)
            if os.path.splitext(f)[1].lower().lstrip('.') in ALLOWED_EXTENSIONS
        )

        if not files:
            self.report({'WARNING'}, "No supported images found in the images folder")
            return {'CANCELLED'}

        # Resolve the catalog UUID before the import loop --------------------
        catalog_id = None
        lib_path   = props.selected_library
        sel_cat    = props.selected_catalog

        if sel_cat and sel_cat != _NEW_CATALOG:
            # Existing catalog — the enum identifier IS the UUID
            catalog_id = sel_cat

        elif sel_cat == _NEW_CATALOG:
            new_path = props.new_catalog_path.strip()
            if not new_path:
                self.report({'ERROR'}, "Enter a catalog path or select an existing catalog")
                return {'CANCELLED'}

            if lib_path == _CURRENT_FILE:
                if not bpy.data.filepath:
                    self.report({'WARNING'},
                        "Save the .blend file first to assign a catalog to Current File assets")
                else:
                    cats_file  = os.path.join(os.path.dirname(bpy.data.filepath),
                                              "blender_assets.cats.txt")
                    catalog_id = _ensure_catalog_in_file(new_path, cats_file)
            else:
                cats_file  = os.path.join(lib_path, "blender_assets.cats.txt")
                catalog_id = _ensure_catalog_in_file(new_path, cats_file)

            if catalog_id:
                print(f"[brushes_creator] Created catalog '{new_path}' ({catalog_id}) in {cats_file}")

        created = sum(
            1 for f in files
            if self._create_brush_from_file(os.path.join(tex_dir, f), thumb_dir, props, catalog_id)
        )

        if created:
            self.report({'INFO'}, f"Created {created} brush(es)")
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    area.tag_redraw()
        else:
            self.report({'WARNING'}, "No brushes were created")

        return {'FINISHED'}

    def _find_thumbnail(self, stem, thumb_dir):
        """Return the path of a thumbnail matching the texture stem, or None."""
        if not thumb_dir or not os.path.isdir(thumb_dir):
            return None
        for ext in ALLOWED_EXTENSIONS:
            candidate = os.path.join(thumb_dir, f"{stem}.{ext}")
            if os.path.exists(candidate):
                return candidate
        return None

    def _unique_brush_name(self, base):
        if base not in bpy.data.brushes:
            return base
        i = 1
        while True:
            candidate = f"{base}_{i:02d}"
            if candidate not in bpy.data.brushes:
                return candidate
            i += 1

    def _apply_preview(self, brush, thumb_path):
        if not thumb_path or not os.path.exists(thumb_path):
            return
        try:
            # Toolbar icon (3D viewport brush selector, Blender 3.x compat)
            if hasattr(brush, 'use_custom_icon'):
                brush.use_custom_icon = True
                brush.icon_filepath = thumb_path

            if brush.asset_data is not None:
                window = bpy.context.window_manager.windows[0]
                with bpy.context.temp_override(window=window, id=brush):
                    result = bpy.ops.ed.lib_id_load_custom_preview(filepath=thumb_path)
                if 'FINISHED' not in result:
                    print(f"[brushes_creator] Preview not loaded for '{brush.name}' (operator returned {result})")
        except Exception as e:
            print(f"Preview warning for {brush.name}: {e}")

    def _new_brush(self, name, mode, texture, strength, stroke, thumb_path,
                   map_mode='RANDOM', front_faces_only=False, catalog_id=None):
        # TODO: add checkbox which asks user if they want duplicate brushes, defaulting to false. skip creation if checkbox is false and brush name already exists. display a warning/info box for anything not created in this way
        brush = bpy.data.brushes.new(name=self._unique_brush_name(name), mode=mode)
        brush.texture = texture
        brush.strength = strength
        if hasattr(brush, 'use_fake_user'):
            brush.use_fake_user = True
        brush.asset_mark()
        if catalog_id and brush.asset_data is not None:
            brush.asset_data.catalog_id = catalog_id
        if stroke and hasattr(brush, 'stroke_method'):
            brush.stroke_method = stroke
        if brush.texture_slot:
            brush.texture_slot.map_mode = map_mode
        if mode == 'SCULPT' and hasattr(brush, 'use_frontface'):
            brush.use_frontface = front_faces_only
        self._apply_preview(brush, thumb_path)
        return brush

    def _create_brush_from_file(self, filepath, thumb_dir, props, catalog_id=None):
        try:
            stem = pathlib.Path(filepath).stem
            base_name = "".join(c for c in stem if c.isalnum() or c in ' _-')
            if props.use_name_prepost:
                base_name = props.name_pre + base_name + props.name_post

            image = bpy.data.images.load(filepath, check_existing=props.img_use_existing)
            image.name = base_name

            texture = bpy.data.textures.new(base_name, 'IMAGE')
            texture.use_calculate_alpha = props.texture_calculate_alpha
            texture.use_fake_user = props.texture_fake_user
            texture.use_interpolation = props.texture_interpolation
            texture.image = image

            thumb = self._find_thumbnail(stem, thumb_dir)

            # Determine which stroke methods to use
            if props.stroke_type == 'BOTH':
                strokes = [('SPACE', '_Space'), ('ANCHORED', '_Anchored')]
            else:
                strokes = [(props.stroke_type, '')]

            # TODO: when creating `BOTH` the 'TEXTURE_PAINT' paint brush is named normally, but the 'SCULPT' brush is named with a "_01" suffix, as the brush name already exists. an additional suffix should be added in this situation (_sculpt, _tpaint)
            if props.brush_type in {'TEXTURE_PAINT', 'BOTH'}:
                for stroke, suffix in strokes:
                    self._new_brush(base_name + suffix, 'TEXTURE_PAINT', texture, props.tp_strength, stroke, thumb, props.texture_map_mode, catalog_id=catalog_id)

            if props.brush_type in {'SCULPT', 'BOTH'}:
                for stroke, suffix in strokes:
                    self._new_brush(base_name + suffix, 'SCULPT', texture, props.sculpt_strength, stroke, thumb, props.texture_map_mode, props.sculpt_front_faces_only, catalog_id=catalog_id)

            return True

        except Exception as e:
            print(f"Failed to create brush from {filepath}: {e}")
            return False


# ==========================================================
# Panel draw (called by the main addon panel, not registered directly)
# ==========================================================

def draw_panel(layout, context):
    props = context.scene.brush_creator_props

    box = layout.box()
    box.label(text="Folders", icon='FILE_FOLDER')
    box.prop(props, "textures_dir", text="Images")
    box.prop(props, "thumbs_dir", text="Thumbnails")

    box = layout.box()
    box.label(text="Brush Settings", icon='BRUSH_DATA')
    box.prop(props, "brush_type", expand=True)
    box.separator()
    box.prop(props, "stroke_type", expand=True)
    box.separator()
    bt = props.brush_type
    if bt in {'TEXTURE_PAINT', 'BOTH'}:
        box.prop(props, "tp_strength")
    if bt in {'SCULPT', 'BOTH'}:
        box.prop(props, "sculpt_strength")
        box.prop(props, "sculpt_front_faces_only")
    box.separator()
    box.prop(props, "texture_map_mode")

    box = layout.box()
    box.label(text="Naming", icon='SORTALPHA')
    box.prop(props, "use_name_prepost")
    if props.use_name_prepost:
        row = box.row()
        row.prop(props, "name_pre")
        row.prop(props, "name_post")

    box = layout.box()
    box.label(text="Asset Catalog", icon='ASSET_MANAGER')
    box.prop(props, "selected_library", text="Library")
    box.prop(props, "selected_catalog", text="Catalog")
    if props.selected_catalog == _NEW_CATALOG:
        box.prop(props, "new_catalog_path", text="Path")
        if props.selected_library == _CURRENT_FILE and not bpy.data.filepath:
            box.label(text="Save the .blend file first", icon='ERROR')

    layout.operator("brushes.import_from_folders", icon='BRUSHES_ALL')


# ==========================================================
# Shared helper
# ==========================================================

def _active_brush(context):
    ts = context.tool_settings
    mode = context.mode
    if mode == 'SCULPT':
        return ts.sculpt.brush if ts.sculpt else None
    if mode == 'PAINT_TEXTURE':
        return ts.image_paint.brush if ts.image_paint else None
    if mode == 'PAINT_WEIGHT':
        return ts.weight_paint.brush if ts.weight_paint else None
    if mode == 'PAINT_VERTEX':
        return ts.vertex_paint.brush if ts.vertex_paint else None
    return None


# ==========================================================
# Stroke-method operators
# ==========================================================

class BRUSH_OT_set_stroke_method(bpy.types.Operator):
    """Set the active brush stroke method (used by the pie menu)"""
    bl_idname = "brush.set_stroke_method"
    bl_label = "Set Stroke Method"
    bl_options = {'REGISTER', 'UNDO'}

    method: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return _active_brush(context) is not None

    def execute(self, context):
        brush = _active_brush(context)
        brush.stroke_method = self.method
        self.report({'INFO'}, f"Stroke: {self.method.replace('_', ' ').title()}")
        return {'FINISHED'}


class BRUSH_OT_cycle_stroke_method(bpy.types.Operator):
    """Cycle the active brush through available stroke methods"""
    bl_idname = "brush.cycle_stroke_method"
    bl_label = "Cycle Brush Stroke Method"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _active_brush(context) is not None

    def execute(self, context):
        brush = _active_brush(context)
        current = brush.stroke_method
        try:
            idx = STROKE_METHOD_CYCLE.index(current)
        except ValueError:
            idx = 0
        next_method = STROKE_METHOD_CYCLE[(idx + 1) % len(STROKE_METHOD_CYCLE)]
        brush.stroke_method = next_method
        self.report({'INFO'}, f"Stroke: {next_method.replace('_', ' ').title()}")
        return {'FINISHED'}


# ==========================================================
# Stroke-method pie menu
# ==========================================================

# (stroke_method_id, display_label) in pie slice order:
# W, E, S, N, NW, NE, SW  (Blender fills slices in this sequence)
_PIE_ITEMS = (
    ('SPACE',     "Space"),
    ('ANCHORED',  "Anchored"),
    ('DOTS',      "Dots"),
    ('DRAG_DOT',  "Drag Dot"),
    ('AIRBRUSH',  "Airbrush"),
    ('LINE',      "Line"),
    ('CURVE',     "Curve"),
)

class BRUSH_MT_stroke_method_pie(bpy.types.Menu):
    bl_label = "Stroke Method"

    def draw(self, context):
        pie = self.layout.menu_pie()
        brush = _active_brush(context)
        current = brush.stroke_method if brush else None

        for method, label in _PIE_ITEMS:
            op = pie.operator(
                BRUSH_OT_set_stroke_method.bl_idname,
                text=label,
                depress=(current == method),
            )
            op.method = method


# ==========================================================
# Keymap
# ==========================================================

_addon_keymaps: list = []


def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new(
        'wm.call_menu_pie', type='M', value='PRESS', ctrl=True, alt=True,
    )
    kmi.properties.name = BRUSH_MT_stroke_method_pie.__name__
    _addon_keymaps.append((km, kmi))


def unregister_keymaps():
    for km, kmi in _addon_keymaps:
        km.keymap_items.remove(kmi)
    _addon_keymaps.clear()


# ==========================================================
# Registration
# ==========================================================

classes = (
    BrushCreatorProperties,
    BRUSHES_OT_import_from_folders,
    BRUSH_OT_set_stroke_method,
    BRUSH_OT_cycle_stroke_method,
    BRUSH_MT_stroke_method_pie,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.brush_creator_props = PointerProperty(type=BrushCreatorProperties)
    register_keymaps()


def unregister():
    unregister_keymaps()
    del bpy.types.Scene.brush_creator_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()