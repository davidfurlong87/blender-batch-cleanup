import bpy
from mathutils import Vector, Matrix


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





def delete_object_by_name(obj_name):
    bpy.data.objects.remove(bpy.data.objects[obj_name])


# -------------------------------------------
# ----------------REGEX FUNCS----------------
# -------------------------------------------
def add_numbers(context):
    regex = "^\d{" + str(context.scene.numbers_to_add) + "}"

    context.scene.rename_regex += regex


# -------------------------------------------
# ------------ARRANGING FUNCS---------------
# -------------------------------------------

def average_dimensions(objects, dimension='x'):
    match dimension:
        case 'y':
            return sum([obj.dimensions.y for obj in objects]) / len(objects)
        case 'z':
            return sum([obj.dimensions.z for obj in objects]) / len(objects)
        case 'x':
            return sum([obj.dimensions.x for obj in objects]) / len(objects)
        case _:
            return sum([obj.dimensions.x for obj in objects]) / len(objects)


def deselect_all():
    bpy.ops.object.select_all(action='DESELECT')


def reload_file():
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
