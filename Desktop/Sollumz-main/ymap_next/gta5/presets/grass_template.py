"""Grass template preset category for map grass batches.

Captures the per-template settings (lod distances, spawn weight, orient-to-
terrain factor) of the currently active grass template inside the active
grass batch.
"""

from pathlib import Path

import bpy

from ....shared.presets import (
    PresetCategory,
    PresetDeleteOperatorBase,
    PresetLoadOperatorBase,
    PresetPanel,
    PresetSaveOperatorBase,
    make_get_targets_from_collection,
    register_preset_category,
)
from ...context import active_grass_template, active_grass_templates_collection


def _poll(context):
    if active_grass_template(context) is None:
        return False, "Select a grass template."
    return True, ""


GRASS_TEMPLATE_PRESET_CATEGORY = PresetCategory(
    id="grass_template",
    label="Grass Template",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "grass_template_presets.json",
    get_target=active_grass_template,
    get_targets=make_get_targets_from_collection(active_grass_templates_collection),
    poll=_poll,
)


register_preset_category(GRASS_TEMPLATE_PRESET_CATEGORY)


class SOLLUMZ_OT_save_grass_template_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_grass_template_preset"
    bl_label = "保存草模板预设"
    bl_description = "将当前草模板设置保存为命名预设"
    category = GRASS_TEMPLATE_PRESET_CATEGORY


class SOLLUMZ_OT_load_grass_template_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_grass_template_preset"
    bl_label = "应用草模板预设"
    bl_description = "应用已保存的草模板预设"
    category = GRASS_TEMPLATE_PRESET_CATEGORY


class SOLLUMZ_OT_delete_grass_template_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_grass_template_preset"
    bl_label = "删除草模板预设"
    bl_description = "移除已保存的草模板预设"
    category = GRASS_TEMPLATE_PRESET_CATEGORY


class SOLLUMZ_PT_grass_template_presets(PresetPanel, bpy.types.Panel):
    bl_label = "草模板预设"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = GRASS_TEMPLATE_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_grass_template_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_grass_template_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_grass_template_preset.bl_idname
