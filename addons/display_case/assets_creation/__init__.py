import bpy
import os
import pathlib
from bpy.props import BoolProperty, StringProperty, PointerProperty

ALLOWED_PREVIEW_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tga', 'webp'}

MODEL_EXTENSIONS = {
    '.obj', '.fbx', '.glb', '.gltf', '.stl', '.dae',
    '.abc', '.usd', '.usda', '.usdc', '.usdz',
}


# ==========================================================
# Properties
# ==========================================================

class AssetCreatorProperties(bpy.types.PropertyGroup):
    models_dir: StringProperty(
        name="Models Folder",
        subtype='DIR_PATH',
        description="Folder containing model files to import as assets"
    )  # type: ignore
    previews_dir: StringProperty(
        name="Previews Folder",
        subtype='DIR_PATH',
        description="Folder with preview images matched by filename stem (optional)"
    )  # type: ignore
    use_collection: BoolProperty(
        name="One Collection per Asset",
        description="Wrap all objects from each file into a named collection and mark that collection as the asset",
        default=True,
    )  # type: ignore
    author_name: StringProperty(name="Author")  # type: ignore
    description: StringProperty(name="Description")  # type: ignore
    tags: StringProperty(
        name="Tags",
        description="Comma-separated tags to apply to each asset"
    )  # type: ignore
    remove_existing_tags: BoolProperty(
        name="Clear Existing Tags",
        description="Remove all existing tags before adding the new ones",
        default=False,
    )  # type: ignore
    use_name_prepost: BoolProperty(
        name="Use Prefix / Suffix",
        default=False,
        description="Prepend/append strings to generated asset names"
    )  # type: ignore
    name_pre: StringProperty(name="Prefix", description="Prepend to asset names")  # type: ignore
    name_post: StringProperty(name="Suffix", description="Append to asset names")  # type: ignore


# ==========================================================
# Helpers
# ==========================================================

def _import_file(filepath):
    """Import a model file and return the set of newly created objects."""
    ext = pathlib.Path(filepath).suffix.lower()
    before = set(bpy.data.objects)

    try:
        if ext == '.obj':
            try:
                bpy.ops.wm.obj_import(filepath=filepath)
            except AttributeError:
                bpy.ops.import_scene.obj(filepath=filepath)
        elif ext == '.fbx':
            bpy.ops.import_scene.fbx(filepath=filepath)
        elif ext in {'.glb', '.gltf'}:
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext == '.stl':
            try:
                bpy.ops.wm.stl_import(filepath=filepath)
            except AttributeError:
                bpy.ops.import_mesh.stl(filepath=filepath)
        elif ext == '.dae':
            bpy.ops.wm.collada_import(filepath=filepath)
        elif ext == '.abc':
            bpy.ops.wm.alembic_import(filepath=filepath)
        elif ext in {'.usd', '.usda', '.usdc', '.usdz'}:
            bpy.ops.wm.usd_import(filepath=filepath)
        else:
            return set()
    except Exception as e:
        print(f"[assets_creation] Import failed for {filepath}: {e}")
        return set()

    return set(bpy.data.objects) - before


def _find_preview(stem, previews_dir):
    """Return path of a preview image matching the given stem, or None."""
    if not previews_dir or not os.path.isdir(previews_dir):
        return None
    for ext in ALLOWED_PREVIEW_EXTENSIONS:
        candidate = os.path.join(previews_dir, f"{stem}.{ext}")
        if os.path.exists(candidate):
            return candidate
    return None


def _apply_preview(id_block, preview_path):
    """Load a preview image for a Blender ID (object or collection)."""
    if not preview_path or not os.path.exists(preview_path):
        return
    try:
        with bpy.context.temp_override(id=id_block):
            bpy.ops.ed.lib_id_load_custom_preview(filepath=preview_path)
    except Exception as e:
        print(f"[assets_creation] Preview warning for {id_block.name}: {e}")


def _apply_metadata(asset_data, props):
    """Write author, description, and tags to an asset_data block."""
    if props.author_name:
        asset_data.author = props.author_name
    if props.description:
        asset_data.description = props.description
    if props.remove_existing_tags:
        while asset_data.tags:
            asset_data.tags.remove(asset_data.tags[0])
    for tag in props.tags.split(','):
        tag = tag.strip()
        if tag:
            asset_data.tags.new(name=tag)


# ==========================================================
# Operator
# ==========================================================

class ASSETS_OT_import_from_folder(bpy.types.Operator):
    bl_idname = "assets.import_from_folder"
    bl_label = "Import Assets From Folder"
    bl_description = "Import all model files from the selected folder and mark them as Blender assets"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.asset_creator_props

        models_dir = bpy.path.abspath(props.models_dir) if props.models_dir else None
        previews_dir = bpy.path.abspath(props.previews_dir) if props.previews_dir else None

        if not models_dir or not os.path.isdir(models_dir):
            self.report({'ERROR'}, "Models folder is invalid or not set")
            return {'CANCELLED'}

        files = sorted(
            f for f in os.listdir(models_dir)
            if pathlib.Path(f).suffix.lower() in MODEL_EXTENSIONS
        )

        if not files:
            self.report({'WARNING'}, "No supported model files found in the folder")
            return {'CANCELLED'}

        created = 0
        for filename in files:
            filepath = os.path.join(models_dir, filename)
            stem = pathlib.Path(filename).stem
            base_name = stem
            if props.use_name_prepost:
                base_name = props.name_pre + base_name + props.name_post

            new_objects = _import_file(filepath)
            if not new_objects:
                print(f"[assets_creation] No objects imported from {filename}")
                continue

            preview_path = _find_preview(stem, previews_dir)

            if props.use_collection:
                coll = bpy.data.collections.new(name=base_name)
                context.scene.collection.children.link(coll)
                for obj in new_objects:
                    for parent_coll in list(obj.users_collection):
                        parent_coll.objects.unlink(obj)
                    coll.objects.link(obj)
                coll.asset_mark()
                _apply_metadata(coll.asset_data, props)
                _apply_preview(coll, preview_path)
            else:
                for obj in new_objects:
                    if len(new_objects) == 1:
                        obj.name = base_name
                    obj.asset_mark()
                    _apply_metadata(obj.asset_data, props)
                    _apply_preview(obj, preview_path)

            created += 1

        if created:
            self.report({'INFO'}, f"Created {created} asset(s)")
        else:
            self.report({'WARNING'}, "No assets were created")

        return {'FINISHED'}


# ==========================================================
# Panel draw (called by the main addon panel, not registered directly)
# ==========================================================

def draw_panel(layout, context):
    props = context.scene.asset_creator_props

    box = layout.box()
    box.label(text="Folders", icon='FILE_FOLDER')
    box.prop(props, "models_dir", text="Models")
    box.prop(props, "previews_dir", text="Previews")

    box = layout.box()
    box.label(text="Asset Settings", icon='ASSET_MANAGER')
    box.prop(props, "use_collection")
    box.separator()
    box.prop(props, "author_name")
    box.prop(props, "description")
    box.separator()
    box.label(text="Tags (comma-separated):", icon='INFO')
    box.prop(props, "tags", text="")
    box.prop(props, "remove_existing_tags")

    box = layout.box()
    box.label(text="Naming", icon='SORTALPHA')
    box.prop(props, "use_name_prepost")
    if props.use_name_prepost:
        row = box.row()
        row.prop(props, "name_pre")
        row.prop(props, "name_post")

    layout.operator("assets.import_from_folder", icon='ASSET_MANAGER')


# ==========================================================
# Registration
# ==========================================================

classes = (
    AssetCreatorProperties,
    ASSETS_OT_import_from_folder,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.asset_creator_props = PointerProperty(type=AssetCreatorProperties)


def unregister():
    del bpy.types.Scene.asset_creator_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()