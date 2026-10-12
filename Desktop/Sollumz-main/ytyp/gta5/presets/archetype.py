"""Archetype preset category."""
import bpy
from pathlib import Path

from ....shared.presets import (
    PresetCategory,
    register_preset_category,
    make_get_targets_from_collection,
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
)
from ...utils import get_selected_archetype, get_selected_archetypes_collection


def _poll(context):
    if get_selected_archetype(context) is None:
        return False, "Select an archetype."
    return True, ""


ARCHETYPE_PRESET_CATEGORY = PresetCategory(
    id="archetype",
    label="架构",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "archetype_presets.json",
    get_target=get_selected_archetype,
    get_targets=make_get_targets_from_collection(get_selected_archetypes_collection),
    poll=_poll,
)


register_preset_category(ARCHETYPE_PRESET_CATEGORY)


class SOLLUMZ_OT_save_archetype_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_archetype_preset"
    bl_label = "保存架构预设"
    bl_description = "将当前架构属性保存为命名预设"
    category = ARCHETYPE_PRESET_CATEGORY


class SOLLUMZ_OT_load_archetype_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_archetype_preset"
    bl_label = "应用架构预设"
    bl_description = "将已保存的架构预设应用到活动架构"
    category = ARCHETYPE_PRESET_CATEGORY


class SOLLUMZ_OT_delete_archetype_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_archetype_preset"
    bl_label = "删除架构预设"
    bl_description = "移除已保存的架构预设"
    category = ARCHETYPE_PRESET_CATEGORY


class SOLLUMZ_PT_archetype_presets(PresetPanel, bpy.types.Panel):
    bl_label = "架构预设"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = ARCHETYPE_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_archetype_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_archetype_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_archetype_preset.bl_idname
