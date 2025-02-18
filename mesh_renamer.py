import bpy
import re


class RegexCommandProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    function: bpy.props.StringProperty()


class OBJECT_PT_FindAndReplacePanel(bpy.types.Panel):
    bl_label = "Rename Meshes"
    bl_idname = "OBJECT_PT_find_and_replace_names"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BatchRenamer"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "rename_regex")
        layout.label(text="Commands:")

        row = layout.row()
        row.prop(context.scene, "numbers_to_add", text="Add Number")
        row.operator("object.execute_command", text="Add Numbers").command = "add_numbers"

        for command in context.scene.regex_commands:
            if command.function != "add_number":
                op = layout.operator("object.execute_command", text=command.name)
                op.command = command.function

        row = layout.row()
        layout.operator("object.rename_meshes")
        layout.operator("object.clear_regex")

class OBJECT_PT_RenameMeshesPanel(bpy.types.Panel):
    bl_label = "Rename Meshes"
    bl_idname = "OBJECT_PT_rename_meshes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BatchRenamer"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "rename_regex")
        layout.label(text="Commands:")

        row = layout.row()
        row.prop(context.scene, "numbers_to_add", text="Add Number")
        row.operator("object.execute_command", text="Add Numbers").command = "add_numbers"

        for command in context.scene.regex_commands:
            if command.function != "add_number":
                op = layout.operator("object.execute_command", text=command.name)
                op.command = command.function

        row = layout.row()
        layout.operator("object.rename_meshes")
        layout.operator("object.clear_regex")

        # Setting origin
        layout.separator()
        layout.label(text="Set Origin:")
        layout.operator("object.set_origin_parent", text="Set to Parent Origin")
        layout.operator("object.set_origin_bottom", text="Set to Bottom")


class OBJECT_OT_ExecuteCommand(bpy.types.Operator):
    bl_idname = "object.execute_command"
    bl_label = "Execute Command"
    bl_description = "Executes a predefined function"

    command: bpy.props.StringProperty()

    def execute(self, context):
        if self.command in COMMAND_FUNCTIONS:
            COMMAND_FUNCTIONS[self.command](context)
        else:
            self.report({'ERROR'}, f"Unknown command: {self.command}")
        return {'FINISHED'}


def add_underscore(context):
    context.scene.rename_regex += "_"


def add_numbers(context):
    numbers_to_add = context.scene.numbers_to_add
    regex = "^\d{" + str(context.scene.numbers_to_add) + "}"

    context.scene.rename_regex += regex


def add_text(context):
    context.scene.rename_regex += "YOUR_TEXT"


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


COMMAND_FUNCTIONS = {
    "add_underscore": add_underscore,
    "add_numbers": add_numbers,
    "add_text": add_text,
}

class OBJECT_OT_SetOriginParent(bpy.types.Operator):
    bl_idname = "object.set_origin_parent"
    bl_label = "Set Origin to Parent"
    bl_description = "Sets the origin of selected objects to their parent's origin"

    def execute(self, context):
        set_origin_to_parent(context)
        return {'FINISHED'}

class OBJECT_OT_SetOriginBottom(bpy.types.Operator):
    bl_idname = "object.set_origin_bottom"
    bl_label = "Set Origin to Bottom"
    bl_description = "Sets the origin of selected objects to their bottom and moves them to Z = 0"

    def execute(self, context):
        set_origin_to_bottom(context)
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


def register():
    bpy.utils.register_class(RegexCommandProperty)
    bpy.utils.register_class(OBJECT_PT_RenameMeshesPanel)
    bpy.utils.register_class(OBJECT_OT_RenameMeshes)
    bpy.utils.register_class(OBJECT_OT_ExecuteCommand)
    bpy.utils.register_class(OBJECT_OT_ClearRegex)
    bpy.utils.register_class(OBJECT_OT_SetOriginParent)
    bpy.utils.register_class(OBJECT_OT_SetOriginBottom)


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

    bpy.types.Scene.regex_commands = bpy.props.CollectionProperty(type=RegexCommandProperty)

    scene = bpy.context.scene
    scene.regex_commands.clear()

    command_list = [
        ("Add Underscore", "add_underscore"),
        # ("Add Numbers", "add_numbers"),
        ("Add Text", "add_text")
    ]

    # # Find and Replace Properties
    # bpy.types.Scene.text_to_find = bpy.props.StringProperty(
    #     name="Text to Find",
    #     description="The text to search for in an object's name",
    #     default=r""
    # )

    for name, function in command_list:
        item = scene.regex_commands.add()
        item.name = name
        item.function = function


def unregister():
    bpy.utils.unregister_class(RegexCommandProperty)
    bpy.utils.unregister_class(OBJECT_PT_RenameMeshesPanel)
    bpy.utils.unregister_class(OBJECT_OT_RenameMeshes)
    bpy.utils.unregister_class(OBJECT_OT_ExecuteCommand)
    bpy.utils.unregister_class(OBJECT_OT_ClearRegex)
    bpy.utils.unregister_class(OBJECT_OT_SetOriginParent)
    bpy.utils.unregister_class(OBJECT_OT_SetOriginBottom)

    del bpy.types.Scene.rename_regex
    del bpy.types.Scene.numbers_to_add
    del bpy.types.Scene.regex_commands


if __name__ == "__main__":
    register()

