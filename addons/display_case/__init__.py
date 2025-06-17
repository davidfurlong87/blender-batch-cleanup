import bpy
import os
from .display_case import *
from bpy.props import BoolProperty, EnumProperty, StringProperty, FloatProperty

bl_info = {
    "name": "display_case",
    "author": "",
    "description": "a cool disp case",
    "blender": (2, 80, 0),
    "location": "View3D",
    "warning": "",
    "category": "Generic"
}

import bpy
import re
from .utils.utils import *
from mathutils import Vector

bl_category_name = "AssetOps"

geo_nodes_text_group_name = "display_case_text"


# # TODO: Delete?
# COMMAND_FUNCTIONS = {
#     "add_numbers": add_numbers,
# }


class RegexCommandProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    function: bpy.props.StringProperty()


# TODO: Copy for orient arrangements
# class RenderResolutionEnum(bpy.types.EnumProperty):
#     name = "Render Resolution"
#     description = "Select the render resolution"
#     items = [
#         ("64", "x64", "64"),
#         ("128", "x128", "128"),
#         ("256", "x256", "256"),
#         ("512", "x512", "512"),
#         ("1024", "x1024", "1024"),
#         ("2048", "x2048", "2048"),
#         ("4096", "x4096", "4096"),
#     ]
#
#
# bpy.types.Scene.render_resolution = bpy.props.EnumProperty(
#     name="Render Resolution",
#     description="Select the render resolution",
#     items=RenderResolutionEnum.items,
#     default="128",
# )

class OBJECT_PT_OrientMeshesPanel(bpy.types.Panel):
    bl_label = "Orient Meshes"
    bl_idname = "OBJECT_PT_orient_meshes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = bl_category_name

    def draw(self, context):
        layout = self.layout
        # Setting origin
        layout.label(text="Set Origin:")
        layout.prop(context.scene, "delete_empties")

        layout.operator("object.set_origin_parent", text="Set to Parent Origin")
        layout.operator("object.set_origin_bottom", text="Set to Bottom")

        layout.label(text="Display Collection:")
        layout.prop(context.scene, "use_current_collection")
        layout.label(text="New Collection Name")
        layout.prop(context.scene, "new_collection_name")
        layout.label(text="Text Object Suffix")
        layout.prop(context.scene, "text_object_suffix")
        layout.operator("object.build_display_collection", text="Build Collection")

        layout.label(text="Arrange Ops:")
        layout.label(text="Custom Arrange Separator:")
        layout.prop(context.scene, "arrange_meshes_separator")
        row = layout.row()

        layout.operator("object.arrange_meshes", text="Arrange meshes")
        layout.operator("object.update_text_objects", text="Update Text")
        row = layout.row()

        layout.prop(context.scene, "default_text_parameters")


class OBJECT_PT_CleanupPanel(bpy.types.Panel):
    bl_label = "Batch Cleanup"
    bl_idname = "OBJECT_PT_batch_cleanup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = bl_category_name

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "reload_file")

        row = layout.row()
        layout.operator("object.remove_duplicate_mats", text="Remove Duplicate Mats")
        layout.operator("object.delete_empties", text="Delete Empties")


class OBJECT_PT_AssetMakerPanel(bpy.types.Panel):
    bl_label = "Asset Maker"
    bl_idname = "OBJECT_PT_asset_maker_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = bl_category_name

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # layout.prop(context.scene, "rename_regex")
        box = layout.box()
        box.label(text="Select the location of asset images preview image", icon='INFO')
        row = box.row(align=True)
        row.prop(bpy.context.scene, "asset_preview_path", text="")
        row.operator("object.browse_folder", text="Select Folder", icon='FILE_FOLDER')
        
        box = layout.box()
        row = box.row()
        row.label(text="Image Prefix:")
        row.prop(context.scene, "asset_images_prefix", text="")
        row = box.row()
        row.label(text="Image Suffix:")
        row.prop(context.scene, "asset_images_suffix", text="")
        row = box.row()
        # row.label(text="Build Assets With Images:")
        row.operator("object.add_asset_images", text="Build Assets With Images", icon='ASSET_MANAGER')


class OBJECT_PT_RenameMeshesPanel(bpy.types.Panel):
    bl_label = "Rename Meshes"
    bl_idname = "OBJECT_PT_rename_meshes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = bl_category_name

    def draw(self, context):
        layout = self.layout
        layout.label(text="RenameMeshes:")
        layout.prop(context.scene, "rename_regex")
        
        row = layout.row()
        row.prop(context.scene, "numbers_to_add", text="Add Number")
        # TODO: reimplement below
        # row.operator("object.execute_command", text="Add Numbers").command = "add_numbers"
        
        row = layout.row()
        layout.operator("object.rename_meshes")
        layout.operator("object.clear_regex")

class VIEW3D_PT_vertex_group_creator(bpy.types.Panel):
    """Panel for creating a full vertex group"""
    bl_label = "Vertex Group Creator"
    bl_idname = "VIEW3D_PT_vertex_group_creator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = bl_category_name

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "vertex_group_name")
        layout.operator("object.create_full_vertex_group")
        layout.operator("object.assign_vertex_group_by_name")

class OBJECT_OT_create_full_vertex_group(bpy.types.Operator):
    """Create a vertex group and assign all vertices to it"""
    bl_idname = "object.create_full_vertex_group"
    bl_label = "Create Full Vertex Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        group_name = context.scene.vertex_group_name

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        # TODO: duplicated in class AssignVertexGroupOperator. Define in one place

        # Create the vertex group
        vgroup = obj.vertex_groups.get(group_name) or obj.vertex_groups.new(name=group_name)

        # Assign all vertices to the group with weight = 1.0
        indices = [v.index for v in obj.data.vertices]
        vgroup.add(index=indices, weight=1.0, type='REPLACE')

        self.report({'INFO'}, f"Assigned {len(indices)} vertices to '{group_name}'")
        return {'FINISHED'}
    
class OBJECT_OT_AssignVertexGroupOperator(bpy.types.Operator):
    """Assign all vertices to a vertex group named by the mesh name for each selected object"""
    bl_idname = "object.assign_vertex_group_by_name"
    bl_label = "Assign Vertex Group by Mesh Name"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Clear existing vertex groups
            obj.vertex_groups.clear()

            # TODO: This uses obj name from outliner. data.name will use underlying mesh name. (Which one?)
            # Create new vertex group with mesh name
            group_name = obj.name
            # group_name = obj.data.name
            vgroup = obj.vertex_groups.new(name=group_name)

            # Assign all vertices
            indices = [v.index for v in obj.data.vertices]
            vgroup.add(index=indices, weight=1.0, type='REPLACE')

        self.report({'INFO'}, "Vertex groups assigned to selected objects")
        return {'FINISHED'}

# Orient panel ops
class OBJECT_OT_SetOriginParent(bpy.types.Operator):
    bl_idname = "object.set_origin_parent"
    bl_label = "Set Origin to Parent"
    bl_description = "Sets the origin of selected objects to their parent's origin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clear_parent_keep_transform = True
        reselect_objects = True

        selected_objects = get_selected_objects_of_type('MESH')
        empties_to_delete = []
        for obj in selected_objects:
            if obj.parent and obj.type == 'MESH':
                parent = obj.parent

                # # Get parent's world location
                parent_world_loc = parent.matrix_world.translation
                new_origin_local = obj.matrix_world.inverted() @ parent_world_loc

                # # Apply new origin to the child mesh
                obj.data.transform(Matrix.Translation(-new_origin_local))

                # # Ensure child remains visually in place
                obj.matrix_world.translation = parent_world_loc

                # # TODO: Implement reload file if needed. maybe not needed if data is already deleted
                # # if (bpy.types.Scene.reload_file):

                if bpy.types.Scene.delete_empties:
                    if parent.type == 'EMPTY':
                        empties_to_delete.append(parent.name)

        if (clear_parent_keep_transform):
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        # TODO: Possibly delete this check, just have it loop regardless
        if bpy.types.Scene.delete_empties:
            for empty_name in empties_to_delete:
                delete_object_by_name(empty_name)
        # reselect all
        if (reselect_objects):
            for obj in selected_objects:
                obj.select_set(True)

        return {'FINISHED'}


class OBJECT_OT_SetOriginBottom(bpy.types.Operator):
    bl_idname = "object.set_origin_bottom"
    bl_label = "Set Origin to Bottom"
    bl_description = "Sets the origin of selected objects to their bottom and moves them to Z = 0"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clear_parent_keep_transform = True
        # delete_empties = True
        reselect_objects = True
        send_to_floor = True

        selected_objects = get_selected_objects_of_type('MESH')
        empties_to_delete = []
        bpy.ops.object.origin_set_to_bottom()

        for obj in selected_objects:
            if send_to_floor:
                obj.location.z = 0
            if bpy.types.Scene.delete_empties and obj.parent:
                parent = obj.parent
                if parent.type == 'EMPTY':
                    empties_to_delete.append(parent.name)

        if (clear_parent_keep_transform):
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        # TODO: Possibly delete this check, just have it loop regardless
        if bpy.types.Scene.delete_empties:
            for empty_name in empties_to_delete:
                delete_object_by_name(empty_name)
        if (reselect_objects):
            for obj in selected_objects:
                obj.select_set(True)
        return {'FINISHED'}


def sort_positions_list_from_axis(objects, dimension='x'):
    match dimension:
        case 'y':
            return sorted([obj.location.y for obj in objects])
        case 'z':
            return sorted([obj.location.z for obj in objects])
        case 'x':
            return sorted([obj.location.x for obj in objects])
        case _:
            # defaults to x
            return sorted([obj.location.x for obj in objects])


def get_median_point_of_objects(objects, dimension='x'):
    def get_min_max(lst):
        return [lst[0], lst[-1]]

    match dimension:
        case 'y':
            return sum(get_min_max(sort_positions_list_from_axis(objects, dimension='y'))) / 2
        case 'z':
            return sum(get_min_max(sort_positions_list_from_axis(objects, dimension='z'))) / 2
        case 'x':
            return sum(get_min_max(sort_positions_list_from_axis(objects, dimension='x'))) / 2
        case _:
            # defaults to x
            return sum(get_min_max(sort_positions_list_from_axis(objects, dimension='x'))) / 2


# TODO: This function considers empties. If meshes are parented to them, then the mesh origin may be far away from the group
# TODO: Only consider the unparented mesh origin
def add_display_text_to_collection(collection, text_object_suffix, context):
    # Get positions before we add text object
    separator_y = Vector(context.scene.arrange_meshes_separator).y
    median_x = median_point_x = get_median_point_of_objects(get_collection_objects_of_type(collection), dimension='x')
    lowest_y = get_lowest_y_from_objects(get_collection_objects_of_type(collection))

    bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.data.align_x = 'CENTER'
    text_obj = get_active_object()
    text_obj.name = collection.name + text_object_suffix
    text_obj.data.body = collection.name

    text_obj.location = Vector((median_x, lowest_y - separator_y, 0))

    if text_obj:
        # Check if a Geometry Nodes modifier already exists, if not, create one
        mod = text_obj.modifiers.get("GeometryNodes")
        if not mod:
            mod = text_obj.modifiers.new(name="GeometryNodes", type="NODES")

        # Assign the existing Geometry Nodes group to the modifier
        if geo_nodes_text_group_name in bpy.data.node_groups:
            mod.node_group = bpy.data.node_groups[geo_nodes_text_group_name]
            print(f"Assigned Geometry Nodes group '{geo_nodes_text_group_name}' to '{text_obj.name}'")
        else:
            print(f"Geometry Nodes group '{geo_nodes_text_group_name}' not found")
    else:
        print(f"Object '{text_obj.name}' not found")


def get_lowest_y_from_objects(obj_list):
    return min([obj.location.y for obj in obj_list])


class OBJECT_OT_BuildDisplayCollection(bpy.types.Operator):
    bl_idname = "object.build_display_collection"
    bl_label = "Arrange Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        collection_name = get_active_collection().name if context.scene.use_current_collection else str(
            context.scene.new_collection_name)
        if not context.scene.use_current_collection:
            if collection_name == "":
                self.report({'ERROR'}, "Collection name empty")
                return {'CANCELLED'}
            if check_collection_exists(collection_name):
                self.report({'ERROR'}, "Collection already exists")
                return {'CANCELLED'}

        collection = get_or_create_collection(collection_name)
        move_selected_objects_to_collection(collection)

        clear_collection_of_type(collection, 'FONT')

        add_display_text_to_collection(collection, get_text_obj_suffix(), context)
        if not context.scene.use_current_collection:
            link_object_to_single_collection(get_active_object(), collection)

        return {'FINISHED'}


class OBJECT_OT_ArrangeMeshes(bpy.types.Operator):
    bl_idname = "object.arrange_meshes"
    bl_label = "Arrange Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # TODO: Set as Property
        align_to_left = True

        selected_mesh_objects = get_selected_objects_of_type('MESH')

        if not selected_mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Sort objects by current X location
        selected_mesh_objects.sort(key=lambda obj: obj.location.x)

        start_vector_x = min([obj.location.x for obj in selected_mesh_objects])

        separator = Vector(context.scene.arrange_meshes_separator)
        average_dimension = average_dimensions(selected_mesh_objects, 'x')

        x_offset = 0
        position_y = selected_mesh_objects[0].location.y
        for obj in selected_mesh_objects:
            obj.location.x = start_vector_x + (x_offset * (average_dimension * separator.x))
            obj.location.y = position_y
            obj.location.z = 0
            x_offset += 1

        median_point_x = get_median_point_of_objects(selected_mesh_objects, dimension='x')
        text_object = get_collection_objects_of_type(get_active_collection(), 'FONT')
        print(text_object)
        # if text_object:
        #     text_object.location.x = median_point_x
        #     text_object.location.y = position_y - separator.y
        return {'FINISHED'}


class OBJECT_OT_UpdateTextObjects(bpy.types.Operator):
    bl_idname = "object.update_text_objects"
    bl_label = "UpdateTextObjects"
    bl_description = "Updates display case text objects with custom parameters."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}


class OBJECT_OT_RemoveDuplicateMats(bpy.types.Operator):
    bl_idname = "object.remove_duplicate_mats"
    bl_label = "Remove Duped Mats"
    bl_description = "Scans project and removes any duplicate materials."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mats = bpy.data.materials

        for mat in mats:
            (original, _, ext) = mat.name.rpartition(".")

            if ext.isnumeric() and mats.find(original) != -1:
                print("%s -> %s" % (mat.name, original))

                mat.user_remap(mats[original])
                mats.remove(mat)

        if context.scene.reload_file:
            reload_file()

        return {'FINISHED'}


class OBJECT_OT_DeleteEmpties(bpy.types.Operator):
    bl_idname = "object.delete_empties"
    bl_label = "Delete all empties in scene"
    bl_description = "Scans project and removes any empties."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        deselect_all()
        for obj in bpy.context.scene.objects:
            if obj.type == 'EMPTY':
                delete_object_by_name(obj.name)

        # Call the operator only once
        # bpy.ops.object.delete()

        if context.scene.reload_file:
            reload_file()

        return {'FINISHED'}


class OBJECT_OT_RenameMeshes(bpy.types.Operator):
    bl_idname = "object.rename_meshes"
    bl_label = "Rename Mesh Objects"
    bl_description = "Renames mesh objects based on user-defined regex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        user_pattern = context.scene.rename_regex + "(.+)"
        print("\nProcessing...\n")
        try:
            pattern = re.compile(user_pattern)
        except re.error:
            self.report({'ERROR'}, "Invalid regex pattern")
            return {'CANCELLED'}

        print(f"Scanning for mesh object names which match the pattern: {user_pattern}")
        # TODO: Replace below with "get_all_objects_of_type(*mesh_types)"
        for obj in bpy.data.objects:
            if obj.type == 'MESH':  # Ensure we're only renaming mesh objects
                match = pattern.match(obj.name)
                if match:
                    f"Match for object: {obj.name}"
                    new_name = match.group(1)  # Extract the actual mesh name
                    obj.name = new_name
                    print(f"Renamed: {obj.name} -> {new_name}")
                else:
                    print(f"Skipping {obj.name}")

        return {'FINISHED'}


class OBJECT_OT_ClearRegex(bpy.types.Operator):
    bl_idname = "object.clear_regex"
    bl_label = "Clear User-Defined Regex"
    bl_description = "Clear Dat"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.rename_regex = ""

        return {'FINISHED'}


class OBJECT_OT_BrowseFolder(bpy.types.Operator):
    bl_idname = "object.browse_folder"
    bl_label = "Choose Assets Folder"
    directory: bpy.props.StringProperty(
        subtype='DIR_PATH',
    )

    def execute(self, context):
        if self.directory:
            context.scene.asset_preview_path = self.directory
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


class TextObjectParameters(bpy.types.PropertyGroup):
    text_size: FloatProperty(name="Text Size")


PANELS = [
    OBJECT_PT_OrientMeshesPanel,
    OBJECT_PT_CleanupPanel,
    OBJECT_PT_AssetMakerPanel,
    OBJECT_PT_RenameMeshesPanel,
    VIEW3D_PT_vertex_group_creator
]

ARRANGE_OPERATORS = [
    OBJECT_OT_SetOriginParent,
    OBJECT_OT_SetOriginBottom,
    OBJECT_OT_BuildDisplayCollection,
    OBJECT_OT_ArrangeMeshes,
    OBJECT_OT_UpdateTextObjects
]

CLEANUP_OPERATORS = [
    OBJECT_OT_RemoveDuplicateMats,
    OBJECT_OT_DeleteEmpties,
    OBJECT_OT_create_full_vertex_group,
    OBJECT_OT_AssignVertexGroupOperator
]

RENAME_OPERATORS = [
    OBJECT_OT_RenameMeshes,
    # OBJECT_OT_ExecuteCommand,
    OBJECT_OT_ClearRegex
]

ASSET_MAKER_OPERATORS = [
    OBJECT_OT_BrowseFolder,
    OBJECT_OT_Add_Asset_Images
]

PARAMETER_GROUPS = [
    TextObjectParameters
]

REGISTER_CLASSES = PANELS + ARRANGE_OPERATORS + CLEANUP_OPERATORS + RENAME_OPERATORS + ASSET_MAKER_OPERATORS + PARAMETER_GROUPS


def register():
    bpy.utils.register_class(RegexCommandProperty)

    for r_class in REGISTER_CLASSES:
        bpy.utils.register_class(r_class)

    # TODO: Still needed?
    bpy.types.Scene.regex_commands = bpy.props.CollectionProperty(type=RegexCommandProperty)


    # Arrange properties
    bpy.types.Scene.arrange_meshes_separator = bpy.props.FloatVectorProperty(
        name="",
        description="Vector by which meshes will be separated."
    )
    bpy.types.Scene.use_current_collection = bpy.props.BoolProperty(
        name="Current Collection",
        description="Will use the current collection for operation.",
        default=True
    )
    bpy.types.Scene.new_collection_name = bpy.props.StringProperty(
        name="",
        description="Name for new collections",
        default=""
    )
    bpy.types.Scene.text_object_suffix = bpy.props.StringProperty(
        name="",
        description="Suffix added to text objects.",
        default="_Text"
    )
    bpy.types.Scene.delete_empties = BoolProperty(
        name="Delete Empties",
        description="Delete empties.",
        default=True
    )
    bpy.types.Scene.force_whole_numbers = BoolProperty(
        name="Whole Numbers",
        description="When arrangiong meshes, this will force the locations to be whole numbers",
        default=True
    )

    # Cleanup Properties
    bpy.types.Scene.reload_file = bpy.props.BoolProperty(
        name="Reload file",
        description="Close and reopen the file to clear data",
        default=False
    )
    bpy.types.Object.default_text_parameters = bpy.props.PointerProperty(
        type=TextObjectParameters
    )
    bpy.types.Scene.vertex_group_name = bpy.props.StringProperty(
        name="Group Name",
        description="Name of the new vertex group",
        default="MyGroup"
    )
    # bpy.types.Scene.custom_text_parameters = bpy.types.Scene.default_text_parameters


    # Regex Removal Properties

    bpy.types.Scene.rename_regex = bpy.props.StringProperty(
        name="Regex Pattern",
        description="Enter regex to match and rename meshes",
        default=r""
    )
    bpy.types.Scene.numbers_to_add = bpy.props.IntProperty(
        name="Added Numbers",
        description="Number of digits to append",
        default=0
    )

    # Asset gen properties
    bpy.types.Scene.asset_preview_path = bpy.props.StringProperty(
        name="Image Path",
        description="Path to pre-generated asset renders",
    )
    bpy.types.Scene.asset_images_prefix = bpy.props.StringProperty(
        name="File Prefix",
        description="Prefix for asset preview images",
        default="prefix_placeholder"
    )
    bpy.types.Scene.asset_images_suffix = bpy.props.StringProperty(
        name="File Suffix",
        description="Suffix for asset preview images",
        default="suffix_placeholder"
    )




def unregister():
    bpy.utils.unregister_class(RegexCommandProperty)

    del bpy.types.Object.my_prop_grp
    for r_class in REGISTER_CLASSES:
        bpy.utils.unregister_class(r_class)

    # Delete Arrange properties
    del bpy.types.Scene.arrange_meshes_separator
    del bpy.types.Scene.use_current_collection
    del bpy.types.Scene.new_collection_name
    del bpy.types.Scene.text_object_suffix
    del bpy.types.Scene.delete_empties
    del bpy.types.Scene.default_text_parameters
    del bpy.types.Scene.custom_text_parameters

    # Delete Cleanup Properties
    del bpy.types.Scene.reload_file
    del bpy.types.Scene.vertex_group_name

    # Delete renamer types
    del bpy.types.Scene.rename_regex
    del bpy.types.Scene.numbers_to_add

    # Delete asset maker types
    del bpy.types.Scene.asset_preview_path
    del bpy.types.Scene.asset_images_prefix
    del bpy.types.Scene.asset_images_suffix
    # TODO: Still needed all?
    del bpy.types.Scene.regex_commands


if __name__ == "__main__":
    register()
