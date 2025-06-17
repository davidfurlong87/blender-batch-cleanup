# import bpy
# import re
# from .utils.utils import *
# from mathutils import Vector
#
# bl_category_name = "AssetOps"
#
#
# # # TODO: Delete?
# # COMMAND_FUNCTIONS = {
# #     "add_numbers": add_numbers,
# # }
#
#
# class RegexCommandProperty(bpy.types.PropertyGroup):
#     name: bpy.props.StringProperty()
#     function: bpy.props.StringProperty()
#
#
# class OBJECT_PT_OrientMeshesPanel(bpy.types.Panel):
#     bl_label = "Orient Meshes"
#     bl_idname = "OBJECT_PT_orient_meshes"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = bl_category_name
#
#     def draw(self, context):
#         layout = self.layout
#         # Setting origin
#         layout.label(text="Set Origin:")
#         layout.operator("object.set_origin_parent", text="Set to Parent Origin")
#         layout.operator("object.set_origin_bottom", text="Set to Bottom")
#
#         layout.label(text="Display Collection:")
#         layout.prop(context.scene, "use_current_collection")
#         layout.label(text="New Collection Name")
#         layout.prop(context.scene, "new_collection_name")
#         layout.label(text="Text Object Suffix")
#         layout.prop(context.scene, "text_object_suffix")
#         layout.operator("object.build_display_collection", text="Build Collection")
#
#         layout.label(text="Arrange Ops:")
#         layout.label(text="Custom Arrange Separator:")
#         layout.prop(context.scene, "arrange_meshes_separator")
#         row = layout.row()
#
#         layout.operator("object.arrange_meshes", text="Arrange meshes")
#
#
# class OBJECT_PT_CleanupPanel(bpy.types.Panel):
#     bl_label = "Batch Cleanup"
#     bl_idname = "OBJECT_PT_batch_cleanup"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = bl_category_name
#
#     def draw(self, context):
#         layout = self.layout
#         layout.prop(context.scene, "reload_file")
#
#         row = layout.row()
#         layout.operator("object.remove_duplicate_mats", text="Remove Duplicate Mats")
#         layout.operator("object.delete_empties", text="Delete Empties")
#
#
# class OBJECT_PT_AssetMakerPanel(bpy.types.Panel):
#     bl_label = "Asset Maker"
#     bl_idname = "OBJECT_PT_asset_maker_panel"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = bl_category_name
#
#     def draw(self, context):
#         layout = self.layout
#         # layout.prop(context.scene, "rename_regex")
#
#         row = layout.row()
#         layout.label(text="AssetMaker:")
#         row = layout.row()
#         layout.label(text="AssetMaker debug:")
#         row = layout.row()
#         layout.label(text="AssetMaker debug:")
#         # row.prop(context.scene, "numbers_to_add", text="Add Number")
#         # row.operator("object.execute_command", text="Add Numbers").command = "add_numbers"
#         #
#         # row = layout.row()
#         # layout.operator("object.rename_meshes")
#         layout.operator("object.browse_folder")
#
#
# class OBJECT_PT_RenameMeshesPanel(bpy.types.Panel):
#     bl_label = "Rename Meshes"
#     bl_idname = "OBJECT_PT_rename_meshes"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = bl_category_name
#
#     def draw(self, context):
#         layout = self.layout
#         layout.label(text="RenameMeshes:")
#         # layout.prop(context.scene, "rename_regex")
#         #
#         # row = layout.row()
#         # row.prop(context.scene, "numbers_to_add", text="Add Number")
#         # # TODO: reimplement below
#         # # row.operator("object.execute_command", text="Add Numbers").command = "add_numbers"
#         #
#         # row = layout.row()
#         # layout.operator("object.rename_meshes")
#         # layout.operator("object.clear_regex")
#
#
# # TODO: Remove?
# # class OBJECT_OT_ExecuteCommand(bpy.types.Operator):
# #     bl_idname = "object.execute_command"
# #     bl_label = "Execute Command"
# #     bl_description = "Executes a predefined function"
# #     bl_options = {'REGISTER', 'UNDO'}
# #
# #     command: bpy.props.StringProperty()
# #
# #     def execute(self, context):
# #         if self.command in COMMAND_FUNCTIONS:
# #             COMMAND_FUNCTIONS[self.command](context)
# #         else:
# #             self.report({'ERROR'}, f"Unknown command: {self.command}")
# #         return {'FINISHED'}
#
#
# # Orient panel ops
# class OBJECT_OT_SetOriginParent(bpy.types.Operator):
#     bl_idname = "object.set_origin_parent"
#     bl_label = "Set Origin to Parent"
#     bl_description = "Sets the origin of selected objects to their parent's origin"
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#         set_origin_to_parent(context)
#         return {'FINISHED'}
#
#
# class OBJECT_OT_SetOriginBottom(bpy.types.Operator):
#     bl_idname = "object.set_origin_bottom"
#     bl_label = "Set Origin to Bottom"
#     bl_description = "Sets the origin of selected objects to their bottom and moves them to Z = 0"
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#         set_origin_to_bottom(context)
#         return {'FINISHED'}
#
#
# class OBJECT_OT_BuildDisplayCollection(bpy.types.Operator):
#     bl_idname = "object.build_display_collection"
#     bl_label = "Arrange Meshes"
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#         collection_name = str(context.scene.new_collection_name)
#         if not context.scene.use_current_collection:
#             if collection_name == "":
#                 self.report({'ERROR'}, "Collection name empty")
#                 return {'CANCELLED'}
#             if check_collection_exists(collection_name):
#                 self.report({'ERROR'}, "Collection already exists")
#                 return {'CANCELLED'}
#
#         collection = get_or_create_collection(collection_name)
#         move_selected_objects_to_collection(collection)
#
#         clear_collection_of_type(collection, 'FONT')
#         add_display_text_to_collection(collection, get_text_obj_suffix())
#         if not context.scene.use_current_collection:
#             link_object_to_single_collection(get_active_object(), collection)
#
#         return {'FINISHED'}
#
#
# class OBJECT_OT_ArrangeMeshes(bpy.types.Operator):
#     bl_idname = "object.arrange_meshes"
#     bl_label = "Arrange Meshes"
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#         # TODO: Set as Property
#         align_to_left = True
#
#         selected_mesh_objects = get_selected_objects_of_type('MESH')
#
#         if not selected_mesh_objects:
#             self.report({'ERROR'}, "No mesh objects selected")
#             return {'CANCELLED'}
#
#         # Sort objects by current X location
#         selected_mesh_objects.sort(key=lambda obj: obj.location.x)
#
#         start_vector_x = min([obj.location.x for obj in selected_mesh_objects])
#
#         separator = Vector(context.scene.arrange_meshes_separator)
#         average_dimension = average_dimensions(selected_mesh_objects, 'x')
#
#         x_offset = 0
#         position_y = selected_mesh_objects[0].location.y
#         for obj in selected_mesh_objects:
#             obj.location.x = start_vector_x + (x_offset * (average_dimension * separator.x))
#             obj.location.y = position_y
#             obj.location.z = 0
#             x_offset += 1
#
#         median_point_x = get_median_point_of_objects(selected_mesh_objects, dimension='x')
#         text_object = get_collection_objects_of_type(get_active_collection(), 'FONT')
#         print(text_object)
#         # if text_object:
#         #     text_object.location.x = median_point_x
#         #     text_object.location.y = position_y - separator.y
#         return {'FINISHED'}
#
#
# class OBJECT_OT_RemoveDuplicateMats(bpy.types.Operator):
#     bl_idname = "object.remove_duplicate_mats"
#     bl_label = "Remove Duped Mats"
#     bl_description = "Scans project and removes any duplicate materials."
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#         mats = bpy.data.materials
#
#         for mat in mats:
#             (original, _, ext) = mat.name.rpartition(".")
#
#             if ext.isnumeric() and mats.find(original) != -1:
#                 print("%s -> %s" % (mat.name, original))
#
#                 mat.user_remap(mats[original])
#                 mats.remove(mat)
#
#         if context.scene.reload_file:
#             reload_file()
#
#         return {'FINISHED'}
#
#
# class OBJECT_OT_DeleteEmpties(bpy.types.Operator):
#     bl_idname = "object.delete_empties"
#     bl_label = "Delete all empties in scene"
#     bl_description = "Scans project and removes any empties."
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#         deselect_all()
#         for obj in bpy.context.scene.objects:
#             if obj.type == 'EMPTY':
#                 obj.select_set(True)
#
#         # Call the operator only once
#         bpy.ops.object.delete()
#
#         if context.scene.reload_file:
#             reload_file()
#
#         return {'FINISHED'}
#
#
# class OBJECT_OT_RenameMeshes(bpy.types.Operator):
#     bl_idname = "object.rename_meshes"
#     bl_label = "Rename Mesh Objects"
#     bl_description = "Renames mesh objects based on user-defined regex"
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#         user_pattern = context.scene.rename_regex + "(.+)"
#         print("\nProcessing...\n")
#         try:
#             pattern = re.compile(user_pattern)
#         except re.error:
#             self.report({'ERROR'}, "Invalid regex pattern")
#             return {'CANCELLED'}
#
#         print(f"Scanning for mesh object names which match the pattern: {user_pattern}")
#         # TODO: Replace below with "get_all_objects_of_type(*mesh_types)"
#         for obj in bpy.data.objects:
#             if obj.type == 'MESH':  # Ensure we're only renaming mesh objects
#                 match = pattern.match(obj.name)
#                 if match:
#                     f"Match for object: {obj.name}"
#                     new_name = match.group(1)  # Extract the actual mesh name
#                     obj.name = new_name
#                     print(f"Renamed: {obj.name} -> {new_name}")
#                 else:
#                     print(f"Skipping {obj.name}")
#
#         return {'FINISHED'}
#
#
# class OBJECT_OT_ClearRegex(bpy.types.Operator):
#     bl_idname = "object.clear_regex"
#     bl_label = "Clear User-Defined Regex"
#     bl_description = "Clear Dat"
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#         context.scene.rename_regex = ""
#
#         return {'FINISHED'}
#
#
# class OBJECT_OT_BrowseFolder(bpy.types.Operator):
#     bl_idname = "object.browse_folder"
#     bl_label = "Choose Assets Folder"
#     directory: bpy.props.StringProperty(
#         subtype='DIR_PATH',
#     )
#
#     def execute(self, context):
#         if self.directory:
#             context.scene.alb_base_path = self.directory
#         return {'FINISHED'}
#
#     def invoke(self, context, event):
#         context.window_manager.fileselect_add(self)
#         return {'RUNNING_MODAL'}
