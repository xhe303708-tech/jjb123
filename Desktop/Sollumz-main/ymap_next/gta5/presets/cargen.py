"""Car generator preset category for map cargens."""

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
from ...context import active_cargen, active_cargens_collection

# Per-instance / display fields skipped from templating.
_SKIP_FIELDS = (
    "name",
    "ui_label",
    "linked_collection",
    "uuid",
    "uuid_str",
    "map_group_uuid",
    "map_data_uuid",
    "map_data_name",
)


def _poll(context):
    if active_cargen(context) is None:
        return False, "Select a car generator."
    return True, ""


CARGEN_PRESET_CATEGORY = PresetCategory(
    id="cargen",
    label="载具生成器",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "cargen_presets.json",
    skip=_SKIP_FIELDS,
    get_target=active_cargen,
    get_targets=make_get_targets_from_collection(active_cargens_collection),
    poll=_poll,
)


register_preset_category(CARGEN_PRESET_CATEGORY)


class SOLLUMZ_OT_save_cargen_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_cargen_preset"
    bl_label = "保存载具生成器预设"
    bl_description = "将当前载具生成器属性保存为命名预设"
    category = CARGEN_PRESET_CATEGORY


class SOLLUMZ_OT_load_cargen_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_cargen_preset"
    bl_label = "应用载具生成器预设"
    bl_description = "应用已保存的载具生成器预设"
    category = CARGEN_PRESET_CATEGORY


class SOLLUMZ_OT_delete_cargen_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_cargen_preset"
    bl_label = "删除载具生成器预设"
    bl_description = "移除已保存的载具生成器预设"
    category = CARGEN_PRESET_CATEGORY


class SOLLUMZ_PT_cargen_presets(PresetPanel, bpy.types.Panel):
    bl_label = "载具生成器预设"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = CARGEN_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_cargen_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_cargen_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_cargen_preset.bl_idname
