import numpy as np
from bpy.types import OperatorFileListElement
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector
from datetime import datetime
from pathlib import Path
import os
import bpy
import math

SetupBlendFile = "BrushEditorSetup.blend"
CompositingBlendFile = (
    "BrushEditor_5_0_CompositingNodes.blend"  # Used in Blender 5.0 and up
)

brush_texture_type_enum = bpy.props.EnumProperty(
    items={
        (
            "Vector Displacement",
            "Vector Displacement",
            "For brushes with overhangs. Only the sculpt plane will be used for rendering",
            0,
        ),
        (
            "Height Displacement",
            "Height Displacement",
            "For brushes that use height map that only displace in surface normal direction",
            1,
        ),
    },
    default="Vector Displacement",
    options={"HIDDEN"},
    name="Type",
)

brush_preview_type = bpy.props.EnumProperty(
    items={
        ("Flat", "Flat", "Brush surface: Plane (Looking from above)", 0),
        ("Tilted", "Tilted", "Brush surface: Plane (Looking from an angle)", 1),
        ("Sphere", "Sphere", "Brush surface: Sphere (Looking from an angle)", 2),
    },
    default="Sphere",
    name="Preview Type",
)

texture_resolution_enum = bpy.props.EnumProperty(
    items={
        ("128", "128 px", "Render with 128 x 128 pixels", 1),
        ("256", "256 px", "Render with 256 x 256 pixels", 2),
        ("512", "512 px", "Render with 512 x 512 pixels", 3),
        ("1024", "1024 px", "Render with 1024 x 1024 pixels", 4),
        ("2048", "2048 px", "Render with 2048 x 2048 pixels", 5),
        ("4096", "4096 px", "Render with 4096 x 4096 pixels", 6),
    },
    default="512",
    name="Texture resolution",
)

vdm_color_depth_enum = bpy.props.EnumProperty(
    items={
        ("16", "16", "Reduced file size", 1),
        ("32", "32", "", 2),
    },
    default="32",
    name="Texture color depth",
)

heightmap_color_depth_enum = bpy.props.EnumProperty(
    items={
        ("8", "8", "Reduced file size", 1),
        ("16", "16", "", 2),
    },
    default="16",
    name="Texture color depth",
)


def get_addon_prefs():
    preferences = bpy.context.preferences
    return preferences.addons[__name__].preferences


class SculptBrushTextureEditorPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    default_brush_type: brush_texture_type_enum  # type: ignore

    default_texture_resolution_vdm: texture_resolution_enum  # type: ignore
    default_texture_resolution_height: texture_resolution_enum  # type: ignore
    compression: bpy.props.EnumProperty(
        items={
            ("none", "None", "", 1),
            ("zip", "ZIP (lossless)", "", 2),
        },
        default="zip",
        name="VDM texture compression",
    )  # type: ignore

    vdm_color_depth: vdm_color_depth_enum  # type: ignore

    heightmap_color_depth: heightmap_color_depth_enum  # type: ignore

    use_transparent_preview_background: bpy.props.BoolProperty(
        name="Use transparent preview background", default=True
    )  # type: ignore

    preview_world_color: bpy.props.FloatVectorProperty(
        name="Preview background color",
        subtype="COLOR",
        min=0.0,
        max=1.0,
        default=[0.002, 0.003, 0.005],
    )  # type: ignore

    preferred_preview_type: brush_preview_type  # type: ignore

    sculpting_plane_vertices_per_side: (
        bpy.props.IntProperty(  # So we have default values
            name="Sculpting plane vertex count per edge loop",
            default=128,
            min=16,
            max=128,
        )
    )  # type: ignore

    sculpting_plane_multires_subdivisions: (
        bpy.props.IntProperty(  # So we have default values
            name="Sculpting plane multires subdivisions", default=1, min=0, max=5
        )
    )  # type: ignore

    render_samples: bpy.props.IntProperty(
        name="Render samples", default=64, min=2, max=4096
    )  # type: ignore

    default_brush_hardness: bpy.props.FloatProperty(
        name="Default brush hardness",
        default=0.9,
        min=0,
        max=1.0,
        description="The hardness defines where the gradual falloff begins. 1.0 means constant falloff a the brush border",
    )  # type: ignore

    def draw(self, context):
        layout = self.layout

        brushtype_layout = layout.row(align=True)
        brushtype_layout.label(text="Preferred brush type")
        brushtype_layout.prop(self, "default_brush_type", text="")

        heightmap_res_layout = layout.row(align=True)
        heightmap_res_layout.label(text="Default heightmap texture resolution")
        heightmap_res_layout.prop(self, "default_texture_resolution_height", text="")

        vdm_res_layout = layout.row(align=True)
        vdm_res_layout.label(text="Default VDM texture resolution")
        vdm_res_layout.prop(self, "default_texture_resolution_vdm", text="")

        compression_layout = layout.row(align=True)
        compression_layout.label(text="VDM compression type")
        compression_layout.prop(self, "compression", text="")

        heightmap_bitdepth_layout = layout.row(align=True)
        heightmap_bitdepth_layout.label(text="Heightmap texture color depth")
        heightmap_bitdepth_layout.prop(self, "heightmap_color_depth", text="")

        vdm_bitdepth_layout = layout.row(align=True)
        vdm_bitdepth_layout.label(text="VDM texture color depth")
        vdm_bitdepth_layout.prop(self, "vdm_color_depth", text="")

        samples_layout = layout.row(align=True)
        samples_layout.label(text="Render samples:")
        samples_layout.prop(self, "render_samples", text="")

        hardness_layout = layout.row(align=True)
        hardness_layout.label(text="Default brush hardness")
        hardness_layout.prop(self, "default_brush_hardness")

        layout.separator()

        bgcolortransparent_layout = layout.row(align=True)
        bgcolortransparent_layout.label(text="Use transparent preview background")
        bgcolortransparent_layout.prop(
            self, "use_transparent_preview_background", text=""
        )

        if get_addon_prefs().use_transparent_preview_background == False:
            bgcolor_layout = layout.row(align=True)
            bgcolor_layout.label(text="Preview background color")
            bgcolor_layout.prop(self, "preview_world_color", text="")

        previewtype_layout = layout.row(align=True)
        previewtype_layout.label(text="Preferred preview type")
        previewtype_layout.prop(self, "preferred_preview_type", text="")


def GetVDMBakeMaterial():
    """Try to find VDM material in current file.
    If not found, load the VDM material from the SetupBlendFile.
    """
    global SetupBlendFile
    if bpy.data.materials.find("VDM_baking_material") == -1:
        global AddonDirectory
        addondir = Path(AddonDirectory)

        bpy.ops.wm.append(
            filepath=SetupBlendFile,
            directory=str(Path.joinpath(addondir, SetupBlendFile, "Material")),
            filename="VDM_baking_material",
        )

    bpy.data.materials["VDM_baking_material"].use_fake_user = True
    return bpy.data.materials["VDM_baking_material"]


def GetCompositingNodeGroup(in_name, in_scene):
    """Try to find Compositing Node Group in current file.
    If not found, load the Compositing Node Group from the CompositingBlendFile.
    """

    global CompositingBlendFile
    if bpy.data.node_groups.find(in_name) == -1:
        global AddonDirectory
        addondir = Path(AddonDirectory)

        bpy.ops.wm.append(
            filepath=CompositingBlendFile,
            directory=str(Path.joinpath(addondir, CompositingBlendFile, "NodeTree")),
            filename=in_name,
        )

        bpy.data.node_groups[in_name].nodes["Render Layers"].scene = in_scene

    bpy.data.node_groups[in_name].use_fake_user = True
    return bpy.data.node_groups[in_name]


class BrushImportSettings(bpy.types.PropertyGroup):
    files: bpy.props.CollectionProperty(name="File paths", type=OperatorFileListElement)  # type: ignore

    preview_type: brush_preview_type  # type: ignore

    directory: bpy.props.StringProperty(subtype="DIR_PATH")  # type: ignore

    x_channel: bpy.props.EnumProperty(
        items={
            ("X", "X", "X (red) channel", 0),
            ("Y", "Y", "Y (green) channel", 1),
            ("Z", "Z", "Z (blue) channel", 2),
        },
        default="X",
        name="Swizzle X",
    )  # type: ignore
    y_channel: bpy.props.EnumProperty(
        items={
            ("X", "X", "X (red) channel", 0),
            ("Y", "Y", "Y (green) channel", 1),
            ("Z", "Z", "Z (blue) channel", 2),
        },
        default="Y",
        name="Y",
    )  # type: ignore
    z_channel: bpy.props.EnumProperty(
        items={
            ("X", "X", "X (red) channel", 0),
            ("Y", "Y", "Y (green) channel", 1),
            ("Z", "Z", "Z (blue) channel", 2),
        },
        default="Z",
        name="Z",
    )  # type: ignore

    channel_multiply: bpy.props.FloatVectorProperty(
        name="Channel multiply of x y z", default=[1.0, 1.0, 1.0]
    )  # type: ignore

    enable_texture_resize: bpy.props.BoolProperty(
        name="Change texture size", default=False
    )  # type: ignore
    max_texture_size: bpy.props.IntProperty(
        name="Max texture size",
        subtype="PIXEL",
        default=512,
        min=16,
        max=4096,
        description="Scales images down that are bigger than this value",
    )  # type: ignore

    added_prefix: bpy.props.StringProperty(name="Added brush name prefix")  # type: ignore
    directory: bpy.props.StringProperty(name="Directory")  # type: ignore

    vdm_brush_strength: bpy.props.FloatProperty(
        name="VDM brush strength",
        default=1.0,
        soft_min=0,
        soft_max=1.0,
        description="The default brush strength for VDMs",
    )  # type: ignore
    heightmap_brush_strength: bpy.props.FloatProperty(
        name="Heightmap brush strength",
        default=0.25,
        soft_min=0,
        soft_max=1.0,
        description="The default brush strength for height maps/alphas",
    )  # type: ignore

    brush_hardness: bpy.props.FloatProperty(
        name="Brush hardness",
        default=0.9,
        min=0,
        max=1.0,
        description="The hardness defines where the gradual falloff begins. 1.0 means constant falloff a the brush border",
    )  # type: ignore

    sample_bias: bpy.props.FloatProperty(
        name="Sample bias",
        default=0.0,
        min=-1.0,
        max=1.0,
        description="Brush setting. It has no effect on the image itself but values will be shifted while you paint",
    )  # type: ignore

    vdm_preview_displacement: bpy.props.FloatProperty(
        name="Preview VDM displacement",
        default=1.0,
        min=0.0,
        max=5.0,
        description="Multiplied with brush strength. Determines how much the preview mesh is displaced by the texture",
    )  # type: ignore

    heightmap_preview_displacement: bpy.props.FloatProperty(
        name="Heightmap preview displacement",
        default=1.0,
        min=0.0,
        max=5.0,
        description="Multiplied with brush strength. Determines how much the preview mesh is displaced by the texture",
    )  # type: ignore


class BrushComponent(bpy.types.PropertyGroup):
    mesh_object: bpy.props.PointerProperty(
        type=bpy.types.Object, name="Object used for rendering", description=""
    )  # type: ignore


class CustomMadeBrush(bpy.types.PropertyGroup):
    brush_name: bpy.props.StringProperty(
        name="Brush name",
        description="The name that is used for the brush and texture.",
    )  # type: ignore
    brush: bpy.props.PointerProperty(
        type=bpy.types.Brush, name="Custom brush", description=""
    )  # type: ignore
    texture: bpy.props.PointerProperty(
        type=bpy.types.Texture, name="Custom created texture", description=""
    )  # type: ignore
    image: bpy.props.PointerProperty(
        type=bpy.types.Image, name="Custom rendered image", description=""
    )  # type: ignore
    sample_bias: bpy.props.FloatProperty(
        name="Sample bias", description="Calculated as remapped_shifting_value"
    )  # type: ignore
    canvas_mesh: bpy.props.PointerProperty(
        type=bpy.types.Object, name="Canvas mesh", description=""
    )  # type: ignore
    brush_strength: bpy.props.FloatProperty(
        name="Brush strength",
        default=1.0,
        min=0.0,
        max=1.0,
        description="The correct strength so the height of the brush is the same as in the brush editor",
    )  # type: ignore
    brush_texture_type: brush_texture_type_enum  # type: ignore
    preview_type: brush_preview_type  # type: ignore
    preview_rotation: bpy.props.FloatProperty(
        name="Preview object rotation",
        description="Rotates the preview object before rendering about x degrees",
        subtype="ANGLE",
    )  # type: ignore
    is_loaded_image_brush: bpy.props.BoolProperty(
        name="Is loaded image brush", default=False
    )  # type: ignore

    # Data specific to heightmap brushes
    # The whole point of having a collection of MESH objects that are visible to the render is the ability to render more than just the 'mesh canvas'.
    # This opens up for more possibilities in height maps. They can consist of arbitrary meshes.
    # Using the canvas to sculpt on is just the default that most people might use to create organic and seamless shapes.
    objects_used_for_rendering: bpy.props.CollectionProperty(
        type=BrushComponent, name="Objects used for rendering", description=""
    )


class SculptBrushEditorAddonData(bpy.types.PropertyGroup):
    # Added this property in version 1.1.1
    saved_addon_version: bpy.props.StringProperty(
        name="Saved addon version",
        default="1.1.1",
        description="The addon version this file was saved with.",
    )

    editor_scene: bpy.props.PointerProperty(
        type=bpy.types.Scene, name="EditorScene", description=""
    )
    editor_workspace: bpy.props.PointerProperty(
        type=bpy.types.WorkSpace, name="EditorWorkspace", description=""
    )
    default_scene: bpy.props.PointerProperty(
        type=bpy.types.Scene, name="DefaultScene", description=""
    )
    default_workspace: bpy.props.PointerProperty(
        type=bpy.types.WorkSpace, name="DefaultWorkspace", description=""
    )

    draft_brush_name: bpy.props.StringProperty(
        name="Name", description="The name that will be used for the brush and texture."
    )
    current_canvas_mesh: bpy.props.PointerProperty(
        type=bpy.types.Object, name="Current canvas mesh", description=""
    )
    current_edited_brush: bpy.props.IntProperty(
        name="Current edited brush index", description="", default=-1
    )
    brush_collection: bpy.props.CollectionProperty(type=CustomMadeBrush)
    create_preview_image: bpy.props.BoolProperty(
        name="Create brush preview image", default=True
    )
    heightmap_render_camera: bpy.props.PointerProperty(
        type=bpy.types.Object, name="Brush render camera", description=""
    )

    current_brush_texture_type: brush_texture_type_enum
    current_preview_type: brush_preview_type
    preview_rotation: bpy.props.FloatProperty(
        name="Preview object rotation",
        description="Rotates the preview object before rendering about x degrees",
        subtype="ANGLE",
    )

    sculpting_plane_vertices_per_side: bpy.props.IntProperty(
        name="Sculpting plane vertex count per edge loop", default=128, min=16, max=128
    )
    sculpting_plane_multires_subdivisions: bpy.props.IntProperty(
        name="Sculpting plane multires subdivisions", default=1, min=0, max=5
    )

    # Data for heightmap brushes
    use_map_range_zero_to_one: bpy.props.BoolProperty(
        name="Always use full value range",
        default=True,
        description="The resulting brush will behave the same way but the height map will look different. Using a full range means there is always pure white and pure black in the texture",
    )
    limit_z_sample_start: bpy.props.BoolProperty(
        name="Limit Z sample start",
        default=False,
        description="The minimum Z location in world space that is captured inside the height map",
    )
    limit_z_sample_end: bpy.props.BoolProperty(
        name="Limit Z sample end",
        default=False,
        description="The maximum Z location in world space that is captured inside the height map",
    )
    min_z_sample: bpy.props.FloatProperty(
        name="Min Z location",
        description="The minimum Z location in world space that is captured inside the height map",
        default=0,
    )
    max_z_sample: bpy.props.FloatProperty(
        name="Max Z location",
        description="The maximum Z location in world space that is captured inside the height map",
        default=1.0,
    )
    current_brush_import_settings: bpy.props.PointerProperty(type=BrushImportSettings)


def GetSingletonName():
    return "SculptBrushTextureEditorData"


def HasAddonData():
    return bpy.data.objects.find(GetSingletonName()) > -1


def GetAddonData() -> SculptBrushEditorAddonData:
    singleton_name = GetSingletonName()
    if bpy.data.objects.find(singleton_name) == -1:
        bpy.data.objects.new(singleton_name, None)

    return bpy.data.objects[singleton_name].SculptBrushEditorData


def does_brush_have_an_image(brush):
    if brush is None:
        return False
    return (
            brush.texture is not None
            and brush.texture.type == "IMAGE"
            and brush.texture.image is not None
    )


def GetOutputPath(filename, is_relative=False):
    save_path = bpy.app.tempdir
    if bpy.data.is_saved:
        save_path = os.path.dirname(bpy.data.filepath)

    if is_relative and bpy.data.is_saved:
        return bpy.path.relpath(os.path.join(save_path, "brush_images", filename))
    else:
        return os.path.join(save_path, "brush_images", filename)


def GetCustomBrushDataFromBrush(brush):
    addon_data = GetAddonData()

    for index, brush_data in enumerate(addon_data.brush_collection):
        if brush_data.brush and brush_data.brush == brush:
            return index, brush_data

    return -1, None


def draw_sculpting_resolution_box(self):
    data = get_addon_prefs()
    if HasAddonData():
        data = GetAddonData()

    layout = self.layout

    layout_box = layout.box()
    layout_box.label(text="Resolution for new sculpting plane")

    vertexcount_layout = layout_box.row(align=True)
    vertexcount_layout.label(text="Vertices per side")
    vertexcount_layout.prop(data, "sculpting_plane_vertices_per_side", text="")

    subdivision_layout = layout_box.row(align=True)
    subdivision_layout.label(text="Subdivisions")
    subdivision_layout.prop(data, "sculpting_plane_multires_subdivisions", text="")

    vertex_count = data.sculpting_plane_vertices_per_side * math.pow(
        2, data.sculpting_plane_multires_subdivisions
    )
    total_vertex_count = vertex_count * vertex_count
    layout_row = layout_box.column(align=True)
    layout_row.label(text=f"Vertex counts", icon="INFO")
    layout_row.label(text=f"Subdivided per side: {round(vertex_count):,}")
    layout_row.label(text=f"Subdivided total: {round(total_vertex_count):,}")


class EDITOR_PT_TextureMapBrush(bpy.types.Panel):
    bl_label = "Brush Texture Editor"
    bl_idname = "EDITOR_PT_LayoutPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_context = ".sculpt_mode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if HasAddonData():
            addon_data = GetAddonData()

            # Inside the editor
            if (
                    addon_data.editor_scene
                    and bpy.context.window.scene == addon_data.editor_scene
            ):
                is_occupied, brush_name = GetNewBrushName()
                button_text = "Render brush and close"

                is_new_name = False
                if addon_data.current_edited_brush > -1:
                    brush_data = addon_data.brush_collection[
                        addon_data.current_edited_brush
                    ]
                    if brush_name == brush_data.brush_name:
                        is_occupied = False

                    button_text = "Apply changes to brush and close"

                overwrite = "Overwrite" if is_occupied else "Create"

                if is_occupied:
                    button_text = "Overwrite brush and close"

                layout.operator(
                    CloseBrushMapEditorAndSave.bl_idname,
                    text=button_text,
                    icon="META_DATA",
                )

                if is_occupied:
                    layout.label(text="Name taken: Overrides brush.", icon="INFO")

                layout_box = layout.box()
                layout_box.prop(addon_data, "draft_brush_name")

                brushtype_settings = layout_box.column(align=True)
                brushtype_settings.prop(addon_data, "current_brush_texture_type")
                if addon_data.current_brush_texture_type == "Vector Displacement":
                    brushtype_settings.label(text="VDMs need intact UVs.", icon="INFO")

                else:
                    brushtype_settings.prop(addon_data, "limit_z_sample_start")
                    if addon_data.limit_z_sample_start:
                        brushtype_settings.prop(addon_data, "min_z_sample")
                    brushtype_settings.prop(addon_data, "limit_z_sample_end")
                    if addon_data.limit_z_sample_end:
                        brushtype_settings.prop(addon_data, "max_z_sample")

                    brushtype_settings.prop(addon_data, "use_map_range_zero_to_one")

                preview_layout_col = layout_box.column(align=True)
                preview_layout_col.prop(addon_data, "create_preview_image")
                if addon_data.create_preview_image:
                    preview_layout = preview_layout_col.row(align=True)
                    preview_layout.label(text="Preview type")
                    preview_layout.prop(addon_data, "current_preview_type", text="")
                    preview_rotation_layout = preview_layout_col.row(align=True)
                    preview_rotation_layout.label(text="Preview rotation")
                    preview_rotation_layout.prop(
                        addon_data, "preview_rotation", text=""
                    )

                layout.separator()

                layout.operator(
                    CloseBrushMapEditorWithoutSave.bl_idname,
                    text="Close without saving",
                    icon="PANEL_CLOSE",
                )

            # Outside the editor
            else:
                if does_brush_have_an_image(context.tool_settings.sculpt.brush):
                    layout.operator(
                        OpenBrushMapEditor.bl_idname,
                        text="Edit current brush",
                        icon="CURRENT_FILE",
                    ).edited_brush_name = context.tool_settings.sculpt.brush.name

                layout.operator(
                    OpenBrushMapEditor.bl_idname,
                    text="Create new brush",
                    icon="META_DATA",
                ).edited_brush_name = ""
                draw_sculpting_resolution_box(self)

                layout.prop(context.scene, "SculptBrushEditorDedicatedWorkspace")

                index, brush_data = GetCustomBrushDataFromBrush(
                    context.tool_settings.sculpt.brush
                )
                if (
                        brush_data
                        and brush_data.brush_texture_type == "Height Displacement"
                ):
                    row = layout.row()
                    row.operator(ResetBrushStrength.bl_idname)
                    row.operator(ResetSampleBias.bl_idname)

                layout_box = layout.box()
                layout_box.operator(
                    OT_TexturesFilebrowser.bl_idname,
                    text="Make brush(es) from image(s)",
                    icon="FILEBROWSER",
                )

                layout.operator(
                    RerenderPreviewImages.bl_idname,
                    text="Rerender previews",
                    icon="IMAGE_DATA",
                )

        # That is extra so we don't create addon data in each blend-file we open.
        else:
            if does_brush_have_an_image(context.tool_settings.sculpt.brush):
                layout.operator(
                    OpenBrushMapEditor.bl_idname,
                    text="Edit current brush",
                    icon="CURRENT_FILE",
                ).edited_brush_name = context.tool_settings.sculpt.brush.name

            layout.operator(
                OpenBrushMapEditor.bl_idname, text="Create new brush", icon="META_DATA"
            ).edited_brush_name = ""
            draw_sculpting_resolution_box(self)
            layout.prop(context.scene, "SculptBrushEditorDedicatedWorkspace")

            layout_box = layout.box()
            layout_box.operator(
                OT_TexturesFilebrowser.bl_idname,
                text="Make brush(es) from image(s)",
                icon="FILEBROWSER",
            )


def GetCurrentCanvasMesh() -> bpy.types.Object:
    addon_data = GetAddonData()
    canvas_mesh = None
    if addon_data.current_canvas_mesh:
        canvas_mesh = addon_data.current_canvas_mesh
    elif addon_data.current_edited_brush > -1:
        canvas_mesh = addon_data.brush_collection[
            addon_data.current_edited_brush
        ].canvas_mesh

    return canvas_mesh  # can be None


def AppendNewCanvasMesh(add_multires=True, override_subivisions=1):
    addon_data = GetAddonData()
    addon_prefs = get_addon_prefs()

    subdivs = (
        override_subivisions
        if override_subivisions > 1
        else addon_data.sculpting_plane_vertices_per_side
    )
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=subdivs,
        y_subdivisions=subdivs,
        size=2,
        enter_editmode=False,
        align="WORLD",
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )
    canvas_mesh = bpy.context.active_object

    if add_multires:
        multires = canvas_mesh.modifiers.new("MultiresPlane", type="MULTIRES")
        multires.boundary_smooth = "PRESERVE_CORNERS"

        for index in range(addon_data.sculpting_plane_multires_subdivisions):
            bpy.ops.object.multires_subdivide(
                modifier="MultiresPlane", mode="CATMULL_CLARK"
            )

    canvas_mesh.name = "BrushTexturePlane"
    canvas_mesh.lock_location[0] = True
    canvas_mesh.lock_location[1] = True
    canvas_mesh.lock_location[2] = True
    canvas_mesh.lock_rotation[0] = True
    canvas_mesh.lock_rotation[1] = True
    canvas_mesh.lock_rotation[2] = True

    return canvas_mesh


def set_preview_collections(addon_data, active):
    collections = addon_data.editor_scene.view_layers[0].layer_collection.children

    if collections.find("BrushPreviewTilted") > -1:
        collections["BrushPreviewTilted"].exclude = not active
    if collections.find("BrushPreviewSphere") > -1:
        collections["BrushPreviewSphere"].exclude = not active
    if collections.find("BrushPreviewFlat") > -1:
        collections["BrushPreviewFlat"].exclude = not active


def GetBrushHeightmapRenderCamera() -> bpy.types.Object:
    addon_data = GetAddonData()

    if addon_data.heightmap_render_camera is None:
        if addon_data.editor_scene.find("HeightmapRenderCamera") == -1:
            global SetupBlendFile
            global AddonDirectory
            addondir = Path(AddonDirectory)

            bpy.ops.wm.append(
                filepath=SetupBlendFile,
                directory=str(Path.joinpath(addondir, SetupBlendFile, "Object")),
                filename="HeightmapRenderCamera",
            )
            addon_data.heightmap_render_camera = bpy.context.active_object

        else:
            addon_data.heightmap_render_camera = addon_data.editor_scene.objects[
                "HeightmapRenderCamera"
            ]

    return addon_data.heightmap_render_camera


def GetBrushPreviewRenderCamera() -> bpy.types.Object:
    addon_data = GetAddonData()

    cameraname = f"BrushPreviewCamera{addon_data.current_preview_type}"
    preview_camera = None

    if addon_data.editor_scene.objects[cameraname] is not None:
        preview_camera = addon_data.editor_scene.objects[cameraname]

    if preview_camera == None:
        print("Preview camera wasn't found")
    return preview_camera


def SelectCanvasMesh():
    for selected_objects in bpy.context.selected_objects:
        selected_objects.select_set(False)

    plane = GetCurrentCanvasMesh()
    if plane is None:
        print("Sculpt Brush Editor: Couldn't find canvas mesh object!")
    else:
        plane.select_set(True)
        bpy.context.view_layer.objects.active = plane


def GetNewBrushName():
    addon_data = GetAddonData()

    is_name_occupied = False
    for custom_brush in addon_data.brush_collection:
        if custom_brush.brush_name == addon_data.draft_brush_name:
            is_name_occupied = True
            break

    if addon_data.draft_brush_name != "":
        return is_name_occupied, addon_data.draft_brush_name
    else:
        date = datetime.now()
        dateformat = date.strftime("%b-%d-%Y-%H-%M-%S")
        return False, f"brush-{dateformat}"


def GetVisibleMeshes():
    addon_data = GetAddonData()
    # Couldn't use context.visible_objects because this doesn't include objects hidden from render.
    scene_objects = addon_data.editor_scene.objects
    scene_meshes = []

    for scene_object in scene_objects:
        if scene_object.type == "MESH":
            scene_meshes.append(scene_object)

    visible_meshes_viewport = []
    visible_meshes_render = []

    for scene_mesh in scene_meshes:
        if scene_mesh.hide_render == False:
            visible_meshes_render.append(scene_mesh)
        if scene_mesh.visible_get():
            visible_meshes_viewport.append(scene_mesh)

    return visible_meshes_viewport, visible_meshes_render


AddonDirectory = ""


def HideAllMeshesForRenderAndViewport():
    visible_meshes_viewport, visible_meshes_render = GetVisibleMeshes()

    for mesh in visible_meshes_viewport:
        mesh.hide_set(True)

    for mesh in visible_meshes_render:
        mesh.hide_render = True


def OpenEditorSceneAndWorkspace(context):
    addon_data = GetAddonData()
    global SetupBlendFile
    global AddonDirectory
    addondir = Path(AddonDirectory)

    if addon_data.editor_scene is None:
        bpy.ops.wm.append(
            filepath=SetupBlendFile,
            directory=str(Path.joinpath(addondir, SetupBlendFile, "Scene")),
            filename="BrushEditScene",
        )

        addon_data.editor_scene = bpy.data.scenes["BrushEditScene"]
        addon_data.heightmap_render_camera = addon_data.editor_scene.objects[
            "HeightmapRenderCamera"
        ]

        addon_data.sculpting_plane_multires_subdivisions = (
            get_addon_prefs().sculpting_plane_multires_subdivisions
        )
        addon_data.sculpting_plane_vertices_per_side = (
            get_addon_prefs().sculpting_plane_vertices_per_side
        )

    if (
            addon_data.editor_workspace is None
            and context.scene.SculptBrushEditorDedicatedWorkspace
    ):
        bpy.ops.wm.append(
            filepath=SetupBlendFile,
            directory=str(Path.joinpath(addondir, SetupBlendFile, "WorkSpace")),
            filename="Brush Editor",
        )

        addon_data.editor_workspace = bpy.data.workspaces["Brush Editor"]

    if context.scene != addon_data.editor_scene:
        addon_data.default_scene = context.scene
    if (
            context.scene.SculptBrushEditorDedicatedWorkspace
            and context.workspace != addon_data.editor_workspace
    ):
        addon_data.default_workspace = context.workspace

    if context.scene.SculptBrushEditorDedicatedWorkspace:
        context.window.workspace = addon_data.editor_workspace
    print(str(addon_data.editor_scene))
    context.window.scene = addon_data.editor_scene

    collections = addon_data.editor_scene.view_layers[0].layer_collection.children
    if collections.find("BrushEditing") > -1:
        collections["BrushEditing"].exclude = False
    set_preview_collections(addon_data, False)

    addon_data.editor_scene.SculptBrushEditorDataFakeUser = bpy.data.objects[
        GetSingletonName()
    ]


def PrepareRenderObjectsAndCanvas(add_multires=True, override_subivisions=1):
    addon_data = GetAddonData()

    # Hide every mesh and show only the objects that are relevant to us.
    HideAllMeshesForRenderAndViewport()
    canvas_mesh = GetCurrentCanvasMesh()
    if canvas_mesh is None:
        canvas_mesh = AppendNewCanvasMesh(add_multires, override_subivisions)

    addon_data.current_canvas_mesh = canvas_mesh

    if addon_data.current_edited_brush > -1:
        brush = addon_data.brush_collection[addon_data.current_edited_brush]
        for object in brush.objects_used_for_rendering:
            if object and object.mesh_object:
                object.mesh_object.hide_set(False)
                object.mesh_object.hide_render = False

    canvas_mesh.hide_set(False)
    canvas_mesh.hide_render = False
    SelectCanvasMesh()


def UpdateSceneToNewAddonVersion():
    addon_data = GetAddonData()
    current_version = addon_data.saved_addon_version
    global bl_info
    new_version = f"{bl_info['version']}"
    addon_data.saved_addon_version = new_version

    if current_version != new_version:
        # For future changes to the addon data
        pass


class OpenBrushMapEditor(bpy.types.Operator):
    bl_idname = "texturemap.openeditor"
    bl_label = "Open brush editor"
    bl_description = (
        "Switch to a scene and workspace where a new brush map can be sculpted"
    )
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    edited_brush_name: bpy.props.StringProperty(
        name="Edited brush", options={"HIDDEN"}, default=""
    )

    def execute(self, context):
        addon_data = GetAddonData()
        ResetTemporaryAddonData()

        is_unknown_brush = False
        if self.edited_brush_name != "":
            blender_brush_data = bpy.data.brushes[self.edited_brush_name]
            index, brush_data = GetCustomBrushDataFromBrush(blender_brush_data)

            if brush_data is not None and brush_data.is_loaded_image_brush == False:
                addon_data.current_edited_brush = index
                addon_data.draft_brush_name = brush_data.brush_name
                addon_data.current_brush_texture_type = brush_data.brush_texture_type
                addon_data.current_preview_type = brush_data.preview_type
                addon_data.preview_rotation = brush_data.preview_rotation

            # We edit a brush that is unknown to the add-on
            elif does_brush_have_an_image(blender_brush_data):
                addon_data.draft_brush_name = blender_brush_data.name
                displacement_type = (
                    "Vector Displacement"
                    if blender_brush_data.use_color_as_displacement
                    else "Height Displacement"
                )
                addon_data.current_brush_texture_type = displacement_type
                addon_data.current_preview_type = (
                    get_addon_prefs().preferred_preview_type
                )
                is_unknown_brush = True

        else:
            addon_data.current_brush_texture_type = get_addon_prefs().default_brush_type
            addon_data.current_preview_type = get_addon_prefs().preferred_preview_type
            is_occupied, brush_name = GetNewBrushName()
            addon_data.draft_brush_name = brush_name

        OpenEditorSceneAndWorkspace(context)

        UpdateSceneToNewAddonVersion()

        if is_unknown_brush:
            PrepareRenderObjectsAndCanvas(False, 128)
            blender_brush_data = bpy.data.brushes[self.edited_brush_name]
            canvas_mesh = GetCurrentCanvasMesh()
            texture_displacement_geonodes = canvas_mesh.modifiers.new(
                "Geometry Nodes", type="NODES"
            )
            texture_displacement_geonodes.node_group = bpy.data.node_groups[
                "Texture Displacement"
            ]
            texture_displacement_geonodes["Input_2"] = blender_brush_data.texture.image
            texture_displacement_geonodes["Input_5"] = (
                blender_brush_data.use_color_as_displacement
            )
            texture_displacement_geonodes["Input_7"][2] = math.pow(
                blender_brush_data.strength, 2
            )
            self.report({"INFO"}, "Added geometry nodes for displacement.")

            width = blender_brush_data.texture.image.size[0]
            render_subdivs = 0
            if width > 128:
                render_subdivs = 1
            if width > 256:
                render_subdivs = 2
            if width > 512:
                render_subdivs = 3

            viewport_subdivs = min(1, render_subdivs)
            texture_displacement_geonodes["Input_13"] = viewport_subdivs
            texture_displacement_geonodes["Input_14"] = render_subdivs

        else:
            PrepareRenderObjectsAndCanvas()

        bpy.ops.object.mode_set(mode="SCULPT")

        return {"FINISHED"}


color_channel_enum = bpy.props.EnumProperty(
    items={
        ("X", "X", "X or red channel", 0),
        ("Y", "Y", "Y or green channel", 1),
        ("Z", "Z", "Z or blue channel", 2),
    },
    default="X",
    name="Swizzle",
)


def set_vdm_scene_image_settings(scene):
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.exr_codec = "NONE"
    if get_addon_prefs().compression == "zip":
        scene.render.image_settings.exr_codec = "ZIP"

    scene.render.image_settings.color_depth = get_addon_prefs().vdm_color_depth


class OT_TexturesFilebrowser(bpy.types.Operator, ImportHelper):
    bl_idname = "texture.open_filebrowser"
    bl_label = "Load brush textures"
    bl_options = {"UNDO"}

    filter_glob: bpy.props.StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.exr", options={"HIDDEN"}
    )

    import_settings: bpy.props.PointerProperty(type=BrushImportSettings)

    files: bpy.props.CollectionProperty(name="File paths", type=OperatorFileListElement)
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def draw(self, context):
        layout = self.layout

        settings = self.import_settings
        layout.alignment = "RIGHT"
        layout.label(text="EXR files are loaded as VDM brushes.", icon="INFO")
        layout.separator()

        layout_box = layout.box()
        layout_box.label(text="Texture manipulation on import:")

        swizzling_layout = layout_box.column(align=True)
        swizzling_layout.prop(settings, "x_channel")
        swizzling_layout.prop(settings, "y_channel")
        swizzling_layout.prop(settings, "z_channel")

        channel_layout = layout_box.column()
        channel_layout.prop(settings, "channel_multiply")

        texture_resize_col = layout_box.column(align=True)
        texture_resize_col.prop(settings, "enable_texture_resize")
        texturesize_layout = texture_resize_col.row()
        texturesize_layout.enabled = settings.enable_texture_resize
        texturesize_layout.prop(settings, "max_texture_size")

        brushname_layout = layout.row(align=True)
        brushname_layout.label(text="Added name prefix:")
        brushname_layout.prop(settings, "added_prefix", text="")

        layout.separator()

        brushstrength_layout = layout.column()
        brushstrength_layout.label(text="Default brush settings:")
        brushstrength_layout.prop(settings, "vdm_brush_strength")
        brushstrength_layout.prop(settings, "heightmap_brush_strength")

        brushstrength_layout.prop(settings, "brush_hardness")
        brushstrength_layout.prop(settings, "sample_bias")

        layout.separator()

        preview_layout = layout.column()
        preview_layout.label(text="Brush preview settings:")
        preview_layout.prop(settings, "preview_type")
        preview_layout.prop(settings, "vdm_preview_displacement")
        preview_layout.prop(settings, "heightmap_preview_displacement")

    def execute(self, context):
        addon_data = GetAddonData()

        properties = [
            p.identifier
            for p in self.import_settings.bl_rna.properties
            if not p.is_readonly
        ]
        for prop in properties:
            setattr(
                addon_data.current_brush_import_settings,
                prop,
                getattr(self.import_settings, prop),
            )

        addon_data.current_brush_import_settings.files.clear()
        for file in self.files:
            filename = addon_data.current_brush_import_settings.files.add()
            filename.name = file.name

        addon_data.current_brush_import_settings.directory = self.directory

        bpy.ops.loadbrushes.modal_operator("EXEC_DEFAULT")
        return {"FINISHED"}


def ChangeBrush(brush):
    if bpy.app.version >= (4, 4, 0):
        brush_path = os.path.join("Brush", brush.name)
        bpy.ops.brush.asset_activate(
            asset_library_type="LOCAL", relative_asset_identifier=brush_path
        )
    else:
        bpy.context.tool_settings.sculpt.brush = brush


class LoadBrushesModal(bpy.types.Operator):
    bl_idname = "loadbrushes.modal_operator"
    bl_label = "Load brushes"
    bl_options = {"INTERNAL", "UNDO"}

    new_brushes = []
    current_file_index = 0

    def execute(self, context):
        self.new_brushes = []
        self.current_file_index = 0
        OpenEditorSceneAndWorkspace(context)

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def get_channel_index(self, channel):
        if channel == "X":
            return 0
        if channel == "Y":
            return 1
        else:
            return 2

    def cancel(self, context):
        ReturnToNormalWorkspaceAndScene()
        ResetTemporaryAddonData()

        if bpy.context.active_object and bpy.context.active_object.type == "MESH":
            if bpy.context.active_object.mode != "SCULPT":
                bpy.ops.object.mode_set(mode="SCULPT")

            for new_brush in self.new_brushes:
                new_brush.texture_slot.map_mode = "AREA_PLANE"

        if len(self.new_brushes) > 0:
            self.report({"INFO"}, f"Made {len(self.new_brushes)} new draw brush(es).")
            if bpy.context.active_object and bpy.context.active_object.mode == "SCULPT":
                ChangeBrush(new_brush)
        else:
            self.report({"WARNING"}, f"Did not create new brushes.")

    def modal(self, context, event):
        if event.type in {"ESC"}:  # Cancel
            self.cancel(context)
            return {"CANCELLED"}

        addon_data = GetAddonData()
        settings = addon_data.current_brush_import_settings
        try:
            if self.current_file_index < len(settings.files):
                filepath = settings.files[self.current_file_index]
                image_name = filepath.name

                filepath = os.path.join(settings.directory, filepath.name)
                extension = Path(filepath).suffix

                image_name = image_name.replace(extension, "")
                image_name = f"{settings.added_prefix}{image_name}"
                is_vdm = extension == ".exr"
                scene = bpy.context.scene

                # Get a unique name for the brush, so we don't overwrite them
                number_suffix = 0
                string_suffix = ""
                original_image_name = image_name
                new_image_name = original_image_name
                while f"{original_image_name}{string_suffix}" in bpy.data.images:
                    number_suffix += 1
                    # imitate Blenders numbering
                    string_suffix = "_" + (f"{number_suffix}".zfill(3))
                    new_image_name = f"{original_image_name}{string_suffix}"

                loaded_image = bpy.data.images.load(filepath)
                loaded_image.alpha_mode = "NONE"
                texture_has_changed = False
                loaded_image.name = new_image_name

                if (
                        settings.x_channel != "X"
                        or settings.y_channel != "Y"
                        or settings.z_channel != "Z"
                        or settings.channel_multiply[0] != 1.0
                        or settings.channel_multiply[1] != 1.0
                        or settings.channel_multiply[2] != 1.0
                ):

                    to_image = loaded_image.copy()
                    channel_number = loaded_image.channels
                    to_image.name = f"{loaded_image.name}1"

                    pixels_from = np.empty(
                        shape=len(loaded_image.pixels), dtype=np.float32
                    )
                    loaded_image.pixels.foreach_get(pixels_from)
                    pixels_to = np.empty(
                        shape=len(loaded_image.pixels), dtype=np.float32
                    )
                    to_image.pixels.foreach_get(pixels_to)

                    if channel_number > 1:  # If image is not black and white
                        if settings.x_channel != "X":
                            new_x_channel = self.get_channel_index(settings.x_channel)
                            pixels_to[new_x_channel::channel_number] = pixels_from[
                                                                       0::channel_number
                                                                       ]

                        if settings.y_channel != "Y":
                            new_y_channel = self.get_channel_index(settings.y_channel)
                            pixels_to[new_y_channel::channel_number] = pixels_from[
                                                                       1::channel_number
                                                                       ]

                        if settings.z_channel != "Z":
                            new_z_channel = self.get_channel_index(settings.z_channel)
                            pixels_to[new_z_channel::channel_number] = pixels_from[
                                                                       2::channel_number
                                                                       ]

                    if settings.channel_multiply[0] != 1.0:
                        pixels_to[0::channel_number] *= settings.channel_multiply[0]

                    if settings.channel_multiply[1] != 1.0 and channel_number > 1:
                        pixels_to[1::channel_number] *= settings.channel_multiply[1]

                    if settings.channel_multiply[2] != 1.0 and channel_number > 1:
                        pixels_to[2::channel_number] *= settings.channel_multiply[2]

                    to_image.pixels.foreach_set(pixels_to)
                    bpy.data.images.remove(loaded_image)
                    to_image.name = new_image_name
                    loaded_image = to_image

                    texture_has_changed = True

                if (
                        settings.enable_texture_resize
                        and loaded_image.size[0] > settings.max_texture_size
                ):
                    loaded_image.scale(
                        settings.max_texture_size, settings.max_texture_size
                    )
                    texture_has_changed = True

                scene = addon_data.editor_scene

                if texture_has_changed:
                    output_path = GetOutputPath(
                        f"{loaded_image.name}{extension}", is_relative=True
                    )
                    loaded_image.filepath_raw = output_path

                    if is_vdm:
                        set_vdm_scene_image_settings(scene)

                    else:
                        scene.render.image_settings.file_format = "PNG"
                        scene.render.image_settings.color_mode = "BW"
                        if get_addon_prefs().heightmap_color_depth == "16":
                            scene.render.image_settings.color_depth = "16"
                        else:
                            scene.render.image_settings.color_depth = "32"

                    loaded_image.save_render(
                        filepath=GetOutputPath(
                            f"{loaded_image.name}{extension}", is_relative=False
                        ),
                        scene=scene,
                    )
                    # Remove dirty flag, since we saved the image already (Blender doesn't remove the flag after save_render)
                    loaded_image.reload()

                new_brush, brush_texture, custom_brush_data = (
                    make_new_brush_and_texture(new_image_name, new_image_name)
                )

                new_brush.use_color_as_displacement = is_vdm

                loaded_image.colorspace_settings.is_data = True
                brush_texture.image = loaded_image
                new_brush.texture_sample_bias = settings.sample_bias
                new_brush.hardness = settings.brush_hardness
                new_brush.strength = (
                    settings.vdm_brush_strength
                    if is_vdm
                    else settings.heightmap_brush_strength
                )

                self.new_brushes.append(new_brush)

                custom_brush_data.is_loaded_image_brush = True
                custom_brush_data.image = brush_texture.image
                custom_brush_data.brush_texture_type = (
                    "Vector Displacement" if is_vdm else "Height Displacement"
                )
                custom_brush_data.preview_type = settings.preview_type
                custom_brush_data.preview_rotation = 0
                custom_brush_data.sample_bias = settings.sample_bias
                custom_brush_data.brush_strength = new_brush.strength

                # Preview image
                if addon_data.create_preview_image:
                    displacement_multiplier = (
                        settings.vdm_preview_displacement
                        if is_vdm
                        else settings.heightmap_preview_displacement
                    )
                    render_preview_image(
                        addon_data,
                        new_image_name,
                        new_brush,
                        0,
                        0.2,
                        loaded_image,
                        displacement_multiplier,
                    )

        except BaseException as Err:
            self.report({"ERROR"}, f"{Err}")

        finally:
            self.current_file_index += 1

        if self.current_file_index == len(settings.files):
            self.cancel(context)
            return {"FINISHED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context, event):

        return {"RUNNING_MODAL"}


class RerenderPreviewImages(bpy.types.Operator):
    bl_idname = "rerenderpreviews.modal_operator"
    bl_label = "Rerender Previes"
    bl_options = {"INTERNAL", "UNDO"}

    new_brushes = []
    current_file_index = 0

    def __init__(self):
        pass

    def __del__(self):
        pass

    def invoke(self, context, event):
        self.new_brushes = []

        for brush in bpy.data.brushes:
            if brush.use_paint_sculpt == False:
                continue

            if brush.texture is None or brush.texture.image is None:
                continue

            self.new_brushes.append(brush)

        self.current_file_index = 0
        OpenEditorSceneAndWorkspace(context)

        print(f"Renders {len(self.new_brushes)} new previews...")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        pass

    def cancel(self, context):
        ReturnToNormalWorkspaceAndScene()
        ResetTemporaryAddonData()

        if bpy.context.active_object and bpy.context.active_object.type == "MESH":
            if bpy.context.active_object.mode != "SCULPT":
                bpy.ops.object.mode_set(mode="SCULPT")

        if len(self.new_brushes) > 0:
            self.report({"INFO"}, f"Made {len(self.new_brushes)} new previews.")
        else:
            self.report({"WARNING"}, f"No brushes available to create previews for.")

    def modal(self, context, event):
        if len(self.new_brushes) == 0:
            self.cancel(context)
            return {"FINISHED"}

        if event.type in {"ESC"}:  # Cancel
            self.cancel(context)
            return {"CANCELLED"}

        try:
            if self.current_file_index < len(self.new_brushes):
                addon_data = GetAddonData()
                settings = addon_data.current_brush_import_settings
                new_brush = self.new_brushes[self.current_file_index]

                # Preview image
                displacement_multiplier = (
                    settings.vdm_preview_displacement
                    if new_brush.use_color_as_displacement
                    else settings.heightmap_preview_displacement
                )
                render_preview_image(
                    addon_data,
                    new_brush.name,
                    new_brush,
                    0,
                    0.2,
                    new_brush.texture.image,
                    displacement_multiplier,
                )

        except BaseException as Err:
            self.report({"ERROR"}, f"{Err}")

        finally:
            self.current_file_index += 1

        if self.current_file_index == len(self.new_brushes):
            self.cancel(context)
            return {"FINISHED"}

        return {"RUNNING_MODAL"}


def GetLowestAndHighestZValueInBoundBox(mesh_object):
    bpy.context.object.matrix_world

    bound_corners_worldspace = [
        mesh_object.matrix_world @ Vector(corner) for corner in mesh_object.bound_box
    ]

    lowest_value = 0.0
    highest_value = 0.0
    for vector in bound_corners_worldspace:
        value = vector[2]
        if value > highest_value:
            highest_value = value
        if value < lowest_value:
            lowest_value = value

    return lowest_value, highest_value


def GetLowestAndHighestZValueInMeshes(mesh_objects):
    lowest_value = 0.0
    highest_value = 0.0
    for mesh_object in mesh_objects:
        lowest_mesh_value, highest_mesh_value = GetLowestAndHighestZValueInBoundBox(
            mesh_object
        )

        if highest_mesh_value > highest_value:
            highest_value = highest_mesh_value
        if lowest_mesh_value < lowest_value:
            lowest_value = lowest_mesh_value

    return lowest_value, highest_value


# from https://stackoverflow.com/questions/1969240/mapping-a-range-of-values-to-another


def MapRange(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    valueScaled = 0
    # Convert the left range into a 0-1 range (float)
    if leftSpan > 0:
        valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


def ResetTemporaryAddonData():
    addon_data = GetAddonData()

    addon_data.current_edited_brush = -1
    addon_data.current_canvas_mesh = None
    addon_data.draft_brush_name = ""


def ReturnToNormalWorkspaceAndScene():
    addon_data = GetAddonData()

    if addon_data.default_scene:
        bpy.context.window.scene = addon_data.default_scene
    if (
            addon_data.default_workspace
            and addon_data.default_scene.SculptBrushEditorDedicatedWorkspace
    ):
        bpy.context.window.workspace = addon_data.default_workspace


def render_heightmap(addon_data, new_brush_name):
    # Image
    fileformat = "PNG"
    fileextension = "png"
    scene = addon_data.editor_scene
    if bpy.app.version >= (4, 2, 0) and bpy.app.version < (5, 0, 0):
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = get_addon_prefs().render_samples
    scene.render.image_settings.file_format = fileformat
    scene.render.image_settings.color_mode = "BW"
    scene.render.image_settings.color_depth = get_addon_prefs().heightmap_color_depth
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Raw"
    scene.render.filepath = GetOutputPath(new_brush_name, is_relative=True)
    scene.camera = GetBrushHeightmapRenderCamera()

    if bpy.app.version < (5, 0, 0):
        scene.node_tree.nodes["PreviewPass"].mute = True
        scene.node_tree.nodes["MistPass"].mute = True
        scene.node_tree.nodes["MistPass"].mute = False
    else:
        scene.compositing_node_group = GetCompositingNodeGroup("Heightmap", scene)

    resolution_preference = get_addon_prefs().default_texture_resolution_height
    render_resolution = int(resolution_preference)

    addon_data.editor_scene.render.resolution_percentage = 100
    addon_data.editor_scene.render.resolution_x = render_resolution
    addon_data.editor_scene.render.resolution_y = render_resolution

    bpy.ops.render.render(write_still=True, scene=scene.name)
    rendered_heightmap = bpy.data.images.load(
        bpy.context.scene.render.filepath + "." + fileextension
    )
    rendered_heightmap.colorspace_settings.is_data = True
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Filmic"
    addon_data.editor_scene.render.resolution_x = 1024
    addon_data.editor_scene.render.resolution_y = 1024

    return rendered_heightmap


def render_vdm(addon_data, new_brush_name):
    vdm_bake_material = GetVDMBakeMaterial()
    sculpt_plane = addon_data.current_canvas_mesh
    scene = addon_data.editor_scene

    scene.render.engine = "CYCLES"
    scene.cycles.samples = get_addon_prefs().render_samples
    scene.cycles.use_denoising = False
    scene.cycles.device = "GPU"

    sculpt_plane.data.materials.clear()
    sculpt_plane.data.materials.append(vdm_bake_material)
    sculpt_plane.location = Vector([0, 0, 0])
    sculpt_plane.rotation_euler = (0, 0, 0)

    vdm_texture_node = vdm_bake_material.node_tree.nodes["VDMTexture"]
    resolution_preference = get_addon_prefs().default_texture_resolution_vdm
    render_resolution = int(resolution_preference)

    # Bake
    bpy.ops.object.select_all(action="DESELECT")
    sculpt_plane.select_set(True)
    set_vdm_scene_image_settings(scene)
    output_path = GetOutputPath(f"{new_brush_name}.exr", is_relative=True)
    vdm_texture_image = bpy.data.images.new(
        name=new_brush_name,
        width=render_resolution,
        height=render_resolution,
        alpha=False,
        float_buffer=True,
    )
    vdm_bake_material.node_tree.nodes.active = vdm_texture_node
    vdm_texture_node.image = vdm_texture_image
    vdm_texture_node.select = True

    vdm_texture_image.filepath_raw = output_path
    vdm_texture_image.use_generated_float = True
    vdm_texture_image.colorspace_settings.is_data = True

    bpy.ops.object.bake(type="EMIT")

    # save as render so we have more control over compression settings
    vdm_texture_image.save_render(
        filepath=GetOutputPath(f"{new_brush_name}.exr", is_relative=False), scene=scene
    )
    vdm_texture_image.pack()  # Remove dirty flag
    vdm_texture_image.unpack(method="REMOVE")

    return vdm_texture_image


def render_preview_image(
        addon_data,
        new_brush_name,
        new_brush,
        lowest_value,
        highest_value,
        brush_image,
        displacement_multiplier=1.0,
):
    scene = addon_data.editor_scene
    HideAllMeshesForRenderAndViewport()

    preview_path = GetOutputPath(f"{new_brush_name}_preview", is_relative=True)
    scene.render.filepath = preview_path
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.display.shading.color_type = "VERTEX"

    node_tree = None
    if bpy.app.version < (5, 0, 0):
        node_tree = scene.node_tree
        scene.world.use_nodes = False
        scene.world.color = get_addon_prefs().preview_world_color
        node_tree.nodes["MistPass"].mute = True
        node_tree.nodes["PreviewPass"].mute = True
        node_tree.nodes["PreviewPass"].mute = False
    else:
        scene.compositing_node_group = GetCompositingNodeGroup("BrushPreview", scene)

    GetBrushHeightmapRenderCamera().hide_viewport = True
    collections = scene.view_layers[0].layer_collection.children
    if collections.find("BrushEditing") > -1:
        collections["BrushEditing"].exclude = True
    set_preview_collections(addon_data, False)
    collections = addon_data.editor_scene.view_layers[0].layer_collection.children
    if collections.find(f"BrushPreview{addon_data.current_preview_type}"):
        collections[f"BrushPreview{addon_data.current_preview_type}"].exclude = False

    # Get camera settings
    scene.camera = GetBrushPreviewRenderCamera()
    brush_render_camera = scene.camera
    height = highest_value  # - lowest_value
    if addon_data.current_preview_type == "Sphere":
        if height > 0.5:
            brush_render_camera.data.lens = 115.0 - 65.0 * min(height / 2.0, 1.0)
        else:
            brush_render_camera.data.lens = 115.0
    if addon_data.current_preview_type == "Tilted":
        if height > 0.5:
            brush_render_camera.data.lens = 90.0 - 40.0 * min(height / 3.0, 1.0)
            brush_render_camera.data.shift_x = 0.2 * min(height / 3.0, 1.0)
            brush_render_camera.data.shift_y = 0.2 * min(height / 3.0, 1.0)
        else:
            brush_render_camera.data.lens = 90.0
            brush_render_camera.data.shift_x = 0.0
            brush_render_camera.data.shift_y = 0.0

    preview_object = None
    if addon_data.current_preview_type == "Sphere":
        if addon_data.editor_scene.objects.find("PreviewSphere") != -1:
            preview_object = addon_data.editor_scene.objects["PreviewSphere"]
    else:
        if addon_data.editor_scene.objects.find("PreviewPlane") != -1:
            preview_object = addon_data.editor_scene.objects["PreviewPlane"]

    if preview_object is not None:
        preview_object.hide_render = False
        preview_object.modifiers["TextureDisplacement"]["Input_2"] = brush_image
        preview_object.modifiers["TextureDisplacement"][
            "Input_5"
        ] = new_brush.use_color_as_displacement
        preview_object.modifiers["TextureDisplacement"]["Input_7"][2] = math.pow(
            new_brush.strength * displacement_multiplier, 2
        )
        preview_object.modifiers["TextureDisplacement"][
            "Input_8"
        ] = new_brush.texture_sample_bias
        preview_object.rotation_euler[2] = -addon_data.preview_rotation

    scene.render.resolution_x = 256
    scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100

    scene.render.image_settings.file_format = "PNG"

    if bpy.app.version >= (5, 0, 0):
        scene.render.film_transparent = True
        scene.render.image_settings.color_mode = "RGBA"
        if get_addon_prefs().use_transparent_preview_background:
            scene.compositing_node_group.nodes["Color"].outputs[0].default_value = (
                1.0,
                1.0,
                1.0,
                0.0,
            )
        else:
            scene.compositing_node_group.nodes["Color"].outputs[0].default_value = (
                *get_addon_prefs().preview_world_color,
                1.0,
            )
    elif get_addon_prefs().use_transparent_preview_background:
        scene.render.film_transparent = True
        scene.render.image_settings.color_mode = "RGBA"
    else:
        scene.render.film_transparent = False
        scene.render.image_settings.color_mode = "RGB"

    scene.render.image_settings.color_depth = "8"

    # Render
    bpy.ops.render.render(write_still=True, scene=scene.name)
    # ------

    if bpy.app.version < (5, 0, 0):
        node_tree.nodes["PreviewPass"].mute = True
        node_tree.nodes["MistPass"].mute = False

    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.image_settings.color_mode = "BW"
    scene.render.image_settings.color_depth = "16"

    if bpy.app.version < (5, 0, 0):
        new_brush.use_custom_icon = True
        new_brush.icon_filepath = preview_path + ".png"

    if bpy.app.version >= (4, 3, 0):
        new_brush.asset_mark()
        with bpy.context.temp_override(id=new_brush):
            bpy.ops.ed.lib_id_load_custom_preview(
                filepath=bpy.path.abspath(preview_path + ".png")
            )


def get_heightmap_bias_and_strength(addon_data, lowest_value, highest_value):
    render_camera = GetBrushHeightmapRenderCamera()
    remapped_shifting_value = 0
    brush_strength = 1.0

    if addon_data.limit_z_sample_start:
        lowest_value = max(addon_data.min_z_sample, lowest_value)

    if addon_data.limit_z_sample_end:
        highest_value = min(addon_data.max_z_sample, highest_value)
    if addon_data.use_map_range_zero_to_one:
        render_camera.location.z = highest_value + 1.0

        addon_data.editor_scene.world.mist_settings.start = 1.0
        depth = highest_value - lowest_value
        addon_data.editor_scene.world.mist_settings.depth = depth
        brush_strength = math.sqrt(depth)

        remapped_shifting_value = MapRange(0, lowest_value, highest_value, 0, 1.0)
    else:
        real_depth = highest_value - lowest_value
        if real_depth > 1.0:
            # Strengths work exponentially..
            brush_strength = math.sqrt(real_depth)
        depth = max(real_depth, 1.0)
        addon_data.editor_scene.world.mist_settings.depth = depth
        addon_data.editor_scene.world.mist_settings.start = 1.0
        render_camera.location.z = lowest_value + depth + 1.0

        remapped_shifting_value = MapRange(
            0, lowest_value, lowest_value + depth, 0, 1.0
        )

    return brush_strength, remapped_shifting_value


def make_new_brush_and_texture(reference_brush_name, new_brush_name):
    addon_data = GetAddonData()

    # Make new brush beforehand while we're still in sculpt mode (Needed to set map mode to area plane..)
    new_brush: bpy.types.Brush = None
    if reference_brush_name in bpy.data.brushes:
        new_brush = bpy.data.brushes[reference_brush_name]
    else:
        new_brush = bpy.data.brushes.new(name=new_brush_name, mode="SCULPT")
        new_brush.stroke_method = "ANCHORED"
        if bpy.context.active_object and bpy.context.active_object.mode == "SCULPT":
            new_brush.texture_slot.map_mode = "AREA_PLANE"
        new_brush.hardness = 0.9

    # Texture
    brush_texture: bpy.types.Texture = None
    if reference_brush_name in bpy.data.textures:
        brush_texture = bpy.data.textures[reference_brush_name]
    else:
        brush_texture = bpy.data.textures.new(name=new_brush_name, type="IMAGE")
    brush_texture.extension = "EXTEND"
    brush_texture.use_clamp = False  # Remain negative values
    brush_texture.name = new_brush_name

    # Set brush settings
    new_brush.texture = brush_texture
    new_brush.name = new_brush_name

    custom_brush_data = None
    for brush_data in addon_data.brush_collection:
        if reference_brush_name == brush_data.brush_name:
            custom_brush_data = brush_data
            break
    if custom_brush_data is None:
        custom_brush_data = addon_data.brush_collection.add()
    custom_brush_data.brush_name = new_brush_name
    custom_brush_data.brush = new_brush
    custom_brush_data.texture = brush_texture
    custom_brush_data.is_loaded_image_brush = False

    return new_brush, brush_texture, custom_brush_data


class CloseBrushMapEditorAndSave(bpy.types.Operator):
    bl_idname = "texturemap.saveandcloseeditor"
    bl_label = "Close brush editor"
    bl_description = "Creates the texture map from your sculpture, creates a brush with it and returns to old scene and workspace"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        addon_data = GetAddonData()
        new_brush_name = addon_data.draft_brush_name
        reference_brush_name = addon_data.draft_brush_name
        if addon_data.current_edited_brush > -1:
            reference_brush_name = addon_data.brush_collection[
                addon_data.current_edited_brush
            ].brush_name

        # Make new brush beforehand while we're still in sculpt mode (Needed to set map mode to area plane..)
        new_brush, brush_texture, custom_brush_data = make_new_brush_and_texture(
            reference_brush_name, new_brush_name
        )

        bpy.ops.object.mode_set(mode="OBJECT")

        # Save default settings
        default_render_engine = addon_data.editor_scene.render.engine
        default_view_transform = addon_data.editor_scene.view_settings.view_transform
        default_display_device = addon_data.editor_scene.display_settings.display_device
        default_file_format = addon_data.editor_scene.render.image_settings.file_format
        default_color_mode = addon_data.editor_scene.render.image_settings.color_mode
        default_codec = addon_data.editor_scene.render.image_settings.exr_codec
        default_denoise = addon_data.editor_scene.cycles.use_denoising
        default_compute_device = addon_data.editor_scene.cycles.device
        default_scene_samples = addon_data.editor_scene.cycles.samples
        default_eevee_samples = addon_data.editor_scene.eevee.taa_render_samples

        try:
            old_image_name = f"{reference_brush_name}"
            if old_image_name in bpy.data.images:
                oldimage = bpy.data.images[old_image_name]
                name = oldimage.name + "_original"
                if oldimage.has_data:
                    if name not in bpy.data.images:
                        oldimage.name = name
                        extension = (
                            "exr" if oldimage.file_format == "OPEN_EXR" else "png"
                        )
                        oldimage.filepath_raw = GetOutputPath(
                            filename=f"{name}.{extension}", is_relative=True
                        )
                        oldimage.save()
                    else:
                        oldimage.name = "Old brush texture"
            # bpy.data.images.remove(bpy.data.images[old_image_name])  # Removing images directly can lead to crashes!

            visible_meshes_viewport, visible_meshes_in_render = GetVisibleMeshes()
            lowest_value, highest_value = GetLowestAndHighestZValueInMeshes(
                visible_meshes_in_render
            )

            remapped_shifting_value = 0  # remapped to texture value [0;1]
            brush_strength = 1.0
            brush_image = None
            if addon_data.current_brush_texture_type == "Height Displacement":
                brush_strength, remapped_shifting_value = (
                    get_heightmap_bias_and_strength(
                        addon_data, lowest_value, highest_value
                    )
                )
                brush_image = render_heightmap(addon_data, new_brush_name)
            else:
                brush_image = render_vdm(addon_data, new_brush_name)

            brush_texture.image = brush_image
            new_brush.use_color_as_displacement = (
                    addon_data.current_brush_texture_type == "Vector Displacement"
            )
            new_brush.texture_sample_bias = remapped_shifting_value
            new_brush.strength = brush_strength
            new_brush.hardness = get_addon_prefs().default_brush_hardness

            # Preview image
            if addon_data.create_preview_image:
                render_preview_image(
                    addon_data,
                    new_brush_name,
                    new_brush,
                    lowest_value,
                    highest_value,
                    brush_image,
                )

            custom_brush_data.image = brush_texture.image
            custom_brush_data.brush_texture_type = addon_data.current_brush_texture_type
            custom_brush_data.preview_type = addon_data.current_preview_type
            custom_brush_data.preview_rotation = addon_data.preview_rotation

            custom_brush_data.objects_used_for_rendering.clear()
            for visible_mesh_in_render in visible_meshes_in_render:
                added_mesh = custom_brush_data.objects_used_for_rendering.add()
                # Could be wrong if some collections are disabled
                added_mesh.mesh_object = visible_mesh_in_render
            custom_brush_data.sample_bias = remapped_shifting_value
            custom_brush_data.canvas_mesh = addon_data.current_canvas_mesh
            custom_brush_data.brush_strength = brush_strength

        finally:
            addon_data.editor_scene.render.image_settings.file_format = (
                default_file_format
            )
            addon_data.editor_scene.render.image_settings.color_mode = (
                default_color_mode
            )
            addon_data.editor_scene.render.image_settings.exr_codec = default_codec
            addon_data.editor_scene.cycles.samples = default_scene_samples
            addon_data.editor_scene.eevee.taa_render_samples = default_eevee_samples
            addon_data.editor_scene.display_settings.display_device = (
                default_display_device
            )
            addon_data.editor_scene.view_settings.view_transform = (
                default_view_transform
            )
            addon_data.editor_scene.cycles.use_denoising = default_denoise
            addon_data.editor_scene.cycles.device = default_compute_device
            addon_data.editor_scene.render.engine = default_render_engine

        ReturnToNormalWorkspaceAndScene()
        ResetTemporaryAddonData()

        if bpy.context.active_object and bpy.context.active_object.mode == "SCULPT":
            ChangeBrush(new_brush)

        return {"FINISHED"}


class ResetSampleBias(bpy.types.Operator):
    bl_idname = "texturemap.resetsamplebias"
    bl_label = "Reset sample bias"
    bl_description = (
        "Resets the sample bias of the brush to the value that was set on creation"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        index, brush_data = GetCustomBrushDataFromBrush(
            context.tool_settings.sculpt.brush
        )
        return brush_data is not None

    def execute(self, context):
        addon_data = GetAddonData()

        index, brush_data = GetCustomBrushDataFromBrush(
            context.tool_settings.sculpt.brush
        )

        if brush_data:
            context.tool_settings.sculpt.brush.texture_sample_bias = (
                brush_data.sample_bias
            )

        return {"FINISHED"}


class ResetBrushStrength(bpy.types.Operator):
    bl_idname = "texturemap.resetbrushstrength"
    bl_label = "Reset brush strength"
    bl_description = "Resets the brush strength to the value that was set on creation"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        index, brush_data = GetCustomBrushDataFromBrush(
            context.tool_settings.sculpt.brush
        )
        return brush_data is not None

    def execute(self, context):
        addon_data = GetAddonData()

        index, brush_data = GetCustomBrushDataFromBrush(
            context.tool_settings.sculpt.brush
        )

        if brush_data:
            context.tool_settings.sculpt.brush.strength = brush_data.brush_strength

        return {"FINISHED"}


class CloseBrushMapEditorWithoutSave(bpy.types.Operator):
    bl_idname = "texturemap.closeeditor"
    bl_label = "Close brush editor"
    bl_description = "Returns to old scene and workspace"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        ReturnToNormalWorkspaceAndScene()
        ResetTemporaryAddonData()

        return {"FINISHED"}


registered_classes = [
    BrushImportSettings,
    SculptBrushTextureEditorPreferences,
    BrushComponent,
    CustomMadeBrush,
    EDITOR_PT_TextureMapBrush,
    OpenBrushMapEditor,
    SculptBrushEditorAddonData,
    CloseBrushMapEditorAndSave,
    CloseBrushMapEditorWithoutSave,
    ResetSampleBias,
    ResetBrushStrength,
    LoadBrushesModal,
    OT_TexturesFilebrowser,
    RerenderPreviewImages,
]


def register():
    global AddonDirectory
    script_file = os.path.realpath(__file__)
    AddonDirectory = os.path.dirname(script_file)

    for registered_class in registered_classes:
        bpy.utils.register_class(registered_class)

    bpy.types.Object.SculptBrushEditorData = bpy.props.PointerProperty(
        type=SculptBrushEditorAddonData
    )
    bpy.types.Scene.SculptBrushEditorDedicatedWorkspace = bpy.props.BoolProperty(
        name="Open dedicated workspace", default=True
    )
    bpy.types.Scene.SculptBrushEditorDataFakeUser = bpy.props.PointerProperty(
        type=bpy.types.Object
    )  # Keeping the data storage alive


def unregister():
    for registered_class in registered_classes:
        bpy.utils.unregister_class(registered_class)

    del bpy.types.Scene.SculptBrushEditorDataFakeUser
    del bpy.types.Scene.SculptBrushEditorDedicatedWorkspace
    del bpy.types.Object.SculptBrushEditorData
