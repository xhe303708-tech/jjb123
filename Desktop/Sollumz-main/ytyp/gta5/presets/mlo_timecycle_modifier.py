"""MLO timecycle modifier preset operators + panel.
Presets shared with map timecycle modifiers.
"""
import bpy

from ....shared.presets import (
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
    make_get_targets_from_collection,
)
from ....ymap_next.gta5.presets.timecycle_modifier import TIMECYCLE_MODIFIER_PRESET_CATEGORY
from ...utils import get_selected_tcm, get_selected_tcms_collection


class SOLLUMZ_OT_save_mlo_timecycle_modifier_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_mlo_timecycle_modifier_preset"
    bl_label = "保存时间周期修改器预设"
    bl_description = "将当前时间周期修改器属性保存为命名预设"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY
    get_target = get_selected_tcm

    @classmethod
    def poll(cls, context):
        if get_selected_tcm(context) is None:
            cls.poll_message_set("Select a timecycle modifier.")
            return False
        return True


class SOLLUMZ_OT_load_mlo_timecycle_modifier_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_mlo_timecycle_modifier_preset"
    bl_label = "应用时间周期修改器预设"
    bl_description = "应用已保存的时间周期修改器预设"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY
    get_target = get_selected_tcm
    get_targets = make_get_targets_from_collection(get_selected_tcms_collection)

    @classmethod
    def poll(cls, context):
        if get_selected_tcm(context) is None:
            cls.poll_message_set("Select a timecycle modifier.")
            return False
        return True


class SOLLUMZ_OT_delete_mlo_timecycle_modifier_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_mlo_timecycle_modifier_preset"
    bl_label = "删除时间周期修改器预设"
    bl_description = "移除已保存的时间周期修改器预设"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY


class SOLLUMZ_PT_mlo_timecycle_modifier_presets(PresetPanel, bpy.types.Panel):
    bl_label = "时间周期修改器预设"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_mlo_timecycle_modifier_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_mlo_timecycle_modifier_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_mlo_timecycle_modifier_preset.bl_idname
