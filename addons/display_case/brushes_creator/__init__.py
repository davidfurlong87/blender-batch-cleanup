import bpy
from bpy.props import BoolProperty, StringProperty, FloatProperty, EnumProperty, PointerProperty
import pathlib
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tga', 'webp', 'hdr'}

# ==========================================================
# Properties
# ==========================================================

class BrushCreatorProperties(bpy.types.PropertyGroup):
    textures_dir: StringProperty(
        name="Images Folder",
        subtype='DIR_PATH',
        description="Folder containing texture image files to import as brushes"
    )
    thumbs_dir: StringProperty(
        name="Thumbnails Folder",
        subtype='DIR_PATH',
        description="Folder with preview images matched by filename stem (optional)"
    )
    use_name_prepost: BoolProperty(
        name="Use Prefix / Suffix",
        default=False,
        description="Prepend/append strings to generated brush names"
    )
    name_pre: StringProperty(name="Prefix", description="Prepend to brush names")
    name_post: StringProperty(name="Suffix", description="Append to brush names")
    brush_type: EnumProperty(
        name="Brush Type",
        items=[
            ('TEXTURE_PAINT', "Texture Paint", "Create texture paint brushes"),
            ('SCULPT', "Sculpt", "Create sculpt brushes"),
            ('BOTH', "Both", "Create both brush types"),
        ],
        default='BOTH'
    )
    stroke_type: EnumProperty(
        name="Stroke Type",
        items=[
            ('SPACE', "Space", "Use Space stroke method"),
            ('ANCHORED', "Anchored", "Use Anchored stroke method"),
            ('BOTH', "Both", "Create one brush per stroke method"),
        ],
        default='SPACE'
    )
    tp_strength: FloatProperty(name="Paint Strength", default=1.0, min=0.0, max=2.0)
    sculpt_strength: FloatProperty(name="Sculpt Strength", default=0.5, min=0.0, max=2.0)
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
    )
    # Internal texture settings (not exposed in panel)
    img_use_existing: BoolProperty(default=True)
    texture_calculate_alpha: BoolProperty(default=True)
    texture_fake_user: BoolProperty(default=True)
    texture_interpolation: BoolProperty(default=True)


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

        created = sum(
            1 for f in files
            if self._create_brush_from_file(os.path.join(tex_dir, f), thumb_dir, props)
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
            if hasattr(brush, 'use_custom_icon'):
                brush.use_custom_icon = True
                brush.icon_filepath = thumb_path
        except Exception as e:
            print(f"Preview warning for {brush.name}: {e}")

    def _new_brush(self, name, mode, texture, strength, stroke, thumb_path, map_mode='RANDOM'):
        brush = bpy.data.brushes.new(name=self._unique_brush_name(name), mode=mode)
        brush.texture = texture
        brush.strength = strength
        if stroke and hasattr(brush, 'stroke_method'):
            brush.stroke_method = stroke
        if brush.texture_slot:
            brush.texture_slot.map_mode = map_mode
        self._apply_preview(brush, thumb_path)
        return brush

    def _create_brush_from_file(self, filepath, thumb_dir, props):
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

            if props.brush_type in {'TEXTURE_PAINT', 'BOTH'}:
                for stroke, suffix in strokes:
                    self._new_brush(base_name + suffix, 'TEXTURE_PAINT', texture, props.tp_strength, stroke, thumb, props.texture_map_mode)

            if props.brush_type in {'SCULPT', 'BOTH'}:
                for stroke, suffix in strokes:
                    self._new_brush(base_name + suffix, 'SCULPT', texture, props.sculpt_strength, stroke, thumb, props.texture_map_mode)

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
    box.separator()
    box.prop(props, "texture_map_mode")

    box = layout.box()
    box.label(text="Naming", icon='SORTALPHA')
    box.prop(props, "use_name_prepost")
    if props.use_name_prepost:
        row = box.row()
        row.prop(props, "name_pre")
        row.prop(props, "name_post")

    layout.operator("brushes.import_from_folders", icon='BRUSHES_ALL')


# ==========================================================
# Registration
# ==========================================================

classes = (
    BrushCreatorProperties,
    BRUSHES_OT_import_from_folders,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.brush_creator_props = PointerProperty(type=BrushCreatorProperties)


def unregister():
    del bpy.types.Scene.brush_creator_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()