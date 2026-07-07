import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty, FloatProperty,PointerProperty

import os
class AssetSettings(bpy.types.PropertyGroup):
    author_name: bpy.props.StringProperty(name="Author Name") # type: ignore
    tags: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)# type: ignore
    assets_description: bpy.props.StringProperty(name="Description")# type: ignore
    tag_items: bpy.props.StringProperty(name="Tags")# type: ignore
    remove_tags: bpy.props.BoolProperty(name="Remove Existing Tags Before Adding New", default=False)# type: ignore
    object_to_3DCursor: bpy.props.BoolProperty(name="Object to 3D Cursor", default=True)# type: ignore
    hide_non_render_objects_mode_a: bpy.props.BoolProperty(name="Hide non-render objects in the collection",
                                                           default=True)# type: ignore
    # hide_non_render_objects_mode_b: bpy.props.BoolProperty(name="Hide non-render objects in the collection", default=True)
    use_original_resolution: bpy.props.BoolProperty(name="Use original resolution", default=False)# type: ignore
    use_camera_angle_presets: bpy.props.BoolProperty(name="Use camera angle presets", default=True)# type: ignore
    use_studio_presets_to_render_assets: bpy.props.BoolProperty(name="Use studio presets to render assets",
                                                                default=False)# type: ignore
    exclude_camera_light_empty: bpy.props.BoolProperty(name="Exclude camera light empty instance", default=True)# type: ignore
    render_setting_transparent_background: bpy.props.BoolProperty(name="Transparent Background", default=True)# type: ignore


class AssetCreationProperties(bpy.types.PropertyGroup):
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

class ALB_OT_UpdateAssetSettings(bpy.types.Operator):
    bl_idname = "object.update_asset_settings"
    bl_label = "Update Asset Settings"
    bl_description = "Update asset settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = bpy.context.scene.asset_settings

        # if selected any object
        if context.selected_objects:
            for obj in context.selected_objects:

                with bpy.context.temp_override(id=obj):

                    if obj.asset_data is not None:
                        if settings.author_name != "":
                            obj.asset_data.author = settings.author_name

                        if settings.remove_tags:

                            while len(obj.asset_data.tags) > 0:
                                obj.asset_data.tags.remove(obj.asset_data.tags[0])

                        for tag_name in settings.tag_items.split(','):
                            tag_name = tag_name.strip()
                            if tag_name:
                                # TODO: Remove val after testing
                                new_tag = obj.asset_data.tags.new(name=tag_name)
                        if settings.assets_description != "":
                            obj.asset_data.description = settings.assets_description
                    else:
                        print("Active object does not have asset data.")

                base_path = context.scene.alb_base_path
                output_path = os.path.join(base_path, f"{obj.name}.png")
                # if the preview image is exist
                if os.path.exists(output_path):

                    if output_path:
                        with bpy.context.temp_override(id=obj):
                            bpy.ops.ed.lib_id_load_custom_preview(filepath=output_path)

        return {'FINISHED'}

class OBJECT_OT_BrowseFolder(bpy.types.Operator):
    bl_idname = "object.browse_folder"
    bl_label = "Choose Assets Folder"
    directory: bpy.props.StringProperty(
        subtype='DIR_PATH',
    ) # type: ignore

    def execute(self, context):
        if self.directory:
            context.scene.asset_image_output_path = self.directory
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
class OBJECT_OT_Add_Asset_Images(bpy.types.Operator):
    bl_idname = "object.add_asset_images"
    bl_label = "Assigns pre-built asset renders to assets"

    # file_suffix: bpy.props.StringProperty(name="suffix", default=".png")
    # filter_glob: bpy.props.StringProperty(
    #     default="*.txt",
    #     options={'HIDDEN'},
    #     maxlen=255,  # Max internal buffer length, longer would be clamped.
    # )

    def execute(self, context):
        # bpy.ops.asset.mark()
        prefix = bpy.context.scene.asset_images_prefix
        suffix = bpy.context.scene.asset_images_suffix

        assets_dir = bpy.types.Scene.asset_preview_path
        all_images = os.listdir(assets_dir)
        print(f"images_amount: {len(all_images)}")
        image_extensions = [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".tga", ".exr", ".dds", ".webp"]

        for obj in get_selected_meshes():
            pattern = re.compile(re.escape(prefix + obj.name + suffix) + r"\\.(png|jpg|jpeg|tiff|bmp|tga|exr|dds|webp)$", re.IGNORECASE)

        #      preview_path = os.path.join(assets_dir, obj.name + ".png")  # Adjust extension if needed
        #     obj.asset_mark()
        #     preview_path = os.path.join(assets_dir, obj.name + ".png")  # Adjust extension if needed
        #     if os.path.exists(preview_path):
        #         obj.asset_data.preview_icon_file_path = preview_path
        #     else:
        #         self.report({'WARNING'}, f"Preview not found for {obj.name}")
        return {'FINISHED'}

    # TODO: Add folder path == true
    # def invoke(self, context, event):
    #     context.window_manager.fileselect_add(self)
    #     return {'RUNNING_MODAL'}

def get_selected_objects_of_type(*mesh_types):
    if len(mesh_types) == 0:
        return [obj for obj in bpy.context.selected_objects]
    else:
        return [obj for obj in bpy.context.selected_objects if obj.type in mesh_types]


def get_selected_meshes():
    return get_selected_objects_of_type('MESH')

classes = (
    AssetSettings,
    AssetCreationProperties,
    ALB_OT_UpdateAssetSettings,
    OBJECT_OT_BrowseFolder,
    OBJECT_OT_Add_Asset_Images
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.asset_image_output_path = bpy.props.StringProperty(
        name="Base Path",
        description="Path to save rendered previews",
    )
    bpy.types.Scene.asset_settings = bpy.props.PointerProperty(type=AssetSettings)
    bpy.types.Scene.brush_creator_props = PointerProperty(type=AssetCreationProperties)
    bpy.types.Scene.show_assets_settings_ui = bpy.props.BoolProperty(
        name="Show Assets Settings",
        description="Show or hide assets settings",
        default=True,
    )

def unregister():
    del bpy.types.Scene.show_assets_settings_ui
    del bpy.types.Scene.brush_creator_props
    del bpy.types.Scene.asset_settings
    del bpy.types.Scene.asset_image_output_path
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()