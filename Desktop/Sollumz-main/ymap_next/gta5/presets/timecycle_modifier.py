"""Timecycle modifier preset category for map timecycle modifiers."""

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
from ...context import active_tcm, active_tcms_collection


def _poll(context):
    if active_tcm(context) is None:
        return False, "Select a timecycle modifier."
    return True, ""


TIMECYCLE_MODIFIER_PRESET_CATEGORY = PresetCategory(
    id="timecycle_modifier",
    label="时间周期修改器",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "timecycle_modifier_presets.json",
    get_target=active_tcm,
    get_targets=make_get_targets_from_collection(active_tcms_collection),
    poll=_poll,
)


register_preset_category(TIMECYCLE_MODIFIER_PRESET_CATEGORY)


class SOLLUMZ_OT_save_timecycle_modifier_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_timecycle_modifier_preset"
    bl_label = "保存时间周期修改器预设"
    bl_description = "将当前时间周期修改器属性保存为命名预设"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY


class SOLLUMZ_OT_load_timecycle_modifier_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_timecycle_modifier_preset"
    bl_label = "应用时间周期修改器预设"
    bl_description = "应用已保存的时间周期修改器预设"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY


class SOLLUMZ_OT_delete_timecycle_modifier_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_timecycle_modifier_preset"
    bl_label = "删除时间周期修改器预设"
    bl_description = "移除已保存的时间周期修改器预设"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY


class SOLLUMZ_PT_timecycle_modifier_presets(PresetPanel, bpy.types.Panel):
    bl_label = "时间周期修改器预设"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_timecycle_modifier_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_timecycle_modifier_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_timecycle_modifier_preset.bl_idname
