"""
preview_renderer.py
-------------------
Render-based brush asset preview generation.

Produces previews by displacing a pre-built sphere or plane mesh with the
brush texture via a Geometry Nodes modifier, rendering with Workbench, and
loading the result as the brush asset icon via lib_id_load_custom_preview.

The editor scene is loaded once from SETUP_BLEND_FILE (lazy init) and kept
in bpy.data.scenes for the session.  The active window scene is NEVER changed,
so the user's viewport is unaffected throughout.

Dependencies
------------
Two blend files must live alongside this file in the addon directory:

  BrushEditorSetup.blend                 - editor scene, preview meshes, cameras,
                                           TextureDisplacement node group
  BrushEditor_5_0_CompositingNodes.blend - Blender 5+ compositing node groups
                                           (BrushPreview, Heightmap)
"""

import os
import bpy
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SETUP_BLEND_FILE        = "BrushEditorSetup.blend"
COMPOSITING_BLEND_FILE  = "BrushEditor_5_0_CompositingNodes.blend"

_ADDON_DIR          = Path(__file__).parent
_EDITOR_SCENE_NAME  = "BrushEditScene"

# Collections expected inside the editor scene
_PREVIEW_COLLECTIONS = ("BrushPreviewFlat", "BrushPreviewTilted", "BrushPreviewSphere")
_EDITING_COLLECTION  = "BrushEditing"

# Cached reference — append happens at most once per Blender session
_editor_scene: bpy.types.Scene | None = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Return True if both required blend files are present on disk."""
    return (
        (_ADDON_DIR / SETUP_BLEND_FILE).exists()
        and (_ADDON_DIR / COMPOSITING_BLEND_FILE).exists()
    )


def generate_preview(brush, preview_type: str = "Sphere",
                     displacement_multiplier: float = 1.0) -> bool:
    """Generate a rendered preview for *brush* and assign it as the asset icon.

    Parameters
    ----------
    brush:
        A bpy.types.Brush.  Will be asset-marked if it isn't already.
    preview_type:
        One of ``"Flat"``, ``"Tilted"``, ``"Sphere"``.
    displacement_multiplier:
        Scales the geo-nodes displacement strength used during the render.

    Returns
    -------
    bool
        True if a preview was generated and loaded successfully.
    """
    try:
        scene = _ensure_editor_scene()
    except Exception as e:
        print(f"[preview_renderer] Could not load editor scene: {e}")
        return False

    try:
        _configure_scene_for_render(scene, preview_type)
        _feed_texture_to_preview_object(brush, scene, preview_type, displacement_multiplier)

        output_path = _get_preview_output_path(brush.name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        scene.render.filepath = output_path

        bpy.ops.render.render(write_still=True, scene=scene.name)

        rendered_png = output_path + ".png"
        if not os.path.exists(rendered_png):
            print(f"[preview_renderer] Rendered file not found: {rendered_png}")
            return False

        _assign_preview_to_brush(brush, rendered_png)
        return True

    except Exception as e:
        print(f"[preview_renderer] generate_preview failed for '{brush.name}': {e}")
        return False


# ---------------------------------------------------------------------------
# Internal — scene management
# ---------------------------------------------------------------------------

def _ensure_editor_scene() -> bpy.types.Scene:
    """Return the editor scene, appending it from SETUP_BLEND_FILE if needed.

    Never switches the active window scene.
    """
    global _editor_scene

    # Return cached reference if it's still alive in bpy.data
    if _editor_scene is not None and _editor_scene.name in bpy.data.scenes:
        return _editor_scene

    # Already appended in a previous call (e.g. after a script reload)
    if _EDITOR_SCENE_NAME in bpy.data.scenes:
        _editor_scene = bpy.data.scenes[_EDITOR_SCENE_NAME]
        return _editor_scene

    # Append from blend file — does NOT switch the active window scene
    setup_blend = str(_ADDON_DIR / SETUP_BLEND_FILE)
    bpy.ops.wm.append(
        filepath=setup_blend + "/Scene/" + _EDITOR_SCENE_NAME,
        directory=setup_blend + "/Scene/",
        filename=_EDITOR_SCENE_NAME,
        link=False,
    )

    if _EDITOR_SCENE_NAME not in bpy.data.scenes:
        raise RuntimeError(
            f"Failed to append '{_EDITOR_SCENE_NAME}' from {SETUP_BLEND_FILE}. "
            "Check the blend file is valid and contains a scene with that name."
        )

    _editor_scene = bpy.data.scenes[_EDITOR_SCENE_NAME]
    return _editor_scene


def _get_compositing_node_group(name: str,
                                scene: bpy.types.Scene) -> bpy.types.NodeTree:
    """Return the named compositing node group, appending it if not present.

    Rewires the 'Render Layers' node to *scene* so the group renders the
    correct scene when assigned.
    """
    if name not in bpy.data.node_groups:
        comp_blend = str(_ADDON_DIR / COMPOSITING_BLEND_FILE)
        bpy.ops.wm.append(
            filepath=comp_blend + "/NodeTree/" + name,
            directory=comp_blend + "/NodeTree/",
            filename=name,
            link=False,
        )

    if name not in bpy.data.node_groups:
        raise RuntimeError(
            f"Failed to append node group '{name}' from {COMPOSITING_BLEND_FILE}."
        )

    node_group = bpy.data.node_groups[name]

    if "Render Layers" in node_group.nodes:
        node_group.nodes["Render Layers"].scene = scene

    node_group.use_fake_user = True
    return node_group


# ---------------------------------------------------------------------------
# Internal — per-render configuration
# ---------------------------------------------------------------------------

def _configure_scene_for_render(scene: bpy.types.Scene,
                                preview_type: str) -> None:
    """Set render engine, resolution, compositing, and collection visibility."""

    scene.render.engine = "CYCLES"
    scene.display.shading.color_type = "VERTEX"
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"

    if bpy.app.version >= (5, 0, 0):
        node_group = _get_compositing_node_group("BrushPreview", scene)
        scene.compositing_node_group = node_group
        # Set transparent background via the Color node in the compositing group
        if "Color" in node_group.nodes:
            node_group.nodes["Color"].outputs[0].default_value = (1.0, 1.0, 1.0, 0.0)
    else:
        # Blender 4.x: toggle compositor nodes in the scene node tree
        if scene.node_tree:
            for node_name in ("MistPass", "PreviewPass"):
                if node_name in scene.node_tree.nodes:
                    scene.node_tree.nodes[node_name].mute = (node_name != "PreviewPass")

    _set_render_visibility(scene, preview_type)

    camera_name = f"BrushPreviewCamera{preview_type}"
    if camera_name in scene.objects:
        scene.camera = scene.objects[camera_name]
    else:
        print(f"[preview_renderer] Camera '{camera_name}' not found in editor scene")


def _set_render_visibility(scene: bpy.types.Scene, preview_type: str) -> None:
    """Configure render visibility for a clean preview.

    Uses hide_render only — never hide_set — so the user's viewport is unaffected.
    """
    # Hide every mesh in the scene from the render
    for obj in scene.objects:
        if obj.type == 'MESH':
            obj.hide_render = True

    # Exclude all preview collections, then enable only the target one
    collections = scene.view_layers[0].layer_collection.children
    for coll_name in _PREVIEW_COLLECTIONS:
        if coll_name in collections:
            collections[coll_name].exclude = True
    if _EDITING_COLLECTION in collections:
        collections[_EDITING_COLLECTION].exclude = True

    target_coll_name = f"BrushPreview{preview_type}"
    if target_coll_name in collections:
        collections[target_coll_name].exclude = False

    # Show the specific preview object
    obj_name = "PreviewSphere" if preview_type == "Sphere" else "PreviewPlane"
    if obj_name in scene.objects:
        scene.objects[obj_name].hide_render = False
    else:
        print(f"[preview_renderer] Preview object '{obj_name}' not found in editor scene")


def _feed_texture_to_preview_object(brush, scene: bpy.types.Scene,
                                    preview_type: str,
                                    displacement_multiplier: float) -> None:
    """Wire the brush texture image into the TextureDisplacement geo-nodes modifier."""
    obj_name = "PreviewSphere" if preview_type == "Sphere" else "PreviewPlane"
    if obj_name not in scene.objects:
        return

    preview_obj = scene.objects[obj_name]
    if "TextureDisplacement" not in preview_obj.modifiers:
        print(f"[preview_renderer] 'TextureDisplacement' modifier not found on '{obj_name}'")
        return

    mod = preview_obj.modifiers["TextureDisplacement"]

    if brush.texture and brush.texture.image:
        mod["Input_2"] = brush.texture.image

    mod["Input_5"] = getattr(brush, 'use_color_as_displacement', False)

    strength  = brush.strength * displacement_multiplier
    mod["Input_7"][2] = strength * strength          # matches alt.py: math.pow(strength, 2)

    if hasattr(brush, 'texture_sample_bias'):
        mod["Input_8"] = brush.texture_sample_bias


# ---------------------------------------------------------------------------
# Internal — preview assignment
# ---------------------------------------------------------------------------

def _assign_preview_to_brush(brush, png_path: str) -> None:
    """Load *png_path* as the brush asset icon."""
    if brush.asset_data is None:
        brush.asset_mark()

    # Viewport toolbar icon (Blender 4.x and below)
    if hasattr(brush, 'use_custom_icon'):
        brush.use_custom_icon = True
        brush.icon_filepath = png_path

    # Asset Browser preview (Blender 4.3+)
    if bpy.app.version >= (4, 3, 0):
        window = bpy.context.window_manager.windows[0]
        with bpy.context.temp_override(window=window, id=brush):
            result = bpy.ops.ed.lib_id_load_custom_preview(filepath=png_path)
        if 'FINISHED' not in result:
            print(f"[preview_renderer] lib_id_load_custom_preview returned {result} "
                  f"for '{brush.name}'")


# ---------------------------------------------------------------------------
# Internal — output path
# ---------------------------------------------------------------------------

def _get_preview_output_path(brush_name: str) -> str:
    """Return an absolute output path (without extension) for the preview PNG."""
    if bpy.data.is_saved:
        base = os.path.join(os.path.dirname(bpy.data.filepath), "brush_previews")
    else:
        base = os.path.join(bpy.app.tempdir, "brush_previews")

    safe_name = "".join(c if (c.isalnum() or c in '_-') else '_' for c in brush_name)
    return os.path.join(base, safe_name)
