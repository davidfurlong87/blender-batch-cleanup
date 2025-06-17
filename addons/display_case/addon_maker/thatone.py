import bpy
import os

from bpy.props import EnumProperty
from mathutils import Matrix, Vector, Quaternion

bl_info = {
    "name": "Assets Library Builder",
    "author": "SHEEP",
    "version": (2, 0, 5),
    "blender": (3, 4, 0),
    "location": "Asset Browser > Sidebar > Assets Builder Panel",
    "description": "Helps to build assets library with custom settings",
    "warning": "",
    "wiki_url": "",
    "category": "Assets Library",
}

# get addon version from bl_info and add to properties
alb_addon_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"


class ALB_OT_test_print(bpy.types.Operator):
    bl_idname = "alb.test_print"
    bl_label = "Test Print"
    bl_description = "Test Print"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("Test Print")
        return {'FINISHED'}


# icon import

import bpy
import os
from bpy.utils import previews


def load_icons(directory):
    icons = previews.new()
    icon_names = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg')):
            icon_name = os.path.splitext(filename)[0]
            icon_path = os.path.join(directory, filename)

            icons.load(icon_name, icon_path, 'IMAGE')
            icon_names.append(icon_name)

    log_file_path = os.path.join(directory, 'icon_list.txt')
    with open(log_file_path, 'w') as file:
        for name in icon_names:
            file.write(name + '\n')
    return icons


# using relative path to get the full path of assets directory
current_file_path = os.path.dirname(__file__)
assets_directory = os.path.join(current_file_path, 'img', 'camera_presets_img')

# load icons
camera_presets_img_icons = load_icons(assets_directory)


# icon import Studio_Preset_Library
# load studio_presets_library icons
def load_icons_2(directory):
    icons = previews.new()
    icon_names = []

    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg')):
            # get filename without extension
            icon_name = os.path.splitext(filename)[0]
            icon_path = os.path.join(directory, filename)
            # load image as icon
            icons.load(icon_name, icon_path, 'IMAGE')
            icon_names.append(icon_name)  # add icon name to list

    log_file_path = os.path.join(directory, 'icon_list.txt')
    with open(log_file_path, 'w') as file:
        for name in icon_names:
            file.write(name + '\n')
    return icons


# using relative path to get the full path of assets directory
studio_presets_current_file_path = os.path.dirname(__file__)
studio_presets_assets_directory = os.path.join(studio_presets_current_file_path, 'img', 'studio_presets_library')

# load icons
studio_presets_img_icons = load_icons_2(studio_presets_assets_directory)


# studio_presets_library enum property
class ALB_studio_presets_item(bpy.types.EnumProperty):
    name = "Studio Presets"
    description = "Set the studio presets"
    items = [
        ("0", "Studio_Preset_001", "", studio_presets_img_icons["Studio_Preset_001"].icon_id, 0),
        ("1", "Studio_Preset_002", "", studio_presets_img_icons["Studio_Preset_002"].icon_id, 1),
        ("2", "Studio_Preset_003", "", studio_presets_img_icons["Studio_Preset_003"].icon_id, 2),
        ("3", "Studio_Preset_004", "", studio_presets_img_icons["Studio_Preset_004"].icon_id, 3),
        ("4", "Studio_Preset_005", "", studio_presets_img_icons["Studio_Preset_005"].icon_id, 4),
        ("5", "Studio_Preset_006", "", studio_presets_img_icons["Studio_Preset_006"].icon_id, 5),
        ("6", "Studio_Preset_007", "", studio_presets_img_icons["Studio_Preset_007"].icon_id, 6),
        ("7", "Studio_Preset_008", "", studio_presets_img_icons["Studio_Preset_008"].icon_id, 7),
    ]


bpy.types.Scene.alb_studio_presets_item = bpy.props.EnumProperty(
    name="Studio Presets",
    description="Set the studio presets",
    items=ALB_studio_presets_item.items,
    default="0",
)


# Function to unlink collections with a specific prefix from a given collection
def unlink_collections_with_prefix(collection, prefix, excluded_name):
    # Create a copy of the collection children list to avoid changing the list during iteration
    children = collection.children[:]
    for child in children:
        # Unlink child collections that have the prefix and are not the excluded collection
        if child.name.startswith(prefix) and child.name != excluded_name:
            collection.children.unlink(child)
            print(f"Unlinked collection '{child.name}' from '{collection.name}'")


def alb_studio_presets_import_preset(context, presets_name):
    # Step 1: Check if "ALB_Studio_Presets" collection exists, if not create it
    if "ALB_Studio_Presets" not in bpy.data.collections:
        alb_studio_presets_collection = bpy.data.collections.new("ALB_Studio_Presets")
        bpy.context.scene.collection.children.link(alb_studio_presets_collection)
        alb_studio_presets_collection.color_tag = 'COLOR_07'
        print("ALB_Studio_Presets collection is created")
    else:
        alb_studio_presets_collection = bpy.data.collections["ALB_Studio_Presets"]
        print("ALB_Studio_Presets collection already exists")

    # Step 2: Import preset from .blend file
    alb_studio_presets_lib_directory = os.path.join(current_file_path, 'studio_presets_library')
    studio_presets_library = os.path.join(alb_studio_presets_lib_directory, 'studio_presets_library.blend')
    bpy.ops.wm.append(
        filepath=os.path.join(studio_presets_library, "Collection", presets_name),
        directory=os.path.join(studio_presets_library, "Collection"),
        filename=presets_name
    )
    print(f"{presets_name} is imported")

    # Step 3: Move the imported collection to "ALB_Studio_Presets" collection
    imported_collection = bpy.data.collections[presets_name]

    # 寻找导入的集合的父集合
    parent_collection = None
    for collection in bpy.data.collections:
        if imported_collection.name in collection.children:
            parent_collection = collection
            break

    # unlink the imported collection from its parent collection
    if parent_collection:
        parent_collection.children.unlink(imported_collection)
    else:
        print(f"Could not find parent collection for {presets_name}")

    alb_studio_presets_collection.children.link(imported_collection)

    print(f"{presets_name} is moved to ALB_Studio_Presets collection")

    # Step 4: Select the objects in the imported collection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_collection.objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj  # Set one object active for translation

    # Step 5: Invoke the move operation
    bpy.ops.transform.translate('INVOKE_DEFAULT')

    # 如果功能有問題 可以考慮移除以下代碼
    # Define the name of the collection that should not be unlinked
    excluded_collection_name = "ALB_Studio_Presets"
    # Define the prefix to search for in the collection names
    prefix_to_unlink = "Studio_Preset_"
    # Get the master collection
    master_collection = bpy.context.scene.collection
    # Run the unlink function on the master collection
    unlink_collections_with_prefix(master_collection, prefix_to_unlink, excluded_collection_name)


class ALB_OT_studio_presets_import_preset(bpy.types.Operator):
    bl_idname = "alb.studio_presets_import_preset"
    bl_label = "Import Preset"
    bl_description = "Import the selected studio presets"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        preset_identifier = context.scene.alb_studio_presets_item
        preset_info = context.scene.bl_rna.properties['alb_studio_presets_item'].enum_items[preset_identifier]
        preset_name = preset_info.name

        if preset_name in bpy.data.collections:
            message = f"{preset_name} is already exist"
            context.window_manager['studio_preset_message'] = message
            bpy.context.window_manager.popup_menu(studio_preset_exists, title="Assets Library Builder", icon='INFO')
            del context.window_manager['studio_preset_message']
        else:
            alb_studio_presets_import_preset(context, preset_name)
            # message = f"{preset_name} is not exist"
            # context.window_manager['studio_preset_message'] = message
            # bpy.context.window_manager.popup_menu(studio_preset_exists, title="Assets Library Builder", icon='INFO')
            # del context.window_manager['studio_preset_message']

        return {'FINISHED'}


def studio_preset_exists(self, context):
    message = context.window_manager.get('studio_preset_message', 'No message set')
    self.layout.label(text=message)


# render studio presets

def alb_studio_presets_set_3d_cursor_location(presets_name, action_type, ori_cursor_location):
    if action_type == 'start':
        # get all empty object
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY':
                if obj.name == presets_name:
                    preset_empty = obj
                    # get preset empty location
                    preset_empty_location = preset_empty.location
                    # set 3D cursor location to preset empty location
                    bpy.context.scene.cursor.location = preset_empty_location

    if action_type == 'end':
        if ori_cursor_location is not None:
            print(ori_cursor_location)
            # restore 3D cursor location to original location
            bpy.context.scene.cursor.location = ori_cursor_location
            print('3D cursor location is restored')
        else:
            print('ERROR : ori_cursor_location is None')


class ALB_OT_render_studio_presets(bpy.types.Operator):
    bl_idname = "alb.render_studio_presets"
    bl_label = "Studio Presets"
    bl_description = "Set the studio presets"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        preset_identifier = context.scene.alb_studio_presets_item
        preset_info = context.scene.bl_rna.properties['alb_studio_presets_item'].enum_items[preset_identifier]
        preset_name = preset_info.name

        base_path = context.scene.alb_base_path
        if not base_path:
            self.report({'ERROR'}, "Please set a valid path.")
            return {'CANCELLED'}
        # check if the preset collection is exist
        if preset_name in bpy.data.collections:

            # get original 3D cursor location
            ori_cursor_location = bpy.context.scene.cursor.location.copy()
            alb_studio_presets_set_3d_cursor_location(preset_name, 'start', None)
            # run alb.main_operator
            bpy.ops.alb.main_operator()
            # restore 3D cursor location to original location
            alb_studio_presets_set_3d_cursor_location(preset_name, 'end', ori_cursor_location)

        else:
            message = f"{preset_name} is not exist"
            context.window_manager['studio_preset_message'] = message
            bpy.context.window_manager.popup_menu(studio_preset_exists, title="Assets Library Builder", icon='INFO')
            del context.window_manager['studio_preset_message']

            # alb_studio_presets_import_preset(context, preset_name)

        return {'FINISHED'}


# reload all custom icons

class ALB_OT_reload_icons(bpy.types.Operator):
    bl_idname = "alb.reload_icons"
    bl_label = "Reload Icons"
    bl_description = "Reload all custom icons"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global camera_presets_img_icons
        global studio_presets_img_icons
        # using relative path to get the full path of assets directory
        current_file_path = os.path.dirname(__file__)
        assets_directory = os.path.join(current_file_path, 'img', 'camera_presets_img')
        # load icons
        camera_presets_img_icons = load_icons(assets_directory)

        # using relative path to get the full path of assets directory
        studio_presets_current_file_path = os.path.dirname(__file__)
        studio_presets_assets_directory = os.path.join(studio_presets_current_file_path, 'img',
                                                       'studio_presets_library')
        # load icons
        studio_presets_img_icons = load_icons_2(studio_presets_assets_directory)

        return {'FINISHED'}


# rename tool start
class NumberTypePropertyGroup(bpy.types.PropertyGroup):
    number_type: bpy.props.EnumProperty(
        name="Number Type",
        items=[
            ("1,2...", "1,2,3...", ""),
            ("01,02...", "01,02,03...", ""),
            ("001,002...", "001,002,003...", "")
        ],
        default="1,2..."
    )


class RenameObjectOperator(bpy.types.Operator):
    bl_idname = "object.rename_object"
    bl_label = "Rename Object"
    # undo
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        number_type = context.scene.number_type_properties.number_type
        selected_object = context.active_object
        obj_name = context.scene.obj_name

        if selected_object is not None:
            for i, obj in enumerate(context.selected_objects, start=context.scene.start_number):
                # based on the number type, format the number
                if number_type == "1,2...":
                    formatted_number = str(i)
                elif number_type == "01,02...":
                    formatted_number = f"{i:02d}"
                elif number_type == "001,002...":
                    formatted_number = f"{i:03d}"

                    # 使用格式化后的编号重命名对象
                obj.name = obj_name + formatted_number
                obj.data.name = obj_name + formatted_number

        return {'FINISHED'}


# rename tool end


class ALB_OT_PreviousItem(bpy.types.Operator):
    bl_idname = "alb.previous_item"
    bl_label = "Previous Item"

    def execute(self, context):
        max_index = len(context.scene.bl_rna.properties["camera_angle"].enum_items) - 1
        current_index = int(context.scene.camera_angle)
        # 如果当前是第一个元素，跳到最后一个；否则，索引减1
        new_index = max_index if current_index == 0 else current_index - 1
        context.scene.camera_angle = str(new_index)
        return {'FINISHED'}


class ALB_OT_NextItem(bpy.types.Operator):
    bl_idname = "alb.next_item"
    bl_label = "Next Item"

    def execute(self, context):
        max_index = len(context.scene.bl_rna.properties["camera_angle"].enum_items) - 1
        current_index = int(context.scene.camera_angle)
        # 如果当前是最后一个元素，跳到第一个；否则，索引加1
        new_index = 0 if current_index == max_index else current_index + 1
        context.scene.camera_angle = str(new_index)
        return {'FINISHED'}


class ALB_OT_PreviousItem_studio_preset_library(bpy.types.Operator):
    bl_idname = "alb.previous_item_studio_preset_library"
    bl_label = "Previous Item"

    def execute(self, context):
        max_index = len(context.scene.bl_rna.properties["alb_studio_presets_item"].enum_items) - 1
        current_index = int(context.scene.alb_studio_presets_item)
        new_index = max_index if current_index == 0 else current_index - 1
        context.scene.alb_studio_presets_item = str(new_index)
        return {'FINISHED'}


class ALB_OT_NextItem_studio_preset_library(bpy.types.Operator):
    bl_idname = "alb.next_item_studio_preset_library"
    bl_label = "Next Item"

    def execute(self, context):
        max_index = len(context.scene.bl_rna.properties["alb_studio_presets_item"].enum_items) - 1
        current_index = int(context.scene.alb_studio_presets_item)
        new_index = 0 if current_index == max_index else current_index + 1
        context.scene.alb_studio_presets_item = str(new_index)
        return {'FINISHED'}


# define

author_name = ""
tag_items = []
remove_tags = False
assets_description = ""
object_to_3DCursor = False
hide_non_render_objects_mode_a = False
use_original_resolution = False


class ALB_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__  # 確保這裡使用的是你的插件模塊名

    # 添加一個布林型屬性來保存設置
    preference_panel_setting_show_assets_browser_ui: bpy.props.BoolProperty(
        name="Show Assets Browser UI",
        default=True,
        description="Enable or disable the Assets Browser UI."
    )

    # 繪製偏好設置的UI
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preference_panel_setting_show_assets_browser_ui")


class ALBSettings(bpy.types.PropertyGroup):
    author_name: bpy.props.StringProperty(name="Author Name")
    tags: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    assets_description: bpy.props.StringProperty(name="Description")
    tag_items: bpy.props.StringProperty(name="Tags")
    remove_tags: bpy.props.BoolProperty(name="Remove Existing Tags Before Adding New", default=False)
    object_to_3DCursor: bpy.props.BoolProperty(name="Object to 3D Cursor", default=True)
    hide_non_render_objects_mode_a: bpy.props.BoolProperty(name="Hide non-render objects in the collection",
                                                           default=True)
    # hide_non_render_objects_mode_b: bpy.props.BoolProperty(name="Hide non-render objects in the collection", default=True)
    use_original_resolution: bpy.props.BoolProperty(name="Use original resolution", default=False)
    use_camera_angle_presets: bpy.props.BoolProperty(name="Use camera angle presets", default=True)
    use_studio_presets_to_render_assets: bpy.props.BoolProperty(name="Use studio presets to render assets",
                                                                default=False)
    exclude_camera_light_empty: bpy.props.BoolProperty(name="Exclude camera light empty instance", default=True)
    render_setting_transparent_background: bpy.props.BoolProperty(name="Transparent Background", default=True)


# Render resolution enum Default 128
class RenderResolutionEnum(bpy.types.EnumProperty):
    name = "Render Resolution"
    description = "Select the render resolution"
    items = [
        ("64", "x64", "64"),
        ("128", "x128", "128"),
        ("256", "x256", "256"),
        ("512", "x512", "512"),
        ("1024", "x1024", "1024"),
        ("2048", "x2048", "2048"),
        ("4096", "x4096", "4096"),
    ]


bpy.types.Scene.render_resolution = bpy.props.EnumProperty(
    name="Render Resolution",
    description="Select the render resolution",
    items=RenderResolutionEnum.items,
    default="128",
)


# Operator for adding tags
class ASSET_OT_CustomTagAdd(bpy.types.Operator):
    bl_idname = "asset.custom_tag_add"
    bl_label = "Add Custom Tags"

    def execute(self, context):
        settings = context.scene.alb_settings
        active_object = context.active_object

        if settings.remove_tags:
            active_object.asset_data.tags.clear()

        for tag_name in settings.tag_items.split(','):
            tag_name = tag_name.strip()
            if tag_name:
                new_tag = active_object.asset_data.tags.new(name=tag_name)
                item = settings.tags.add()
                item.name = tag_name

        return {'FINISHED'}


# Operator for removing tags
class ASSET_OT_CustomTagRemove(bpy.types.Operator):
    bl_idname = "asset.custom_tag_remove"
    bl_label = "Remove Custom Tags"

    def execute(self, context):
        settings = context.scene.alb_settings
        active_object = context.active_object

        for tag in settings.tags:
            for asset_tag in active_object.asset_data.tags:
                if asset_tag.name == tag.name:
                    active_object.asset_data.tags.remove(asset_tag)
                    break

        settings.tags.clear()

        return {'FINISHED'}


alb_auto_lock_camera_to_object = "alb_auto_lock_camera_to_object"


# hide_non_render_objects_name = "alb_hide_non_render_objects"


# define the camera angle enum property
class ALB_camera_angle_enum(bpy.types.EnumProperty):
    name = "Camera Angle"
    description = "Set the camera angle"
    items = [
        ("0", "Preset 0", "", camera_presets_img_icons["0"].icon_id, 0),
        ("1", "Preset 1", "", camera_presets_img_icons["1"].icon_id, 1),
        ("2", "Preset 2", "", camera_presets_img_icons["2"].icon_id, 2),
        ("3", "Preset 3", "", camera_presets_img_icons["3"].icon_id, 3),
        ("4", "Preset 4", "", camera_presets_img_icons["4"].icon_id, 4),
        ("5", "Preset 5", "", camera_presets_img_icons["5"].icon_id, 5),
        ("6", "Preset 6", "", camera_presets_img_icons["6"].icon_id, 6),
        ("7", "Preset 7", "", camera_presets_img_icons["7"].icon_id, 7),
        ("8", "Preset 8", "", camera_presets_img_icons["8"].icon_id, 8),
    ]


bpy.types.Scene.camera_angle = bpy.props.EnumProperty(
    name="Camera Angle",
    description="Set the camera angle",
    items=ALB_camera_angle_enum.items,
    default="5",
)


# find actived camera is the scene
def alb_camera_find_active():
    for obj in bpy.context.scene.objects:
        if bpy.context.scene.camera:
            if obj.type == 'CAMERA':
                if obj.data.name == bpy.context.scene.camera.data.name:
                    return obj
    # print("No active camera found")
    return None


def alb_camera_angle_set(camera_object, x_value, y_value, z_value):
    if camera_object:
        camera_object.rotation_euler[0] = 1.5708 * x_value
        camera_object.rotation_euler[1] = 1.5708 * y_value
        camera_object.rotation_euler[2] = 1.5708 * z_value


class ALB_OT_camera_angle_setup(bpy.types.Operator):
    bl_idname = "alb.camera_angle_setup"
    bl_label = "Camera Angle Setup"
    bl_description = "Set the camera angle"

    def execute(self, context):
        camera_object = alb_camera_find_active()
        if camera_object:

            if context.scene.camera_angle == "0":
                alb_camera_angle_set(camera_object, 1, 0, 0.25)
            elif context.scene.camera_angle == "1":
                alb_camera_angle_set(camera_object, 1, 0, 0)
            elif context.scene.camera_angle == "2":
                alb_camera_angle_set(camera_object, 1, 0, -0.25)
            elif context.scene.camera_angle == "3":
                alb_camera_angle_set(camera_object, 0.75, 0, 0.25)
            elif context.scene.camera_angle == "4":
                alb_camera_angle_set(camera_object, 0.75, 0, 0)
            elif context.scene.camera_angle == "5":
                alb_camera_angle_set(camera_object, 0.75, 0, -0.25)
            elif context.scene.camera_angle == "6":
                alb_camera_angle_set(camera_object, 1.25, 0, 0.25)
            elif context.scene.camera_angle == "7":
                alb_camera_angle_set(camera_object, 1.25, 0, 0)
            elif context.scene.camera_angle == "8":
                alb_camera_angle_set(camera_object, 1.25, 0, -0.25)
            else:
                print("No camera angle found")

        return {'FINISHED'}


global_alb_view_context = None


class ALB_OT_RecordView(bpy.types.Operator):
    bl_idname = "alb.record_view"
    bl_label = "Record 3D View"

    def execute(self, context):
        global global_alb_view_context
        global_alb_view_context = record_view3d_context()
        self.report({'INFO'}, "View recorded.")
        return {'FINISHED'}


class ALB_OT_RestoreView(bpy.types.Operator):
    bl_idname = "alb.restore_view"
    bl_label = "Restore 3D View"

    def execute(self, context):
        if global_alb_view_context:
            restore_view3d_context(global_alb_view_context)
            self.report({'INFO'}, "View restored.")
        else:
            self.report({'WARNING'}, "No view to restore.")
        return {'FINISHED'}


def record_view3d_context():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            rv3d = area.spaces.active.region_3d
            view_context = {
                "view_location": rv3d.view_location.copy(),
                "view_rotation": rv3d.view_rotation.copy(),
                "view_distance": rv3d.view_distance
            }
            return view_context
    return None


def restore_view3d_context(view_context):
    if not view_context:
        return
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            rv3d = area.spaces.active.region_3d
            rv3d.view_location = view_context["view_location"]
            rv3d.view_rotation = view_context["view_rotation"]
            rv3d.view_distance = view_context["view_distance"]
            break


# class VIEW3D_PT_CustomPanel(bpy.types.Panel):
#     bl_label = "View3D Snapshot"
#     bl_idname = "VIEW3D_PT_custom_panel"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = 'View3D Snapshot'

#     def draw(self, context):
#         layout = self.layout
#         layout.operator("alb.record_view")
#         layout.operator("alb.restore_view")

class ALB_OT_origin_to_bottom(bpy.types.Operator):
    bl_idname = "alb.origin_to_bottom"
    bl_label = "Set Origin to Bottom"
    bl_description = "Set origin of the selected meshes to the bottom"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # if edit mode, exit edit mode

        for o in context.selected_objects:
            if o.type == 'MESH':

                if bpy.context.mode == 'EDIT_MESH':
                    bpy.ops.object.mode_set(mode='OBJECT')
                    self.origin_to_bottom(o)
                    bpy.ops.object.mode_set(mode='EDIT')
                    break
                # set origin to bottom
                self.origin_to_bottom(o)

        return {'FINISHED'}

    def origin_to_bottom(self, ob, matrix=Matrix()):
        me = ob.data
        mw = ob.matrix_world
        local_verts = [matrix @ Vector(v[:]) for v in ob.bound_box]
        o = sum(local_verts, Vector()) / 8
        o.z = min(v.z for v in local_verts)
        o = matrix.inverted() @ o
        me.transform(Matrix.Translation(-o))
        mw.translation = mw @ o


class ALB_OT_ToggleAutoLockCamera(bpy.types.Operator):
    bl_idname = "alb.toggle_auto_lock_camera"
    bl_label = "Toggle Auto Lock Camera to Object"

    def execute(self, context):
        current_value = get_or_create_global_variable(alb_auto_lock_camera_to_object, False)
        new_value = not current_value
        set_global_variable(alb_auto_lock_camera_to_object, new_value)

        return {'FINISHED'}


def get_or_create_global_variable(name, default):
    if not hasattr(bpy.types.Scene, name):
        setattr(bpy.types.Scene, name, bpy.props.BoolProperty(name=name, default=default))
    return getattr(bpy.context.scene, name)


def set_global_variable(name, value):
    setattr(bpy.context.scene, name, value)


def save_selected_objects_state(context):
    return context.selected_objects.copy()


def restore_selected_objects_state(context, selected_objects_state):
    for ob in bpy.data.objects:
        ob.select_set(False)
    for obj in selected_objects_state:
        obj.select_set(True)
    context.view_layer.objects.active = selected_objects_state[-1] if selected_objects_state else None


def draw_popup_menu(self, context):
    self.layout.label(text="FINISH")


class ALB_TO_set_camera_to_view(bpy.types.Operator):
    bl_idname = "alb.set_camera_to_view"
    bl_label = "Set Camera to View"
    bl_description = "Set camera to view selected object"

    def execute(self, context):
        # nothing to do
        return {'FINISHED'}

    @staticmethod
    def set_camera_to_view(context, obj, camera_move_distance_z):
        for ob in bpy.data.objects:
            ob.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj

        area = next(area for area in context.screen.areas if area.type == 'VIEW_3D')
        region = area.regions[-1]

        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.view3d.view_selected(use_all_regions=False)
            bpy.ops.view3d.camera_to_view_selected()

            camera = context.scene.camera
            current_location = camera.location

            for ob in bpy.data.objects:
                ob.select_set(False)
            camera.select_set(True)
            context.view_layer.objects.active = camera

            # bpy.ops.transform.translate(value=(0, 0, camera_move_distance_z), orient_type='LOCAL', constraint_axis=(False, False, True))
            camera.location += camera_move_distance_z * camera.matrix_world.to_3x3().transposed()[2]

            for ob in bpy.data.objects:
                ob.select_set(False)
            obj.select_set(True)
            context.view_layer.objects.active = obj


set_camera_to_view = ALB_TO_set_camera_to_view.set_camera_to_view


def mark_and_render_asset(active_object, base_path, selected_objects):
    active_object.asset_mark()
    settings = bpy.context.scene.alb_settings

    hide_non_render_objects = settings.hide_non_render_objects_mode_a

    if hide_non_render_objects:
        collection_objects = selected_objects
        original_visibility = {obj: obj.hide_render for obj in collection_objects}

        for obj in collection_objects:
            obj.hide_render = obj != active_object

    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    bpy.context.scene.render.image_settings.quality = 70
    output_path = os.path.join(base_path, f"{active_object.name}.png")
    bpy.context.scene.render.filepath = output_path

    bpy.ops.render.render(write_still=True)

    with bpy.context.temp_override(id=active_object):
        bpy.ops.ed.lib_id_load_custom_preview(filepath=output_path)

        if active_object.asset_data is not None:
            if settings.author_name != "":
                active_object.asset_data.author = settings.author_name

            if settings.remove_tags:

                while len(active_object.asset_data.tags) > 0:
                    active_object.asset_data.tags.remove(active_object.asset_data.tags[0])

            for tag_name in settings.tag_items.split(','):
                tag_name = tag_name.strip()
                if tag_name:
                    new_tag = active_object.asset_data.tags.new(name=tag_name)
            if settings.assets_description != "":
                active_object.asset_data.description = settings.assets_description
        else:
            print("Active object does not have asset data.")

    if hide_non_render_objects:
        for obj, was_hidden in original_visibility.items():
            obj.hide_render = was_hidden


import bpy
import bmesh
from mathutils import Vector


def create_wire_cube_from_selected_object(obj):
    # 確保有物體被選中
    if bpy.context.selected_objects:
        # 取得當前場景中活躍的物體
        active_object = obj
        # 取得選中物體的邊界框(Bound Box)尺寸
        bbox_corners = [active_object.matrix_world @ Vector(corner) for corner in active_object.bound_box]

        # 創建新的網格和物體
        mesh = bpy.data.meshes.new(name="WireCubeMesh")
        wire_cube_object = bpy.data.objects.new("WireCube", mesh)

        # 將新創建的物體添加到當前場景
        bpy.context.collection.objects.link(wire_cube_object)
        # 確保我們正在操作新創建的網格
        bpy.context.view_layer.objects.active = wire_cube_object
        wire_cube_object.select_set(True)

        # 創建一個新的BMesh，並添加頂點
        bm = bmesh.new()
        for corner in bbox_corners:
            bm.verts.new(corner)

        # 更新BMesh到網格數據塊
        bm.to_mesh(mesh)
        bm.free()

        # 創建邊
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

        for edge in edges:
            mesh.edges.add(1)
            mesh.edges[-1].vertices = edge

        # 更新網格
        mesh.update()
        return wire_cube_object

    else:
        pass


def remove_temp_obj(temp_obj):
    bpy.data.objects.remove(temp_obj, do_unlink=True)


def mark_and_render_assets(base_path, camera_move_distance_z):
    settings = bpy.context.scene.alb_settings
    saved_selection = save_selected_objects_state(bpy.context)
    if not bpy.context.scene.camera:
        raise RuntimeError("No active camera found in the scene.")
    if not any(o for o in bpy.context.scene.objects if o.type == 'CAMERA'):
        raise RuntimeError("No camera found in the scene.")
    selected_objects = bpy.context.selected_objects
    # exclude camera light empty
    if settings.exclude_camera_light_empty:
        selected_objects = [obj for obj in selected_objects if obj.type not in {'CAMERA', 'LIGHT', 'EMPTY'}]

    if not selected_objects:
        print("No object selected")
    current_camera = bpy.context.scene.camera
    current_camera_location = current_camera.location.copy()
    current_camera_rotation = current_camera.rotation_euler.copy()

    auto_lock_camera = getattr(bpy.context.scene, alb_auto_lock_camera_to_object)

    temp_obj_list = []
    if auto_lock_camera:
        # print("OBJECT:", len(selected_objects))

        for obj in selected_objects:

            if settings.object_to_3DCursor:
                # save object location
                ori_location = obj.location.copy()
                # set object location to 3D cursor
                obj.location = bpy.context.scene.cursor.location
                bpy.context.view_layer.update()

            temp_obj = create_wire_cube_from_selected_object(obj)
            temp_obj_list.append(temp_obj)

            set_camera_to_view(bpy.context, temp_obj, camera_move_distance_z)
            mark_and_render_asset(obj, base_path, selected_objects)

            if settings.object_to_3DCursor:
                # restore object location
                obj.location = ori_location
    else:
        for obj in selected_objects:
            if settings.object_to_3DCursor:
                # save object location
                ori_location = obj.location.copy()
                # set object location to 3D cursor
                obj.location = bpy.context.scene.cursor.location
            temp_obj = create_wire_cube_from_selected_object(obj)
            temp_obj_list.append(temp_obj)
            mark_and_render_asset(obj, base_path, selected_objects)
            if settings.object_to_3DCursor:
                # restore object location
                obj.location = ori_location

    bpy.context.scene.camera.location = current_camera_location
    bpy.context.scene.camera.rotation_euler = current_camera_rotation
    restore_selected_objects_state(bpy.context, saved_selection)
    bpy.context.window_manager.popup_menu(draw_popup_menu, title="Assets Library Builder", icon='INFO')

    for temp_obj in temp_obj_list:
        remove_temp_obj(temp_obj)


class VIEW3D_OT_toggle_camera_view(bpy.types.Operator):
    bl_idname = "view3d.toggle_camera_view"
    bl_label = "Toggle Camera View"

    def execute(self, context):

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':

                space_data = area.spaces.active
                rv3d = space_data.region_3d
                if rv3d.view_perspective != 'CAMERA':
                    rv3d.view_perspective = 'CAMERA'
                else:
                    rv3d.view_perspective = 'PERSP'
                break
        return {'FINISHED'}


class ALB_OT_UpdateButDontRender(bpy.types.Operator):
    bl_idname = "alb.update_but_dont_render"
    bl_label = "Update But Don't Render"
    bl_description = "Update but don't render the selected object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = bpy.context.scene.alb_settings

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


# UI
def alb_main_panel_ui(self, context, layout, is3dview):
    scn = context.scene

    # box = layout.box()
    # box.scale_y = 2.5

    # box.operator("alb.main_operator", text="Build Assets Library", icon="ASSET_MANAGER")

    layout = self.layout
    box = layout.box()
    settings = context.scene.alb_settings

    # Author name input
    # box.label(text="Asset Settings",icon='INFO')
    box.prop(scn, "alb_show_assets_info_ui", icon=("INFO" if scn.alb_show_assets_info_ui else "INFO"),
             text="【 Assets Settings 】")
    if scn.alb_show_assets_info_ui:
        box.prop(settings, "author_name")

        box.prop(settings, "assets_description")

        # Tags input (user can input multiple tags separated by commas)
        box.label(text="Separate tags with commas.", icon='INFO')
        box.prop(settings, "tag_items")

        # Remove tags option
        box.prop(settings, "remove_tags")

        box.operator("alb.update_but_dont_render", text="Update But Don't Render", icon="FILE_REFRESH")

    # # Add and remove buttons for tags
    # row = layout.row(align=True)
    # row.operator("asset.custom_tag_add", icon='ADD', text="Add Tags")
    # row.operator("asset.custom_tag_remove", icon='REMOVE', text="Remove Tags")

    # # Display existing tags
    # box = layout.box()
    # box.label(text="Current Tags:")
    # for tag in settings.tags:
    #     box.label(text=tag.name)

    layout = self.layout
    box = layout.box()

    box.label(text="Select a folder to save the preview image", icon='INFO')
    row = box.row(align=True)
    row.prop(scn, "alb_base_path", text="")
    row.operator('alb.browse_folder', text="Select Folder", icon='FILE_FOLDER')

    layout = self.layout
    box = layout.box()

    # alb_show_settings
    # box.label(text="Setting",icon='SETTINGS')
    box.prop(scn, "alb_show_settings", icon=("SETTINGS" if scn.alb_show_settings else "SETTINGS"), text="【 Setting 】")
    if scn.alb_show_settings:

        # Hide non-render objects
        box.prop(settings, "hide_non_render_objects_mode_a", text="Hide other objects in selected objects.")
        box_row = box.row(align=False)
        box_row.prop(settings, "object_to_3DCursor")
        box_row = box.row(align=False)
        box_row.prop(settings, "exclude_camera_light_empty", text="Exclude Camera,Light,Empty,Collection Instance")

        # box.separator()
        box3 = box.box()
        box3.scale_y = 1.25
        row3 = box3.row(align=True)
        row3.label(text="Camera Settings", icon='OUTLINER_OB_CAMERA')
        row3.prop(scn, "show_camera_settings", icon=("TRIA_DOWN" if scn.show_camera_settings else "TRIA_RIGHT"),
                  text="Camera Settings")

        if scn.show_camera_settings:
            alb_camera_angle_panel_ui(self, context, box3)

            auto_lock = get_or_create_global_variable(alb_auto_lock_camera_to_object, False)
            box3.prop(context.scene, alb_auto_lock_camera_to_object, text="Auto Lock Camera to Object")

            auto_lock_camera = getattr(scn, alb_auto_lock_camera_to_object)

            box_row = box3.row(align=True)
            box_row.label(text="", icon='DRIVER_DISTANCE')
            box_row.enabled = auto_lock_camera
            box_row.prop(scn, "alb_camera_move_distance_z", text="Shooting distance (m)", slider=True,
                         icon='DRIVER_DISTANCE')

            box4 = box3.box()

            area = next((area for area in bpy.context.screen.areas if area.type == 'VIEW_3D'), None)
            camera = alb_camera_find_active()

            if camera:
                box4.label(text=camera.name + " Settings", icon='OUTLINER_OB_CAMERA')
                if area:
                    space = area.spaces.active

                    if isinstance(space, bpy.types.SpaceView3D):
                        col = box4.column()
                        col.prop(space, "lock_camera", text="Lock Camera to View (Camera View)")

                # if camera is found
                box4.prop(camera.data, "lens", text="Lens")
                box4.prop(camera.data, "passepartout_alpha", text="Passepartout Alpha")
            else:
                # if no active camera found
                box4.label(text="No active camera found in the scene.", icon='ERROR')

        box.separator()

        box2 = box.box()
        box2.scale_y = 1.25
        row2 = box2.row(align=True)
        row2.label(text="Render Settings", icon='RESTRICT_RENDER_OFF')
        row2.prop(scn, "show_render_settings", icon=("TRIA_DOWN" if scn.show_render_settings else "TRIA_RIGHT"),
                  text="Render Settings")
        if scn.show_render_settings:
            box2.prop(settings, "render_setting_transparent_background", text="Transparent BackGround",
                      icon=("TEXTURE_DATA" if scn.render.film_transparent else "OUTLINER_OB_IMAGE"))

            box2.prop(settings, "use_original_resolution", text="Use custom resolution",
                      icon=("RADIOBUT_ON" if settings.use_original_resolution else "RADIOBUT_OFF"))
            if settings.use_original_resolution:
                box2.prop(scn.render, "resolution_x")
                box2.prop(scn.render, "resolution_y")
            else:
                box2.prop(scn, "render_resolution", text="Render Resolution")

        # row = layout.row()

        box.separator()
        alb_studio_presets_ui(self, context, box, is3dview)


def alb_tool_panel_ui(self, context, layout):
    scn = context.scene
    layout = self.layout
    box = layout.box()
    box.scale_y = 1.4

    row = box.row(align=False)
    row.prop(scn, "alb_show_other_tools", icon=("TOOL_SETTINGS" if scn.alb_show_other_tools else "TOOL_SETTINGS"),
             text="【 Handy Tools 】")

    if scn.alb_show_other_tools:
        row = box.row(align=True)

        sub = row.row()
        sub.scale_x = 0.3  # ajust this value to better control the distance between the buttons and the edges
        sub.label(text="")  # empty label to create a space

        # set origin to bottom
        row.operator("alb.origin_to_bottom", text="Set Origin to Bottom", icon='TRIA_DOWN_BAR')

        sub = row.row()
        sub.scale_x = 0.3  # ajust this value to better control the distance between the buttons and the edges
        sub.label(text="")  # empty label to create a space

        # rename tool
        alb_rename_tool_ui(self, context, box)


def alb_camera_angle_panel_ui(self, context, layout):
    scn = context.scene
    settings = context.scene.alb_settings

    # layout = self.layout
    box = layout.box()
    # box.scale_y = 1.5
    box.label(text="Camera Angle", icon='CAMERA_DATA')
    box.prop(settings, "use_camera_angle_presets",
             icon=("RADIOBUT_ON" if settings.use_camera_angle_presets else "RADIOBUT_OFF"),
             text=("Use Angle Presets Library" if settings.use_camera_angle_presets else "Default Angle"))
    if settings.use_camera_angle_presets:
        row = box.row(align=True)
        row.prop(scn, "camera_angle", text="", )
        row = box.row(align=True)

        # create a child row for 'Previous' button and set appropriate scaling
        sub = row.row(align=True)
        scale_num_a = 6.0
        sub.scale_y = scale_num_a
        sub.operator("alb.previous_item", text="", icon='TRIA_LEFT')

        # use template_icon_view to display the enum icons
        row.scale_y = 1.0
        row.template_icon_view(scn, "camera_angle", scale=scale_num_a, scale_popup=scale_num_a)

        # create another child row for 'Next' button and set appropriate scaling
        sub = row.row(align=True)
        sub.scale_y = scale_num_a
        sub.operator("alb.next_item", text="", icon='TRIA_RIGHT')



    else:
        # display rotation_euler setting ui
        if False:
            row = box.row(align=False)
            row.label(text="Rotation Angle Setting", icon='CAMERA_DATA')
            row = box.row(align=True)
            get_active_camera = alb_camera_find_active()
            if get_active_camera:
                row.prop(get_active_camera, "rotation_euler", text="")


def alb_rename_tool_ui(self, context, layout):
    scn = context.scene
    settings = context.scene.alb_settings

    layout.use_property_split = True
    layout.use_property_decorate = False
    layout = layout.box()
    obj = context.active_object
    # layout.label(text="Rename Tool",icon='FILE_TEXT')
    layout.prop(scn, "alb_show_rename_tool_ui", icon='FILE_TEXT', text="Rename Tools")
    if scn.alb_show_rename_tool_ui:
        if obj is not None:
            layout.prop(context.scene, "obj_name", text="Name:", icon="SYNTAX_OFF")

            layout.prop(context.scene, "start_number", text="Start Number:")
            # number_type
            layout.prop(context.scene.number_type_properties, "number_type", text="Type:", icon="PRESET")
            # set button size
            scale = 1.2
            layout.scale_x = scale
            layout.scale_y = scale

            layout.operator("object.rename_object", text="Rename")
        else:
            layout.label(text="No object selected.")


def alb_build_assets_library_button_ui(self, context, layout):
    camera_object = alb_camera_find_active()

    layout = self.layout
    box = layout.box()
    box.label(text="Build Assets !", icon="PLUS")
    box = box.box()
    if camera_object:
        settings = context.scene.alb_settings

        box.scale_y = 2.0
        box.alert = False
        row = box.row(align=True)

        sub = row.row()
        sub.scale_x = 0.25
        sub.label(text="")
        row.operator("alb.main_operator", text="Default", icon="ASSET_MANAGER")
        if settings.use_studio_presets_to_render_assets:
            # run alb.render_studio_presets
            row.alert = True
            row.operator("alb.render_studio_presets", text="Studio Presets", icon="RENDER_STILL")

        sub = row.row()
        sub.scale_x = 0.25
        sub.label(text="")
    else:
        box.label(text="No active camera found in the scene.", icon='ERROR')


def alb_studio_presets_ui(self, context, layout, is3dview):
    if is3dview:
        row = layout.row(align=True)
        box = row.box()
        settings = context.scene.alb_settings
        scn = context.scene
        box.prop(settings, "use_studio_presets_to_render_assets",
                 icon=("RADIOBUT_ON" if settings.use_studio_presets_to_render_assets else "RADIOBUT_OFF"),
                 text="Use Studio Presets")
        row = box.row(align=True)
        if settings.use_studio_presets_to_render_assets:
            row.label(text="This is beta feature, may have some bugs.", icon='ERROR')
            # row = box.row(align=True)
            # row.label(text="This is beta feature, may have some bugs.",icon='ERROR')
            row = box.row(align=True)
            row.prop(scn, "alb_studio_presets_item", text="", )
            row = box.row(align=True)

            # create a child row for 'Previous' button and set appropriate scaling
            sub = row.row(align=True)
            scale_num_a = 6.0
            sub.scale_y = scale_num_a
            sub.operator("alb.previous_item_studio_preset_library", text="", icon='TRIA_LEFT')

            # use template_icon_view to display the enum icons
            row.scale_y = 1.0
            row.template_icon_view(context.scene, "alb_studio_presets_item", scale=6.0, scale_popup=6.0)

            # create another child row for 'Next' button and set appropriate scaling
            sub = row.row(align=True)
            sub.scale_y = scale_num_a
            sub.operator("alb.next_item_studio_preset_library", text="", icon='TRIA_RIGHT')
            if is3dview:
                box.operator("alb.studio_presets_import_preset", text="Import Studio Presets", icon="IMPORT")
            else:
                # 請至3D View NPanel中使用
                box.label(text="Please use in 3D View NPanel.", icon='ERROR')


def ALB_Documentation_and_Info(self, context, layout):
    layout = self.layout
    box = layout.box()
    # dropdown menu
    row = box.row()
    row.label(text="Documentation and Info", icon="INFO")
    row = box.row()
    row.operator("wm.url_open", text="Discord", icon="INFO").url = "https://discord.gg/regrPaE5ur"
    row.operator("wm.url_open", text="Documents",
                 icon="DOCUMENTS").url = "https://blendermarket.com/products/assets-library-builder/docs"
    row.operator("wm.url_open", text="My Website", icon="WORLD").url = "https://caseysheep.com/"
    # show addon version from alb_addon_version properties
    box.label(text="Addon Version: " + alb_addon_version, icon="INFO")
    # Blender version

    # if blender version less than 3.4.0
    if bpy.app.version < (3, 4, 0):
        box.alert = True
        box.label(text="Blender Version: " + bpy.app.version_string, icon="BLENDER")
        box.label(text="Addon may not work properly in this version of Blender.", icon="ERROR")
        box.label(text="Please use Blender 3.4.0 or later.", icon="ERROR")


class ALB_PT_Documentation_and_Info(bpy.types.Panel):
    bl_label = "Documentation and Info"
    bl_idname = "ALB_PT_documentation_and_info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Assets Builder"

    def draw(self, context):
        layout = self.layout
        ALB_Documentation_and_Info(self, context, layout)


class ALB_PT_MainPanel(bpy.types.Panel):
    bl_label = "Assets Library Builder 2.0"
    bl_idname = "ALB_PT_main_panel"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_category = "Assets Builder"

    def draw(self, context):
        layout = self.layout
        is3dview = False
        settings = context.scene.alb_settings
        addon_prefs = bpy.context.preferences.addons[__name__].preferences
        if addon_prefs.preference_panel_setting_show_assets_browser_ui:
            alb_build_assets_library_button_ui(self, context, layout)
            alb_main_panel_ui(self, context, layout, is3dview)

            alb_build_assets_library_button_ui(self, context, layout)

            ALB_Documentation_and_Info(self, context, layout)


class ALB_PT_MainPanel_Npanel(bpy.types.Panel):
    bl_label = "Assets Library Builder 2.0"
    bl_idname = "ALB_PT_main_panel_npanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Assets Builder"

    # #header
    # def draw_header(self, context):
    #     layout = self.layout
    #     #reload icon
    #     layout.operator("alb.reload_icons", text="Reload icon", icon="FILE_REFRESH")

    def draw(self, context):
        layout = self.layout
        is3dview = True
        alb_build_assets_library_button_ui(self, context, layout)

        alb_main_panel_ui(self, context, layout, is3dview)
        alb_tool_panel_ui(self, context, layout)

        alb_build_assets_library_button_ui(self, context, layout)


class ALB_OT_MainOperator(bpy.types.Operator):
    bl_idname = "alb.main_operator"
    bl_label = "Build Library"
    bl_description = "Build the assets library with the current settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        base_path = context.scene.alb_base_path
        camera_move_distance_z = context.scene.alb_camera_move_distance_z
        set_to_true = False
        if not base_path:
            self.report({'ERROR'}, "Please set a valid path.")
            return {'CANCELLED'}
        # if selected any object
        if context.selected_objects:
            settings = context.scene.alb_settings

            if settings.use_camera_angle_presets:
                camera_object = alb_camera_find_active()
                save_ori_angle = camera_object.rotation_euler.copy()

                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        rv3d = area.spaces.active.region_3d

                        # check if it is camera view
                        if rv3d.view_perspective == 'CAMERA':
                            # if lock_camera is True
                            if area.spaces.active.lock_camera:
                                # set False
                                area.spaces.active.lock_camera = False
                                set_to_true = True
                # run camera_angle_setup
                bpy.ops.alb.camera_angle_setup()

            if settings.render_setting_transparent_background:
                # get film_transparent boolen value
                ori_film_transparent = bpy.context.scene.render.film_transparent

                bpy.context.scene.render.film_transparent = True

            # record view alb.record_view
            bpy.ops.alb.record_view()

            # if use_original_resolution
            if not settings.use_original_resolution:
                ori_render_resolution_resolution_x = bpy.context.scene.render.resolution_x
                ori_render_resolution_resolution_y = bpy.context.scene.render.resolution_y

                tmp_render_resolution = int(context.scene.render_resolution)

                bpy.context.scene.render.resolution_x = tmp_render_resolution
                bpy.context.scene.render.resolution_y = tmp_render_resolution

            ####
            mark_and_render_assets(base_path, camera_move_distance_z)
            ####
            if not settings.use_original_resolution:
                bpy.context.scene.render.resolution_x = ori_render_resolution_resolution_x
                bpy.context.scene.render.resolution_y = ori_render_resolution_resolution_y

            # restore view alb.restore_view
            bpy.ops.alb.restore_view()

            if settings.use_camera_angle_presets:
                # restore camera angle to ori_angle
                camera_object.rotation_euler = save_ori_angle

                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        rv3d = area.spaces.active.region_3d

                        # check if it is camera view
                        if rv3d.view_perspective != 'CAMERA':
                            if set_to_true:
                                area.spaces.active.lock_camera = True
                                rv3d.view_perspective = 'CAMERA'

            if settings.render_setting_transparent_background:
                bpy.context.scene.render.film_transparent = ori_film_transparent

        return {'FINISHED'}


class ALB_OT_BrowseFolder(bpy.types.Operator):
    bl_idname = "alb.browse_folder"
    bl_label = "Choose Assets Folder"
    directory: bpy.props.StringProperty(
        subtype='DIR_PATH',
    )

    def execute(self, context):
        if self.directory:
            context.scene.alb_base_path = self.directory
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ALB_Preferences_UI(bpy.types.AddonPreferences):
    bl_idname = "alb.addon_preferences"

    def draw(self, context):
        addon_prefs = bpy.context.preferences.addons[__name__].preferences

        layout = self.layout
        layout.prop(addon_prefs, "preference_panel_setting_show_assets_browser_ui")


def register():
    bpy.types.Scene.alb_auto_lock_camera_to_object = bpy.props.BoolProperty(
        name="Auto Lock Camera to Object",
        default=True,
    )
    # bpy.types.Scene.alb_hide_non_render_objects = bpy.props.BoolProperty(
    #     name="Hide Non-Render Objects",
    #     default=True,
    # )
    bpy.types.Scene.alb_base_path = bpy.props.StringProperty(
        name="Base Path",
        description="Path to save rendered previews",
    )
    bpy.types.Scene.alb_camera_move_distance_z = bpy.props.FloatProperty(
        name="Shooting Distance",
        description="Shooting distance (in meters)",
        default=1.0,
        min=-0.8,
        max=25.0,
    )

    bpy.types.Scene.show_camera_settings = bpy.props.BoolProperty(
        name="Show Camera Settings",
        description="Show or hide camera settings",
        default=True,
    )

    bpy.types.Scene.show_render_settings = bpy.props.BoolProperty(
        name="Show Render Settings",
        description="Show or hide render settings",
        default=False,
    )

    bpy.types.Scene.alb_show_settings = bpy.props.BoolProperty(
        name="Show Settings",
        description="Show or hide settings",
        default=True,
    )

    bpy.types.Scene.alb_show_other_tools = bpy.props.BoolProperty(
        name="Show Handy Tools",
        description="Show or hide Handy Tools",
        default=False,
    )

    bpy.types.Scene.alb_show_assets_info_ui = bpy.props.BoolProperty(
        name="Show Assets Info",
        description="Show or hide assets info",
        default=False,
    )

    # rename tool ui toogle
    bpy.types.Scene.alb_show_rename_tool_ui = bpy.props.BoolProperty(
        name="Show Rename Tool",
        description="Show or hide rename tool",
        default=False,
    )

    bpy.utils.register_class(ALB_PT_Documentation_and_Info)
    bpy.utils.register_class(ALB_PT_MainPanel)
    bpy.utils.register_class(ALB_PT_MainPanel_Npanel)

    bpy.utils.register_class(ALB_OT_MainOperator)
    bpy.utils.register_class(ALB_OT_BrowseFolder)
    bpy.utils.register_class(VIEW3D_OT_toggle_camera_view)

    bpy.utils.register_class(ALB_OT_ToggleAutoLockCamera)

    bpy.utils.register_class(ALBSettings)
    bpy.types.Scene.alb_settings = bpy.props.PointerProperty(type=ALBSettings)
    bpy.utils.register_class(ASSET_OT_CustomTagAdd)
    bpy.utils.register_class(ASSET_OT_CustomTagRemove)

    bpy.utils.register_class(ALB_OT_origin_to_bottom)

    bpy.utils.register_class(ALB_TO_set_camera_to_view)

    bpy.utils.register_class(ALB_OT_RecordView)
    bpy.utils.register_class(ALB_OT_RestoreView)

    bpy.utils.register_class(ALB_OT_camera_angle_setup)

    bpy.utils.register_class(ALB_OT_UpdateButDontRender)

    # rename tool start
    bpy.utils.register_class(RenameObjectOperator)

    bpy.utils.register_class(NumberTypePropertyGroup)
    bpy.types.Scene.obj_name = bpy.props.StringProperty(name="Name", default="Object")
    # start number
    bpy.types.Scene.start_number = bpy.props.IntProperty(name="Start Number", default=0, min=0)
    # number type
    bpy.types.Scene.number_type_properties = bpy.props.PointerProperty(type=NumberTypePropertyGroup)
    # rename tool end

    bpy.utils.register_class(ALB_OT_PreviousItem)
    bpy.utils.register_class(ALB_OT_NextItem)

    bpy.utils.register_class(ALB_OT_studio_presets_import_preset)
    bpy.utils.register_class(ALB_OT_render_studio_presets)

    bpy.utils.register_class(ALB_OT_PreviousItem_studio_preset_library)
    bpy.utils.register_class(ALB_OT_NextItem_studio_preset_library)

    bpy.utils.register_class(ALB_OT_reload_icons)

    bpy.utils.register_class(ALB_Preferences_UI)
    bpy.utils.register_class(ALB_AddonPreferences)


def unregister():
    del bpy.types.Scene.alb_auto_lock_camera_to_object
    # del bpy.types.Scene.alb_hide_non_render_objects
    del bpy.types.Scene.alb_base_path
    del bpy.types.Scene.alb_camera_move_distance_z
    del bpy.types.Scene.show_camera_settings
    del bpy.types.Scene.show_render_settings
    del bpy.types.Scene.alb_show_settings
    del bpy.types.Scene.alb_show_other_tools
    del bpy.types.Scene.alb_show_assets_info_ui
    del bpy.types.Scene.alb_show_rename_tool_ui

    bpy.utils.unregister_class(ALB_PT_MainPanel)
    bpy.utils.unregister_class(ALB_PT_MainPanel_Npanel)
    bpy.utils.unregister_class(ALB_PT_Documentation_and_Info)

    bpy.utils.unregister_class(ALB_OT_MainOperator)
    bpy.utils.unregister_class(ALB_OT_BrowseFolder)
    bpy.utils.unregister_class(VIEW3D_OT_toggle_camera_view)

    bpy.utils.unregister_class(ALB_OT_ToggleAutoLockCamera)

    bpy.utils.unregister_class(ALBSettings)
    del bpy.types.Scene.alb_settings
    bpy.utils.unregister_class(ASSET_OT_CustomTagAdd)
    bpy.utils.unregister_class(ASSET_OT_CustomTagRemove)

    bpy.utils.unregister_class(ALB_OT_origin_to_bottom)

    bpy.utils.unregister_class(ALB_TO_set_camera_to_view)

    bpy.utils.unregister_class(ALB_OT_RecordView)
    bpy.utils.unregister_class(ALB_OT_RestoreView)

    bpy.utils.unregister_class(ALB_OT_camera_angle_setup)

    bpy.utils.unregister_class(ALB_OT_UpdateButDontRender)

    # rename tool start
    bpy.utils.unregister_class(RenameObjectOperator)

    bpy.utils.unregister_class(NumberTypePropertyGroup)
    del bpy.types.Scene.obj_name
    del bpy.types.Scene.start_number
    del bpy.types.Scene.number_type_properties
    # rename tool end

    bpy.utils.unregister_class(ALB_OT_PreviousItem)
    bpy.utils.unregister_class(ALB_OT_NextItem)

    bpy.utils.unregister_class(ALB_OT_studio_presets_import_preset)
    bpy.utils.unregister_class(ALB_OT_render_studio_presets)

    bpy.utils.unregister_class(ALB_OT_PreviousItem_studio_preset_library)
    bpy.utils.unregister_class(ALB_OT_NextItem_studio_preset_library)

    bpy.utils.unregister_class(ALB_OT_reload_icons)

    bpy.utils.unregister_class(ALB_Preferences_UI)
    bpy.utils.unregister_class(ALB_AddonPreferences)


if __name__ == "__main__":
    unregister()
    register()