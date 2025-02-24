import bpy
import re

from mathutils import Vector

bl_category_name = "AssetOps"


# -------------------------------------------
# ------------OBJECT GETTER FUNCS---------------
# -------------------------------------------
#  Functions
def get_selected_objects_of_type(*mesh_types):
    if len(mesh_types) == 0:
        return [obj for obj in bpy.context.selected_objects]
    else:
        return [obj for obj in bpy.context.selected_objects if obj.type in mesh_types]


def get_all_objects_of_type(*mesh_types):
    if len(mesh_types) == 0:
        return [obj for obj in bpy.data.objects]
    else:
        return [obj for obj in bpy.data.objects if obj.type in mesh_types]

def get_collection_objects_of_type(collection, *mesh_types):
    if len(mesh_types) == 0:
        return [obj for obj in collection.objects]
    else:
        return [obj for obj in collection.objects if obj.type in mesh_types]


def get_selected_meshes():
    return get_selected_objects_of_type('MESH')


def get_active_object():
    return bpy.context.active_object


def get_text_obj_suffix():
    return bpy.context.scene.text_object_suffix


# Collections

# -------------------------------------------
# ------------COLLECTION FUNCS---------------
# -------------------------------------------
def link_object_to_single_collection(obj, collection_to_keep):
    collection_to_keep.objects.link(obj)
    unlink_from_other_collections(obj, collection_to_keep)


def unlink_from_other_collections(obj, collection_to_keep):
    for collection in obj.users_collection:
        if collection.name != collection_to_keep.name:
            collection.objects.unlink(obj)


def move_selected_objects_to_collection(collection):
    for obj in get_selected_objects_of_type():
        if obj.name not in collection.objects:
            link_object_to_single_collection(obj, collection)


def clear_collection(collection):
    objs = [obj for obj in collection.objects]
    for obj in objs:
        bpy.data.objects.remove(obj, do_unlink=True)


def clear_collection_of_type(collection, *mesh_types):
    for obj in [obj for obj in collection.objects if obj.type in mesh_types]:
        bpy.data.objects.remove(obj, do_unlink=True)


def check_collection_exists(collection_name):
    if collection_name in bpy.data.collections:
        return True
    else:
        return False


def get_collection_by_name(collection_name):
    # TODO: Does this work? bpy.data.collections.get(target_collection_name)
    # Assumes the collection exists
    return bpy.data.collections[collection_name]

def get_active_collection():
    return bpy.context.collection


def create_new_collection(collection_name):
    return bpy.data.collections.new(collection_name)


def get_or_create_collection(collection_name, b_delete_objects=False):
    if check_collection_exists(collection_name):
        if b_delete_objects:
            clear_collection(bpy.data.collections[collection_name])
        return get_collection_by_name(collection_name)
    else:
        collection = create_new_collection(collection_name)
        bpy.context.scene.collection.children.link(collection)
        return collection


def move_objects_to_new_collection(collection_name):
    bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name=collection_name)

def add_display_text_to_collection(collection, text_object_suffix):
    bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.data.align_x = 'CENTER'
    get_active_object().name = collection.name + text_object_suffix
    get_active_object().data.body = collection.name


# -------------------------------------------
# ----------------REGEX FUNCS----------------
# -------------------------------------------
def add_numbers(context):
    regex = "^\d{" + str(context.scene.numbers_to_add) + "}"

    context.scene.rename_regex += regex


# -------------------------------------------
# ------------ARRANGING FUNCS---------------
# -------------------------------------------
def set_origin_to_parent(context):
    clear_parent_keep_transform = True
    delete_empties = True
    reselect_objects = True

    selected_objects = context.selected_objects
    # TODO: Below can be  bpy.ops.object.select_all(action='DESELECT') check difference
    bpy.ops.view3d.select(deselect_all=True)
    for obj in selected_objects:
        print(obj.name)
        if obj.parent and obj.type == 'MESH':
            # TODO: match statement here? obj.parent match => parent =>
            parent = obj.parent

            # snap cursor to parent transform
            parent.select_set(True)
            bpy.ops.view3d.snap_cursor_to_selected()
            parent.select_set(False)

            obj.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            if (clear_parent_keep_transform):
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            obj.select_set(False)

            if (delete_empties):
                parent.select_set(True)
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                bpy.ops.object.delete(use_global=True, confirm=False)

    # reselect all
    if (reselect_objects):
        for obj in selected_objects:
            obj.select_set(True)


def set_origin_to_bottom(context):
    clear_parent_keep_transform = True
    delete_empties = True
    reselect_objects = True

    selected_objects = context.selected_objects

    bpy.ops.object.origin_set_to_bottom()

    # One process for all meshes
    if (clear_parent_keep_transform):
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    for obj in selected_objects:
        if obj.type == 'MESH':
            obj.location.z = 0
            if (delete_empties and obj.parent):
                parent = obj.parent
                #TODO: Below can be  bpy.ops.view3d.select(deselect_all=True) check difference
                bpy.ops.object.select_all(action='DESELECT')
                parent.select_set(True)
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                bpy.ops.object.delete(use_global=True, confirm=False)

        # reselect all
        if (reselect_objects):
            for obj in selected_objects:
                obj.select_set(True)

def average_dimensions(objects, dimension = 'x'):
    match dimension:
        case 'y':
            return sum([obj.dimensions.y for obj in objects]) / len(objects)
        case 'z':
            return sum([obj.dimensions.z for obj in objects]) / len(objects)
        case 'x':
            return sum([obj.dimensions.x for obj in objects]) / len(objects)
        case _:
            return sum([obj.dimensions.x for obj in objects]) / len(objects)

def get_median_point_of_objects(objects, dimension = 'x'):
    match dimension:
        case 'y':
            return sum([obj.location.y for obj in objects]) / len(objects)
        case 'z':
            return sum([obj.location.z for obj in objects]) / len(objects)
        case 'x':
            return sum([obj.location.x for obj in objects]) / len(objects)
        case _:
            return sum([obj.location.x for obj in objects]) / len(objects)


def deselect_all():
    bpy.ops.object.select_all(action='DESELECT')


def reload_file():
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)


# TODO: Delete?
COMMAND_FUNCTIONS = {
    "add_numbers": add_numbers,
}


class RegexCommandProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    function: bpy.props.StringProperty()


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


class OBJECT_PT_RenameMeshesPanel(bpy.types.Panel):
    bl_label = "Rename Meshes"
    bl_idname = "OBJECT_PT_rename_meshes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = bl_category_name

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "rename_regex")

        row = layout.row()
        row.prop(context.scene, "numbers_to_add", text="Add Number")
        row.operator("object.execute_command", text="Add Numbers").command = "add_numbers"

        row = layout.row()
        layout.operator("object.rename_meshes")
        layout.operator("object.clear_regex")


# TODO: Remove?
class OBJECT_OT_ExecuteCommand(bpy.types.Operator):
    bl_idname = "object.execute_command"
    bl_label = "Execute Command"
    bl_description = "Executes a predefined function"
    bl_options = {'REGISTER', 'UNDO'}

    command: bpy.props.StringProperty()

    def execute(self, context):
        if self.command in COMMAND_FUNCTIONS:
            COMMAND_FUNCTIONS[self.command](context)
        else:
            self.report({'ERROR'}, f"Unknown command: {self.command}")
        return {'FINISHED'}


# Orient panel ops
class OBJECT_OT_SetOriginParent(bpy.types.Operator):
    bl_idname = "object.set_origin_parent"
    bl_label = "Set Origin to Parent"
    bl_description = "Sets the origin of selected objects to their parent's origin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        set_origin_to_parent(context)
        return {'FINISHED'}


class OBJECT_OT_SetOriginBottom(bpy.types.Operator):
    bl_idname = "object.set_origin_bottom"
    bl_label = "Set Origin to Bottom"
    bl_description = "Sets the origin of selected objects to their bottom and moves them to Z = 0"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        set_origin_to_bottom(context)
        return {'FINISHED'}


class OBJECT_OT_BuildDisplayCollection(bpy.types.Operator):
    bl_idname = "object.build_display_collection"
    bl_label = "Arrange Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        collection_name = str(context.scene.new_collection_name)
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
        add_display_text_to_collection(collection, get_text_obj_suffix())
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
                obj.select_set(True)

        # Call the operator only once
        bpy.ops.object.delete()

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

PANELS = [
    OBJECT_PT_OrientMeshesPanel,
    OBJECT_PT_CleanupPanel,
    OBJECT_PT_RenameMeshesPanel
]

ARRANGE_OPERATORS = [
    OBJECT_OT_SetOriginParent,
    OBJECT_OT_SetOriginBottom,
    OBJECT_OT_BuildDisplayCollection,
    OBJECT_OT_ArrangeMeshes
]

CLEANUP_OPERATORS = [
    OBJECT_OT_RemoveDuplicateMats,
    OBJECT_OT_DeleteEmpties
]

RENAME_OPERATORS = [
    OBJECT_OT_RenameMeshes,
    OBJECT_OT_ExecuteCommand,
    OBJECT_OT_ClearRegex
]

def register():
    bpy.utils.register_class(RegexCommandProperty)

    for panel in PANELS:
        bpy.utils.register_class(panel)

    for operator in ARRANGE_OPERATORS:
        bpy.utils.register_class(operator)

    for operator in CLEANUP_OPERATORS:
        bpy.utils.register_class(operator)

    for operator in RENAME_OPERATORS:
        bpy.utils.register_class(operator)

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

    # Cleanup Properties
    bpy.types.Scene.reload_file = bpy.props.BoolProperty(
        name="Reload file",
        description="Close and reopen the file to clear data",
        default=False
    )

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

    # TODO: Still needed?
    bpy.types.Scene.regex_commands = bpy.props.CollectionProperty(type=RegexCommandProperty)
    scene = bpy.context.scene
    scene.regex_commands.clear()


def unregister():
    bpy.utils.unregister_class(RegexCommandProperty)

    for panel in PANELS:
        bpy.utils.unregister_class(panel)

    for operator in ARRANGE_OPERATORS:
        bpy.utils.unregister_class(operator)

    for operator in CLEANUP_OPERATORS:
        bpy.utils.unregister_class(operator)

    for operator in RENAME_OPERATORS:
        bpy.utils.unregister_class(operator)

    del bpy.types.Scene.arrange_meshes_separator
    del bpy.types.Scene.use_current_collection
    del bpy.types.Scene.new_collection_name

    del bpy.types.Scene.reload_file

    del bpy.types.Scene.rename_regex
    del bpy.types.Scene.numbers_to_add

    # TODO: Still needed all?
    del bpy.types.Scene.regex_commands


if __name__ == "__main__":
    register()
