"""MLO rooms preset category."""
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
from ...utils import get_selected_room, get_selected_rooms_collection


def _poll(context):
    if get_selected_room(context) is None:
        return False, "Select a room."
    return True, ""


MLO_ROOM_PRESET_CATEGORY = PresetCategory(
    id="mlo_room",
    label="房间",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "mlo_room_presets.json",
    get_target=get_selected_room,
    get_targets=make_get_targets_from_collection(get_selected_rooms_collection),
    poll=_poll,
)


register_preset_category(MLO_ROOM_PRESET_CATEGORY)


class SOLLUMZ_OT_save_mlo_room_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_mlo_room_preset"
    bl_label = "保存房间预设"
    bl_description = "将当前房间属性保存为命名预设"
    category = MLO_ROOM_PRESET_CATEGORY


class SOLLUMZ_OT_load_mlo_room_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_mlo_room_preset"
    bl_label = "应用房间预设"
    bl_description = "将已保存的房间预设应用到活动房间"
    category = MLO_ROOM_PRESET_CATEGORY


class SOLLUMZ_OT_delete_mlo_room_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_mlo_room_preset"
    bl_label = "删除房间预设"
    bl_description = "移除已保存的房间预设"
    category = MLO_ROOM_PRESET_CATEGORY


class SOLLUMZ_PT_mlo_room_presets(PresetPanel, bpy.types.Panel):
    bl_label = "房间预设"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = MLO_ROOM_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_mlo_room_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_mlo_room_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_mlo_room_preset.bl_idname
