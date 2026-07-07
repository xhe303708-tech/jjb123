import bpy
from bpy.types import (
    bpy_struct,
    bpy_prop_array,
    bpy_prop_collection,
    PropertyGroup,
    Operator,
    UIList,
    UILayout,
    AddonPreferences,
    Menu,
)
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty,
    FloatVectorProperty,
    FloatProperty,
)
from bpy_extras.io_utils import ImportHelper
import rna_keymap_ui
import os
import ast
import textwrap
import traceback
from typing import Optional, Any, TYPE_CHECKING
from configparser import ConfigParser
from pathlib import Path
from .known_paths import prefs_file_path, data_directory_path
from .dependencies import IS_SZIO_NATIVE_AVAILABLE, PYMATERIA_REQUIRED_MSG
if TYPE_CHECKING:
    from .iecontext import ImportSettings, ExportSettings


# Set while preferences are being loaded from disk so the property update callbacks don't trigger a
# redundant save (and full-file rewrite) for every property being loaded. See `_load_preferences`.
_is_loading_preferences = False


def _save_preferences_on_update(self, context):
    _save_preferences()


def _on_update_thunk(self, context):
    # Thunk to allow to override the callback
    if cb := getattr(self, "_on_update", None):
        cb(context)


class ExportSettingsBase:
    def _on_update(self, context):
        ...

    target_formats: bpy.props.EnumProperty(
        name="目标格式",
        description="导出时使用的输出格式",
        items=(
            (
                "NATIVE", "原生",
                "二进制资源格式。游戏原生格式，可直接使用" +
                ("" if IS_SZIO_NATIVE_AVAILABLE else "。\n\n" + PYMATERIA_REQUIRED_MSG),
                1
            ),
            (
                "CWXML", "CW XML",
                "CodeWalker XML 格式。可读的文本格式，但需要通过 CodeWalker 导入后才能被游戏使用",
                2
            ),
        ),
        default={"NATIVE", "CWXML"},
        options={"ENUM_FLAG"},
        update=_on_update_thunk,
    )

    target_versions: bpy.props.EnumProperty(
        name="目标游戏版本",
        description=(
            "要导出的游戏版本。如果两者都启用，文件将分别放在 'gen8/' 和 'gen9/' 子目录中"
        ),
        items=(
            ("GEN8", "Gen8", "GTAV 旧版", 1),
            ("GEN9", "Gen9", "GTAV 增强版", 2),
        ),
        default={"GEN8", "GEN9"},
        options={"ENUM_FLAG"},
        update=_on_update_thunk,
    )

    limit_to_selected: BoolProperty(
        name="限制为已选中",
        description="仅导出已选中且可见的对象",
        default=True,
        update=_on_update_thunk,
    )

    exclude_skeleton: BoolProperty(
        name="排除骨骼",
        description="导出时排除骨骼。通常用于 MP 角色组件",
        default=False,
        update=_on_update_thunk,
    )

    ymap_exclude_entities: BoolProperty(
        name="（已弃用）排除实体",
        description="启用后，将忽略所选 ymap 中的所有实体",
        default=False,
        update=_on_update_thunk,
    )

    ymap_box_occluders: BoolProperty(
        name="（已弃用）排除盒形遮挡器",
        description="启用后，将忽略所选 ymap 中的所有盒形遮挡器",
        default=False,
        update=_on_update_thunk,
    )

    ymap_model_occluders: BoolProperty(
        name="（已弃用）排除模型遮挡器",
        description="启用后，将忽略所选 ymap 中的所有模型遮挡器",
        default=False,
        update=_on_update_thunk,
    )

    ymap_car_generators: BoolProperty(
        name="（已弃用）排除载具生成器",
        description="启用后，将忽略所选 ymap 中的所有载具生成器",
        default=False,
        update=_on_update_thunk,
    )

    apply_transforms: BoolProperty(
        name="应用父级变换",
        description="应用可绘制体/碎片的缩放与旋转",
        default=False,
        update=_on_update_thunk,
    )

    mesh_domain: EnumProperty(
        name="网格域",
        description="导出网格时考虑的域",
        default="FACE_CORNER",
        items=(
            (
                "FACE_CORNER", "面角",
                "导出网格时允许每个面角拥有各自的"
                "属性集。推荐默认设置。"
            ),
            (
                "VERTEX", "顶点",
                "导出网格时仅允许每个顶点拥有一组属性。推荐用于需要保证"
                "顶点数与顺序在导入导出前后保持不变的场景，例如 MP 自由模式头部模型。\n\n"
                "如果连接到该顶点的面角属性不同（顶点颜色、UV 等），"
                "则仅使用其中某一个面角的属性。对于法线，则使用各面角法线的平均值。"
            )
        ),
        update=_on_update_thunk,
    )

    export_ytyps: BoolProperty(
        name="导出 YTYP",
        default=False,
        update=_on_update_thunk,
    )
    export_ytyps_include: EnumProperty(
        name="包含 YTYP",
        default="SELECTED",
        items=(
            ("ALL", "全部", "导出场景中的所有 YTYP"),
            ("SELECTED", "已选择", "导出已选中的 YTYP"),
        ),
        update=_on_update_thunk,
    )

    export_ymaps: BoolProperty(
        name="导出地图",
        default=False,
        update=_on_update_thunk,
    )
    export_ymaps_include: EnumProperty(
        name="包含地图",
        default="SELECTED",
        items=(
            ("ALL", "全部", "导出场景中的所有地图"),
            ("SELECTED", "已选择", "导出已选中的地图"),
        ),
        update=_on_update_thunk,
    )

    export_ytds: BoolProperty(
        name="导出贴图字典",
        default=False,
        update=_on_update_thunk,
    )
    export_ytds_include: EnumProperty(
        name="包含贴图字典",
        default="SELECTED",
        items=(
            ("ALL", "全部", "导出场景中的所有贴图字典"),
            ("SELECTED", "已选择", "导出已选中的贴图字典"),
        ),
        update=_on_update_thunk,
    )

    def to_export_context_settings(self) -> "ExportSettings":
        import itertools
        from .iecontext import ExportSettings, VBBuilderDomain
        from szio.gta5 import is_provider_available, AssetFormat, AssetVersion, AssetTarget
        return ExportSettings(
            targets=tuple(
                t
                for format_id, version_id in itertools.product(self.target_formats, self.target_versions)
                if is_provider_available(t := AssetTarget(AssetFormat[format_id], AssetVersion[version_id]))
            ),
            apply_transforms=self.apply_transforms,
            exclude_skeleton=self.exclude_skeleton,
            mesh_domain=VBBuilderDomain[self.mesh_domain],
        )


class ImportSettingsBase:
    def _on_update(self, context):
        ...

    import_as_asset: BoolProperty(
        name="导入到资产库",
        description="将所选文件作为资产导入到当前 .blend 文件的资产库中",
        default=False,
        update=_on_update_thunk,
    )

    split_by_group: BoolProperty(
        name="按顶点组拆分网格",
        description="按顶点组拆分网格",
        default=True,
        update=_on_update_thunk,
    )

    dwd_import_external_skeleton: EnumProperty(
        name="导入外部骨骼",
        description="导入外部 YFT 用作 YDD 的骨骼",
        items=(
            ("NO", "无", "不导入任何外部骨骼"),
            ("FROM_DIR", "自动", "自动使用与所导入文件同目录下找到的第一个 YFT"),
            ("SAVED", "已保存", "使用偏好设置中保存的 YFT"),
        ),
        default="NO",
        update=_on_update_thunk,
    )

    dwd_import_external_skeleton_saved_path: StringProperty(
        name="导入外部骨骼选择",
        description="要使用的外部骨骼 YFT（来自偏好设置中保存的列表）",
        update=_on_update_thunk,
    )

    frag_import_vehicle_windows: BoolProperty(
        name="导入车窗破碎贴图",
        description=(
            "将车辆车窗的破碎贴图作为对象导入到场景中。如果不导入，"
            "将在导出时自动生成（推荐）"
        ),
        default=False,
        update=_on_update_thunk,
    )

    ymap_skip_missing_entities: BoolProperty(
        name="（已弃用）跳过缺失实体",
        description="启用后，缺失的实体不会创建为空对象",
        default=True,
        update=_on_update_thunk,
    )

    ymap_exclude_entities: BoolProperty(
        name="（已弃用）排除实体",
        description="启用后，将忽略所选 ymap 中的所有实体",
        default=False,
        update=_on_update_thunk,
    )

    ymap_box_occluders: BoolProperty(
        name="（已弃用）排除盒形遮挡器",
        description="启用后，将忽略所选 ymap 中的所有盒形遮挡器",
        default=False,
        update=_on_update_thunk,
    )

    ymap_model_occluders: BoolProperty(
        name="（已弃用）排除模型遮挡器",
        description="启用后，将忽略所选 ymap 中的所有模型遮挡器",
        default=False,
        update=_on_update_thunk,
    )

    ymap_car_generators: BoolProperty(
        name="（已弃用）排除载具生成器",
        description="启用后，将忽略所选 ymap 中的所有载具生成器",
        default=False,
        update=_on_update_thunk,
    )

    ymap_instance_entities: BoolProperty(
        name="实例化实体",
        description="启用后，实例化所导入 ymap 中的所有实体",
        default=True,
        update=_on_update_thunk,
    )

    ytyp_mlo_instance_entities: BoolProperty(
        name="实例化 MLO 实体",
        description=(
            "启用后，MLO 实体将链接到与架构名匹配的对象的副本，"
            "而不是对象本身"
        ),
        default=True,
        update=_on_update_thunk,
    )

    textures_mode: EnumProperty(
        name="贴图模式",
        description="导入时如何处理贴图",
        items=(
            ("PACK", "打包到 Blend 文件（默认）", "将贴图打包到 .blend 文件中（推荐）"),
            ("IMPORT_DIR", "解压到导入目录", "将贴图解压到所导入文件旁的目录"),
            ("CUSTOM_DIR", "解压到自定义目录", "将贴图解压到下方指定的自定义目录"),
        ),
        default="PACK",
        update=_on_update_thunk,
    )

    textures_extract_custom_directory: StringProperty(
        name="自定义贴图目录",
        description=(
            "用于解压贴图的自定义目录。如果未设置，则回退使用导入目录。"
        ),
        subtype="DIR_PATH",
        default="",
        update=_on_update_thunk,
    )

    def to_import_context_settings(self) -> "ImportSettings":
        from .iecontext import ImportSettings, ImportTexturesMode, ImportExternalSkeletonMode

        textures_mode = ImportTexturesMode[self.textures_mode]
        textures_extract_custom_dir=(
            Path(bpy.path.abspath(self.textures_extract_custom_directory))
            if self.textures_extract_custom_directory
            else None
        )
        if textures_mode == ImportTexturesMode.CUSTOM_DIR and not textures_extract_custom_dir:
            # If there is no custom directory set, fallback to the import directory.
            textures_mode = ImportTexturesMode.IMPORT_DIR

        dwd_import_external_skeleton = ImportExternalSkeletonMode[self.dwd_import_external_skeleton]
        dwd_import_external_skeleton_saved_path = (
            Path(bpy.path.abspath(self.dwd_import_external_skeleton_saved_path))
            if dwd_import_external_skeleton == ImportExternalSkeletonMode.SAVED and self.dwd_import_external_skeleton_saved_path
            else None
        )

        return ImportSettings(
            import_as_asset=self.import_as_asset,
            split_by_group=self.split_by_group,
            mlo_instance_entities=self.ytyp_mlo_instance_entities,
            dwd_import_external_skeleton=dwd_import_external_skeleton,
            dwd_import_external_skeleton_saved_path=dwd_import_external_skeleton_saved_path,
            frag_import_vehicle_windows=self.frag_import_vehicle_windows,
            map_instance_entities=self.ymap_instance_entities,
            textures_mode=textures_mode,
            textures_extract_custom_directory=textures_extract_custom_dir,
        )


class SollumzExportSettings(ExportSettingsBase, PropertyGroup):
    def _on_update(self, context):
        # Make sure there is always something selected in the target format/version
        from szio.gta5 import is_provider_available, AssetFormat
        if not self.target_formats or (not is_provider_available(AssetFormat.NATIVE) and "CWXML" not in self.target_formats):
            self.target_formats = {"CWXML"}
            return # the assignment above will trigger this callback again

        if not self.target_versions:
            self.target_versions = {"GEN8"}
            return # the assignment above will trigger this callback again

        _save_preferences_on_update(self, context)


class SollumzImportSettings(ImportSettingsBase, PropertyGroup):
    def _on_update(self, context):
        _save_preferences_on_update(self, context)


class SollumzThemeSettings(PropertyGroup):
    def RGBAProperty(name: str, default: tuple[float, float, float]):
        return FloatVectorProperty(
            name=name,
            subtype="COLOR",
            min=0, max=1,
            size=4,
            default=default,
            update=_save_preferences_on_update,
        )

    mlo_gizmo_room: RGBAProperty("房间", (0.31, 0.38, 1.0, 0.7))
    mlo_gizmo_room_selected: RGBAProperty("已选择房间", (0.62, 0.76, 1.0, 0.9))
    mlo_gizmo_portal: RGBAProperty("Portal", (0.45, 0.98, 0.55, 0.5))
    mlo_gizmo_portal_selected: RGBAProperty("已选择 Portal", (0.93, 1.0, 1.0, 0.7))
    mlo_gizmo_portal_direction: RGBAProperty("Portal 方向箭头", (0.0, 0.6, 1.0, 0.3))
    mlo_gizmo_portal_direction_size: FloatProperty(name="Portal 方向箭头大小", default=0.3, min=0.1, max=5.0)
    mlo_gizmo_tcm: RGBAProperty("时间周期修改器", (0.45, 0.98, 0.55, 0.5))
    mlo_gizmo_tcm_selected: RGBAProperty("已选择时间周期修改器", (0.93, 1.0, 1.0, 0.7))

    cable_overlay_radius: RGBAProperty("半径", (1.0, 0.0, 0.0, 1.0))

    cloth_overlay_pinned: RGBAProperty("已固定", (1.0, 0.65, 0.0, 0.5))
    cloth_overlay_pinned_size: IntProperty(name="已固定大小", default=12, min=1, max=50)
    cloth_overlay_material_errors: RGBAProperty("材质错误", (1.0, 0.05, 0.025, 0.45))
    cloth_overlay_binding_errors: RGBAProperty("绑定错误", (1.0, 0.05, 0.025, 0.75))
    cloth_overlay_binding_errors_size: IntProperty(name="绑定错误大小", default=12, min=1, max=50)

    def reset(self):
        for prop_name, annotation in SollumzThemeSettings.__annotations__.items():
            setattr(self, prop_name, annotation.keywords["default"])


class SOLLUMZ_OT_prefs_theme_reset(Operator):
    bl_idname = "sollumz.prefs_theme_reset"
    bl_label = "重置主题"
    bl_description = "将所有主题设置重置为默认值"

    def execute(self, context):
        get_theme_settings(context).reset()
        _save_preferences()
        return {"FINISHED"}


class SzSharedAssetsDirectory(PropertyGroup):
    name: StringProperty(name="Name")
    path: StringProperty(
        name="Path",
        description="Path to a directory where to store the asset library",
        subtype="DIR_PATH",
        update=_save_preferences_on_update,
    )


class SOLLUMZ_UL_prefs_shared_assets_directories(UIList):
    bl_idname = "SOLLUMZ_UL_prefs_shared_assets_directories"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.prop(item, "name", text="", emboss=False)
        layout.prop(item, "path", text="", emboss=False)


class SOLLUMZ_OT_prefs_shared_assets_directory_add(Operator):
    bl_idname = "sollumz.prefs_shared_assets_directory_add"
    bl_label = "添加共享资产目录"
    bl_description = "添加一个新的目录用于搜索资产"

    name: StringProperty(name="名称")
    path: StringProperty(
        name="路径",
        description="用于存储资产库的目录路径",
        subtype="DIR_PATH",
    )

    def execute(self, context):
        prefs = get_addon_preferences(context)
        d = prefs.shared_assets_directories.add()
        d.name = self.name
        d.path = self.path
        prefs.shared_assets_directories_index = len(prefs.shared_assets_directories) - 1
        _save_preferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class SOLLUMZ_OT_prefs_shared_assets_directory_remove(Operator):
    bl_idname = "sollumz.prefs_shared_assets_directory_remove"
    bl_label = "删除共享资产目录"
    bl_description = "删除所选目录"

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return 0 <= prefs.shared_assets_directories_index < len(prefs.shared_assets_directories)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        prefs.shared_assets_directories.remove(prefs.shared_assets_directories_index)
        prefs.shared_assets_directories_index = max(prefs.shared_assets_directories_index - 1, 0)
        _save_preferences()
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_shared_assets_directory_move_up(Operator):
    bl_idname = "sollumz.prefs_shared_assets_directory_move_up"
    bl_label = "提升共享贴图目录优先级"
    bl_description = "提升该目录的搜索优先级"

    @classmethod
    def poll(self, context):
        prefs = get_addon_preferences(context)
        return 0 < prefs.shared_assets_directories_index < len(prefs.shared_assets_directories)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        indexA = prefs.shared_assets_directories_index
        indexB = prefs.shared_assets_directories_index - 1
        prefs.swap_shared_assets_directories(indexA, indexB)
        prefs.shared_assets_directories_index -= 1
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_shared_assets_directory_move_down(Operator):
    bl_idname = "sollumz.prefs_shared_assets_directory_move_down"
    bl_label = "降低共享贴图目录优先级"
    bl_description = "降低该目录的搜索优先级"

    @classmethod
    def poll(self, context):
        prefs = get_addon_preferences(context)
        return 0 <= prefs.shared_assets_directories_index < (len(prefs.shared_assets_directories) - 1)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        indexA = prefs.shared_assets_directories_index
        indexB = prefs.shared_assets_directories_index + 1
        prefs.swap_shared_assets_directories(indexA, indexB)
        prefs.shared_assets_directories_index += 1
        return {"FINISHED"}


class SzSharedTexturesDirectory(PropertyGroup):
    path: StringProperty(
        name="Path",
        description="Path to a directory with textures",
        subtype="DIR_PATH",
        update=_save_preferences_on_update,
    )
    recursive: BoolProperty(
        name="Recursive",
        description="Search this directory recursively",
        default=True,
        update=_save_preferences_on_update,
    )


class SOLLUMZ_UL_prefs_shared_textures_directories(UIList):
    bl_idname = "SOLLUMZ_UL_prefs_shared_textures_directories"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.prop(item, "path", text="", emboss=False)
        layout.prop(item, "recursive", text="", icon="OUTLINER")


class SOLLUMZ_OT_prefs_shared_textures_directory_add(Operator):
    bl_idname = "sollumz.prefs_shared_textures_directory_add"
    bl_label = "添加共享贴图目录"
    bl_description = "添加一个新的目录用于搜索贴图"

    path: StringProperty(
        name="路径",
        description="包含贴图的目录路径",
        subtype="DIR_PATH",
    )
    recursive: BoolProperty(
        name="递归",
        description="递归搜索此目录",
        default=True,
    )

    def execute(self, context):
        prefs = get_addon_preferences(context)
        d = prefs.shared_textures_directories.add()
        d.path = self.path
        d.recursive = self.recursive
        prefs.shared_textures_directories_index = len(prefs.shared_textures_directories) - 1
        _save_preferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class SOLLUMZ_OT_prefs_shared_textures_directory_remove(Operator):
    bl_idname = "sollumz.prefs_shared_textures_directory_remove"
    bl_label = "删除共享贴图目录"
    bl_description = "删除所选目录"

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return 0 <= prefs.shared_textures_directories_index < len(prefs.shared_textures_directories)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        prefs.shared_textures_directories.remove(prefs.shared_textures_directories_index)
        prefs.shared_textures_directories_index = max(prefs.shared_textures_directories_index - 1, 0)
        _save_preferences()
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_shared_textures_directory_move_up(Operator):
    bl_idname = "sollumz.prefs_shared_textures_directory_move_up"
    bl_label = "提升共享贴图目录优先级"
    bl_description = "提升该目录的搜索优先级"

    @classmethod
    def poll(self, context):
        prefs = get_addon_preferences(context)
        return 0 < prefs.shared_textures_directories_index < len(prefs.shared_textures_directories)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        indexA = prefs.shared_textures_directories_index
        indexB = prefs.shared_textures_directories_index - 1
        prefs.swap_shared_textures_directories(indexA, indexB)
        prefs.shared_textures_directories_index -= 1
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_shared_textures_directory_move_down(Operator):
    bl_idname = "sollumz.prefs_shared_textures_directory_move_down"
    bl_label = "降低共享贴图目录优先级"
    bl_description = "降低该目录的搜索优先级"

    @classmethod
    def poll(self, context):
        prefs = get_addon_preferences(context)
        return 0 <= prefs.shared_textures_directories_index < (len(prefs.shared_textures_directories) - 1)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        indexA = prefs.shared_textures_directories_index
        indexB = prefs.shared_textures_directories_index + 1
        prefs.swap_shared_textures_directories(indexA, indexB)
        prefs.shared_textures_directories_index += 1
        return {"FINISHED"}


def _update_name_tables():
    import szio.gta5.jenkhash

    nt_paths = [nt.path for nt in get_addon_preferences().name_table_paths]
    cache_path = Path(data_directory_path()) / "nametable.cache"
    szio.gta5.jenkhash.load_name_tables(nt_paths, cache_path)


def _on_update_name_tables(self, context):
    _save_preferences_on_update(self, context)
    _update_name_tables()


class SzNameTablePath(PropertyGroup):
    path: StringProperty(
        name="路径",
        description="名称表文件的路径",
        subtype="FILE_PATH",
        update=_on_update_name_tables,
    )

    # NOTE: this is here for forward compatibility to avoid breaking the preferences .ini, we will probably need to
    #       split the name tables for different contexts (e.g. GTA5, RDR2, drawable dictionaries) at some point. For
    #       now, they are all added to the same dictionary so default to GLOBAL.
    category: EnumProperty(
        items=(
            ("GLOBAL", "Global", "", "", 0),
        ),
        default="GLOBAL",
    )


class SOLLUMZ_UL_prefs_name_table_paths(UIList):
    bl_idname = "SOLLUMZ_UL_prefs_name_table_paths"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.prop(item, "path", text="", emboss=False)


class SOLLUMZ_OT_prefs_name_table_path_add(Operator, ImportHelper):
    bl_idname = "sollumz.prefs_name_table_path_add"
    bl_label = "添加名称表"
    bl_description = "添加新的名称表"

    directory: bpy.props.StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})
    files: bpy.props.CollectionProperty(
        name="文件路径",
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    filter_glob: bpy.props.StringProperty(
        default="".join(f"*{ext};" for ext in (".txt", ".nametable")),
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    def execute(self, context):
        if not self.directory or len(self.files) == 0 or self.files[0].name == "":
            # logger.info("No file selected for import!")
            return {"CANCELLED"}

        self.directory = bpy.path.abspath(self.directory)

        from pathlib import Path
        filenames = [f.name for f in self.files]
        directory = Path(self.directory)
        for filename in filenames:
            filepath = (directory / filename).absolute()

            prefs = get_addon_preferences(context)
            d = prefs.name_table_paths.add()
            d.path = str(filepath)

        prefs.name_table_paths_index = len(prefs.name_table_paths) - 1
        _save_preferences()
        _update_name_tables()
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_name_table_path_remove(Operator):
    bl_idname = "sollumz.prefs_name_table_path_remove"
    bl_label = "删除名称表路径"
    bl_description = "删除所选的名称表"

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return 0 <= prefs.name_table_paths_index < len(prefs.name_table_paths)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        prefs.name_table_paths.remove(prefs.name_table_paths_index)
        prefs.name_table_paths_index = max(prefs.name_table_paths_index - 1, 0)
        _save_preferences()
        _update_name_tables()
        return {"FINISHED"}


class SzExternalSkeletonPath(PropertyGroup):
    # 命名为 `name` 以便与 `prop_search` 一起使用，其 `item_search_property` 参数在 5.0 才加入，
    # 我们仍要支持旧版本
    name: StringProperty(
        name="路径",
        description="YFT 文件的路径",
        subtype="FILE_PATH",
        update=_save_preferences_on_update,
    )


class SOLLUMZ_UL_prefs_external_skeleton_paths(UIList):
    bl_idname = "SOLLUMZ_UL_prefs_external_skeleton_paths"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.prop(item, "name", text="", emboss=False)


class SOLLUMZ_OT_prefs_external_skeleton_path_add(Operator, ImportHelper):
    bl_idname = "sollumz.prefs_external_skeleton_path_add"
    bl_label = "添加外部骨骼"
    bl_description = "添加新的外部骨骼"

    directory: bpy.props.StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})
    files: bpy.props.CollectionProperty(
        name="文件路径",
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    filter_glob: bpy.props.StringProperty(
        default="".join(f"*{ext};" for ext in (".yft", ".yft.xml")),
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    def execute(self, context):
        if not self.directory or len(self.files) == 0 or self.files[0].name == "":
            # logger.info("No file selected for import!")
            return {"CANCELLED"}

        self.directory = bpy.path.abspath(self.directory)

        from pathlib import Path
        prefs = get_addon_preferences(context)
        filenames = [f.name for f in self.files]
        directory = Path(self.directory)
        for filename in filenames:
            filepath = (directory / filename).absolute()

            d = prefs.external_skeleton_paths.add()
            d.name = str(filepath)

        prefs.external_skeleton_paths_index = len(prefs.external_skeleton_paths) - 1
        _save_preferences()
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_external_skeleton_path_remove(Operator):
    bl_idname = "sollumz.prefs_external_skeleton_path_remove"
    bl_label = "删除外部骨骼路径"
    bl_description = "删除所选的外部骨骼"

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return 0 <= prefs.external_skeleton_paths_index < len(prefs.external_skeleton_paths)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        prefs.external_skeleton_paths.remove(prefs.external_skeleton_paths_index)
        prefs.external_skeleton_paths_index = max(prefs.external_skeleton_paths_index - 1, 0)
        _save_preferences()
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_external_skeleton_path_add_mp_freemode(Operator):
    bl_idname = "sollumz.prefs_external_skeleton_path_add_mp_freemode"
    bl_label = "选择游戏安装目录"
    bl_description = "从游戏文件中添加 MP 自由模式骨骼"

    directory: bpy.props.StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        if not IS_SZIO_NATIVE_AVAILABLE:
            cls.poll_message_set(PYMATERIA_REQUIRED_MSG)
            return False

        return True

    def draw(self, context):
        pass

    def execute(self, context):
        from . import logger
        with logger.use_operator_logger(self):
            if not self.directory:
                return {"CANCELLED"}

            directory = Path(bpy.path.abspath(self.directory))
            if not directory.is_dir():
                return {"CANCELLED"}

            from .shared.game_assets.game_files import GameFiles
            gf = GameFiles(directory)
            if not gf.is_game_installation():
                logger.warning("所选目录不是 GTA5 安装目录")
                return {"CANCELLED"}


            prefs = get_addon_preferences(context)
            for subpath in (
                "x64v.rpf\models\cdimages\streamedpeds_mp.rpf\mp_m_freemode_01.yft",
                "x64v.rpf\models\cdimages\streamedpeds_mp.rpf\mp_f_freemode_01.yft",
            ):
                filepath = (directory / subpath).absolute()

                d = prefs.external_skeleton_paths.add()
                d.name = str(filepath)

            prefs.external_skeleton_paths_index = len(prefs.external_skeleton_paths) - 1

            return {"FINISHED"}

    def invoke(self, context, event):
        if self.directory:
            return self.execute(context)

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class SOLLUMZ_MT_prefs_external_skeleton_paths_context_menu(Menu):
    bl_label = "外部骨骼路径特殊项"
    bl_idname = "SOLLUMZ_MT_prefs_external_skeleton_paths_context_menu"

    def draw(self, _context):
        layout = self.layout
        layout.operator(SOLLUMZ_OT_prefs_external_skeleton_path_add_mp_freemode.bl_idname, text="从游戏文件添加 MP 自由模式骨骼")


class SzFavoriteEntry(PropertyGroup):
    name: StringProperty(
        name="名称",
    )


class SollumzAddonPreferences(AddonPreferences):
    bl_idname = __package__

    def _on_show_version_update(self, context):
        _save_preferences_on_update(self, context)
        from .sollumz_ui import statusbar_register_draw, statusbar_unregister_draw
        statusbar_unregister_draw()
        if self.show_version_in_statusbar:
            statusbar_register_draw()

    show_version_in_statusbar: BoolProperty(
        name="在状态栏中显示 Sollumz 版本",
        description="在状态栏中 Blender 版本旁边显示 Sollumz 版本",
        default=True,
        update=_on_show_version_update
    )

    show_vertex_painter: BoolProperty(
        name="显示顶点绘制器",
        description="在常规工具中显示顶点绘制器面板（包含地形绘制器）",
        default=True,
        update=_save_preferences_on_update
    )

    extra_color_swatches: BoolProperty(
        name="额外的顶点颜色色板",
        description="向顶点绘制器面板添加 3 个额外的颜色色板（最多 6 个）",
        default=True,
        update=_save_preferences_on_update
    )

    sollumz_icon_header: BoolProperty(
        name="显示 Sollumz 图标",
        description="在属性区域的标题中显示 Sollumz 图标",
        default=True,
        update=_save_preferences_on_update
    )
    use_text_name_as_mat_name: BoolProperty(
        name="将贴图名称用作材质名称",
        description="使用贴图的名称作为材质名称",
        default=True,
        update=_save_preferences_on_update
    )

    shader_preset_apply_textures: BoolProperty(
        name="应用着色器预设中的贴图",
        description=(
            "启用后，将使用着色器预设中的贴图替换材质的现有贴图。"
            "禁用则保留当前贴图不变"
        ),
        default=True,
        update=_save_preferences_on_update
    )

    default_flags_portal: IntProperty(
        name="默认 Portal 标记",
        description="MLO portal 的默认标记",
        default=0,
        update=_save_preferences_on_update
    )

    default_flags_room: IntProperty(
        name="默认房间标记",
        description="MLO 房间的默认标记",
        default=0,
        update=_save_preferences_on_update
    )

    default_flags_entity: IntProperty(
        name="默认实体标记",
        description="MLO 实体的默认标记",
        default=0,
        update=_save_preferences_on_update
    )

    default_flags_archetype: IntProperty(
        name="默认架构标记",
        description="架构的默认标记",
        default=0,
        update=_save_preferences_on_update
    )

    default_sync_selection_enabled: BoolProperty(
        name="默认启用选择同步",
        description="在新场景中默认启用架构/实体选择同步。需要重启生效",
        default=True,
        update=_save_preferences_on_update
    )

    shared_textures_directories: CollectionProperty(
        name="共享贴图",
        type=SzSharedTexturesDirectory,
    )
    shared_textures_directories_index: IntProperty(
        name="已选中的共享贴图目录",
        min=0
    )

    shared_assets_directories: CollectionProperty(
        name="游戏资产库",
        type=SzSharedAssetsDirectory,
    )
    shared_assets_directories_index: IntProperty(
        name="已选中的共享资产目录",
        min=0
    )

    name_table_paths: CollectionProperty(
        name="名称表",
        type=SzNameTablePath,
    )
    name_table_paths_index: IntProperty(
        name="已选中的名称表",
        min=0
    )

    external_skeleton_paths: CollectionProperty(
        name="外部骨骼",
        type=SzExternalSkeletonPath,
    )
    external_skeleton_paths_index: IntProperty(
        name="已选中的外部骨骼",
        min=0
    )

    favorite_shaders: CollectionProperty(
        name="收藏的着色器",
        type=SzFavoriteEntry,
    )
    favorite_collision_materials: CollectionProperty(
        name="收藏的碰撞材质",
        type=SzFavoriteEntry,
    )

    # TODO: operator to create JSON from procedural.meta
    # tree = ET.parse("procedural.meta")
    # procids = [elem.text for elem in tree.getroot().findall("./procTagTable/Item/name")]
    # with open("procids.json", "w") as f:
    #     json.dump(procids, f, separators=(',', ':'))
    def _on_custom_procids_path_update(self, context):
        _save_preferences_on_update(self, context)
        from .ybn.properties import ProceduralIdEnumItems
        ProceduralIdEnumItems.reload()

    custom_procids_path: StringProperty(
        name="自定义 Procedural ID",
        description=(
            "指向包含自定义 Procedural ID 名称列表的 JSON 文件的路径"
            "（包含 255 个字符串条目的 JSON 数组）。"
            "若你使用了修改过的 procedural.meta 文件非常有用"
        ),
        subtype="FILE_PATH",
        update=_on_custom_procids_path_update,
    )

    legacy_import_export: BoolProperty(
        name="旧版导入/导出",
        description=(
            "使用旧版导入/导出系统，仅支持 CodeWalker XML 格式。"
            "仅当你使用新导入/导出系统时遇到问题或错误（涉及二进制资源格式支持）才启用此选项"
        ),
        default=False,
        update=_save_preferences_on_update
    )

    popup_shown_install_dependencies: BoolProperty(
        default=False,
        update=_save_preferences_on_update
    )

    export_settings: PointerProperty(type=SollumzExportSettings, name="导出设置")
    import_settings: PointerProperty(type=SollumzImportSettings, name="导入设置")
    theme: PointerProperty(type=SollumzThemeSettings, name="主题")

    tab: EnumProperty(
        items=(
            ("GENERAL", "常规", "", "SETTINGS", 0),
            ("IMPORT_EXPORT", "导入 / 导出", "", "IMPORT", 1),
            ("KEYMAP", "快捷键", "", "KEY_TAB", 3),
            ("UI", "界面", "", "WINDOW", 4),
            ("THEME", "主题", "", "COLOR", 5),
            ("ABOUT", "关于", "", "INFO_LARGE", 6),
        )
    )

    def swap_shared_assets_directories(self, indexA: int, indexB: int):
        a = self.shared_assets_directories[indexA]
        b = self.shared_assets_directories[indexB]
        nameA, pathA = a.name, a.path
        nameB, pathB = b.name, b.path
        a.name, a.path = nameB, pathB
        b.name, b.path = nameA, pathA

    def swap_shared_textures_directories(self, indexA: int, indexB: int):
        a = self.shared_textures_directories[indexA]
        b = self.shared_textures_directories[indexB]
        pathA, recA = a.path, a.recursive
        pathB, recB = b.path, b.recursive
        a.path, a.recursive = pathB, recB
        b.path, b.recursive = pathA, recA

    def _is_favorite(self, favorites, entry_name: str) -> bool:
        for entry in favorites:
            if entry.name == entry_name:
                return True

        return False

    def _toggle_favorite(self, favorites, entry_name: str, favorite: bool):
        found = None
        for i, entry in enumerate(favorites):
            if entry.name == entry_name:
                found = i
                break

        updated = False
        if favorite:
            # Set as favorite
            if found is None:
                s = favorites.add()
                s.name = entry_name
                updated = True
        else:
            # Remove from favorites
            if found is not None:
                favorites.remove(found)
                updated = True

        if updated:
            _save_preferences()

    def is_favorite_shader(self, shader_name: str) -> bool:
        return self._is_favorite(self.favorite_shaders, shader_name)

    def is_favorite_collision_material(self, collision_material_name: str) -> bool:
        return self._is_favorite(self.favorite_collision_materials, collision_material_name)

    def toggle_favorite_shader(self, shader_name: str, favorite: bool):
        self._toggle_favorite(self.favorite_shaders, shader_name, favorite)

    def toggle_favorite_collision_material(self, collision_material_name: str, favorite: bool):
        self._toggle_favorite(self.favorite_collision_materials, collision_material_name, favorite)

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, "tab", expand=True)

        # Based on CenterAlignMixIn from Blender's scripts/startup/bl_ui/space_userpref.py
        width = context.region.width
        ui_scale = context.preferences.system.ui_scale
        # No horizontal margin if region is rather small.
        is_wide = width > (550 * ui_scale)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()
        if is_wide:
            row.label()  # Needed so col below is centered.

        col = row.column()
        col.ui_units_x = 95

        match self.tab:
            case "GENERAL":
                self.draw_general(context, col)
            case "IMPORT_EXPORT":
                self.draw_import_export(context, col)
            case "KEYMAP":
                self.draw_keymap(context, col)
            case "UI":
                self.draw_ui(context, col)
            case "THEME":
                self.draw_theme(context, col)
            case "ABOUT":
                self.draw_about(context, col)

        if is_wide:
            row.label()  # Needed so col above is centered.

    def draw_general(self, context, layout: UILayout):
        layout.prop(self, "use_text_name_as_mat_name")
        layout.prop(self, "shader_preset_apply_textures")
        layout.prop(self, "default_sync_selection_enabled")

        col = layout.column(align=True)
        col.prop(self, "default_flags_portal", text="Portal 默认标记")
        col.prop(self, "default_flags_room", text="房间")
        col.prop(self, "default_flags_entity", text="实体")
        col.prop(self, "default_flags_archetype", text="架构")

        from .sollumz_ui import draw_list_with_add_remove
        layout.separator()
        layout.label(text="游戏资产库")
        row = layout.row()
        self._draw_help_text(
            context, row,
            "存放 .blend 资产库文件的目录。导入地图和室内时会用到。"
        )
        _, side_col = draw_list_with_add_remove(
            layout,
            SOLLUMZ_OT_prefs_shared_assets_directory_add.bl_idname,
            SOLLUMZ_OT_prefs_shared_assets_directory_remove.bl_idname,
            SOLLUMZ_UL_prefs_shared_assets_directories.bl_idname, "",
            self, "shared_assets_directories",
            self, "shared_assets_directories_index",
            rows=4
        )
        side_col.separator()
        subcol = side_col.column(align=True)
        subcol.operator(SOLLUMZ_OT_prefs_shared_assets_directory_move_up.bl_idname, text="", icon="TRIA_UP")
        subcol.operator(SOLLUMZ_OT_prefs_shared_assets_directory_move_down.bl_idname, text="", icon="TRIA_DOWN")

        layout.separator()
        layout.label(text="共享贴图")
        row = layout.row()
        self._draw_help_text(
            context, row,
            "导入模型时搜索贴图的额外目录。当模型所在目录中找不到贴图时，"
            "会按顺序在这些目录中按名称匹配 .dds 文件。"
        )
        _, side_col = draw_list_with_add_remove(
            layout,
            SOLLUMZ_OT_prefs_shared_textures_directory_add.bl_idname,
            SOLLUMZ_OT_prefs_shared_textures_directory_remove.bl_idname,
            SOLLUMZ_UL_prefs_shared_textures_directories.bl_idname, "",
            self, "shared_textures_directories",
            self, "shared_textures_directories_index",
            rows=4
        )
        side_col.separator()
        subcol = side_col.column(align=True)
        subcol.operator(SOLLUMZ_OT_prefs_shared_textures_directory_move_up.bl_idname, text="", icon="TRIA_UP")
        subcol.operator(SOLLUMZ_OT_prefs_shared_textures_directory_move_down.bl_idname, text="", icon="TRIA_DOWN")

        layout.separator()
        layout.label(text="名称表")
        row = layout.row()
        self._draw_help_text(
            context, row,
            "用于解析哈希名称。接受名称之间以换行符（每行一个名称，.txt）"
            "或空字符（.nametable）分隔的文件。"
        )
        draw_list_with_add_remove(
            layout,
            SOLLUMZ_OT_prefs_name_table_path_add.bl_idname,
            SOLLUMZ_OT_prefs_name_table_path_remove.bl_idname,
            SOLLUMZ_UL_prefs_name_table_paths.bl_idname, "",
            self, "name_table_paths",
            self, "name_table_paths_index",
            rows=4
        )

        layout.separator()
        layout.label(text="外部骨骼")
        row = layout.row()
        self._draw_help_text(
            context, row,
            "导入不包含自身骨骼的可绘制字典（例如 ped 组件模型）时可用的 YFT 文件作为外部骨骼。"
            "当'导入外部骨骼'导入设置设为'已保存'时使用。"
        )
        _, side_col = draw_list_with_add_remove(
            layout,
            SOLLUMZ_OT_prefs_external_skeleton_path_add.bl_idname,
            SOLLUMZ_OT_prefs_external_skeleton_path_remove.bl_idname,
            SOLLUMZ_UL_prefs_external_skeleton_paths.bl_idname, "",
            self, "external_skeleton_paths",
            self, "external_skeleton_paths_index",
            rows=4
        )
        side_col.separator()
        side_col.menu(SOLLUMZ_MT_prefs_external_skeleton_paths_context_menu.bl_idname, icon="DOWNARROW_HLT", text="")

        layout.separator()
        if bpy.app.version >= (4, 1, 0):
            header, body = layout.panel("prefs_general_advanced", default_closed=True)
        else:
            # 当 UILayout.panel 不可用时，足够直接显示面板内容
            header, body = layout, layout
        header.label(text="高级")
        if body:
            # 这里故意不使用 `body`，因为在偏好设置默认框布局中看起来会很奇怪
            layout.prop(self, "custom_procids_path")

    def draw_import_export(self, context, layout: UILayout):
        def _section_header(layout: UILayout, text: str):
            _line_separator(layout)
            row = layout.row()
            row.alignment = "LEFT"
            row.label(text="", icon="BLANK1")
            row.label(text=text, icon="BLANK1")

        sublayout = layout
        width = context.region.width
        ui_scale = context.preferences.system.ui_scale
        use_two_column_layout = width > (800 * ui_scale)
        if use_two_column_layout:
            sublayout = layout.split(factor=0.5)

        # 导入设置
        box = sublayout.box()
        box.label(text="导入", icon="IMPORT")
        settings = self.import_settings
        box.prop(settings, "import_as_asset")

        _section_header(box, text="贴图")
        col = box.column(align=True)
        col.prop(settings, "textures_mode", text="模式")
        if settings.textures_mode == "CUSTOM_DIR":
            split = col.split(factor=0.4)
            row = split.row()
            if not settings.textures_extract_custom_directory:
                row.alignment = "RIGHT"
                row.alert = True
                row.label(icon="ERROR", text="未设置目录")
            split.row().prop(settings, "textures_extract_custom_directory", text="")

        _section_header(box, "碎片")
        box.prop(settings, "split_by_group")
        box.prop(settings, "frag_import_vehicle_windows")
        _section_header(box, "可绘制字典")
        col = box.column(align=True)
        col.row(align=True).prop(settings, "dwd_import_external_skeleton", expand=True)
        if settings.dwd_import_external_skeleton == "SAVED":
            if self.external_skeleton_paths:
                col.prop_search(
                    settings, "dwd_import_external_skeleton_saved_path",
                    self, "external_skeleton_paths",
                    text=" ", icon="ARMATURE_DATA",
                )
            else:
                split = col.split(factor=0.4)
                row = split.row()
                row = split.row()
                row.alert = True
                row.label(text="偏好设置中没有已保存的外部骨骼。", icon="ERROR")

        _section_header(box, "架构定义")
        box.prop(settings, "ytyp_mlo_instance_entities")

        _section_header(box, "地图")
        box.prop(settings, "ymap_instance_entities")

        # 导出设置
        box = sublayout.box()
        box.label(text="导出", icon="EXPORT")
        settings = self.export_settings

        if not self.legacy_import_export:
            from szio.gta5 import AssetFormat, is_provider_available
            row = box.row(align=True)
            row.use_property_split = False
            row.use_property_decorate = False
            split = row.split(factor=0.4, align=True)
            subrow = split.row(align=False)
            subrow.alignment = "RIGHT"
            subrow.label(text="格式")
            subrow = split.row(align=True)
            for f in ("NATIVE", "CWXML"):
                subsubrow = subrow.row(align=True)
                subsubrow.enabled = is_provider_available(AssetFormat[f])
                subsubrow.prop_enum(settings, "target_formats", f)

            row = box.row(align=True)
            row.use_property_split = False
            row.use_property_decorate = False
            split = row.split(factor=0.4, align=True)
            subrow = split.row(align=False)
            subrow.alignment = "RIGHT"
            subrow.label(text="版本")
            subrow = split.row(align=True)
            for f in ("GEN8", "GEN9"):
                subrow.prop_enum(settings, "target_versions", f)

        row = box.row(heading="限制为")
        row.prop(settings, "limit_to_selected", text="已选中的对象")

        _section_header(box, "可绘制体")
        box.prop(settings, "apply_transforms")
        box.prop(settings, "mesh_domain", expand=True)

        _section_header(box, "可绘制字典")
        box.prop(settings, "exclude_skeleton")

        _line_separator(layout, factor=3.0)
        layout.prop(self, "legacy_import_export")

    def draw_keymap(self, context, layout: UILayout):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        keymaps = (
            "3D 视图",
            "3D 视图工具: 对象, 编辑架构扩展",
            "动作编辑器",
            "非线性动画编辑器"
        )

        for keymap in keymaps:
            km = kc.keymaps.get(keymap)

            column = layout.column(align=True)
            row = column.row()
            row.label(text=keymap)

            for kmi in km.keymap_items:
                if (
                    (kmi.idname == "wm.call_menu_pie" and kmi.name.startswith("Sollumz")) or
                    kmi.idname.startswith("sollumz.")
                ):
                    column = layout.column(align=True)
                    row = column.row()
                    rna_keymap_ui.draw_kmi(["ADDON", "USER", "DEFAULT"], kc, km, kmi, row, 1)

            if keymap != keymaps[-1]:
                _line_separator(layout)

    def draw_ui(self, context, layout: UILayout):
        layout.prop(self, "show_version_in_statusbar")
        layout.prop(self, "show_vertex_painter")
        layout.prop(self, "extra_color_swatches")
        layout.prop(self, "sollumz_icon_header")

    def draw_theme(self, context, layout: UILayout):
        def _section_header(layout: UILayout, text: str, icon: str, first: bool = False):
            if not first:
                _line_separator(layout)
            row = layout.row()
            row.label(text=text, icon=icon)

        row = layout.row()
        row.alignment = "RIGHT"
        row.operator(SOLLUMZ_OT_prefs_theme_reset.bl_idname, text="      重置      ", icon="LOOP_BACK")

        layout.separator()

        theme = self.theme
        _section_header(layout, "MLO 操控器", "HOME", True)
        layout.prop(theme, "mlo_gizmo_room")
        layout.prop(theme, "mlo_gizmo_room_selected")
        layout.prop(theme, "mlo_gizmo_portal")
        layout.prop(theme, "mlo_gizmo_portal_selected")
        layout.prop(theme, "mlo_gizmo_portal_direction")
        layout.prop(theme, "mlo_gizmo_portal_direction_size")
        layout.prop(theme, "mlo_gizmo_tcm")
        layout.prop(theme, "mlo_gizmo_tcm_selected")

        _section_header(layout, "绳索叠加层", "OUTLINER_DATA_GREASEPENCIL")
        layout.prop(theme, "cable_overlay_radius")

        _section_header(layout, "布料叠加层", "MATCLOTH")
        layout.prop(theme, "cloth_overlay_pinned")
        layout.prop(theme, "cloth_overlay_pinned_size")
        layout.prop(theme, "cloth_overlay_material_errors")
        layout.prop(theme, "cloth_overlay_binding_errors")
        layout.prop(theme, "cloth_overlay_binding_errors_size")

    def draw_about(self, context, layout: UILayout):
        row = layout.row()
        row.operator("wm.url_open", text="Discord", icon="COMMUNITY").url = "https://discord.sollumz.org/"
        row.operator("wm.url_open", text="文档", icon="HELP").url = "https://docs.sollumz.org/"
        row.operator("wm.url_open", text="问题追踪", icon="URL").url = "https://github.com/Sollumz/Sollumz/issues"

        layout.separator(factor=4.0)

        # TODO: 应将赞助者列表放在可以方便更新的位置
        studio_benefactors = [("TStudio by TurboSaif", "https://turbosaif.tebex.io/")]
        silver_benefactors = ["Tafé", "P-lauski", "Apollo"]
        benefactors = "BrunX • Clementinise • Kuz • Eryxiz • rkangur • DOIIDAUM • L'kid • Unknown-TV • Ktoś • Reveler • SevenLife"

        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="感谢")

        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="", icon="KEYTYPE_EXTREME_VEC")
        row.label(text="工作室赞助者")
        row.label(text="", icon="KEYTYPE_EXTREME_VEC")
        layout.separator()
        for name, url in studio_benefactors:
            row = layout.row()
            row.alignment = "CENTER"
            row.emboss = "PULLDOWN_MENU"
            row.operator("wm.url_open", text=f"   {name}   ", icon="URL").url = url

        _line_separator(layout, factor=2.0)
        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="", icon="HANDLETYPE_FREE_VEC")
        row.label(text="白银赞助者")
        row.label(text="", icon="HANDLETYPE_FREE_VEC")
        layout.separator()
        for name in silver_benefactors:
            row = layout.row()
            row.alignment = "CENTER"
            row.label(text=name)

        _line_separator(layout, factor=2.0)
        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="", icon="REMOVE")
        row.label(text="Benefactors")
        row.label(text="", icon="REMOVE")
        layout.separator()
        # https://b3d.interplanety.org/en/multiline-text-in-blender-interface-panels/
        chars = int(context.region.width * 0.75 / 7)   # 7 pix on 1 character, 0.75 for margins
        wrapper = textwrap.TextWrapper(width=chars)
        text_lines = wrapper.wrap(text=benefactors)
        for text_line in text_lines:
            row = layout.row()
            row.alignment = "CENTER"
            row.label(text=text_line)

        layout.separator(factor=4.0)

        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="Help Support Development")
        row = layout.row()
        row.operator("wm.url_open", text="Open Collective", icon="URL").url = "https://opencollective.com/sollumz"
        row.operator("wm.url_open", text="GitHub Sponsors", icon="URL").url = "https://github.com/sponsors/Sollumz/"

        layout.separator()

    def _draw_help_text(self, context, layout: UILayout, text: str, width_percent: float = 0.95, dim: bool = True):
        chars = int(context.region.width * width_percent / 7)   # 7 pix on 1 character, width_percent for margins
        col = layout.column()
        col.active = False if dim else True
        col.scale_y = 0.65
        for text_line in text.splitlines():
            first_indent = len(text_line) - len(text_line.lstrip(" "))
            wrapper = textwrap.TextWrapper(width=chars, subsequent_indent=" " * first_indent)
            for wrapped_text_line in wrapper.wrap(text=text_line):
                col.label(text=wrapped_text_line)

    def register():
        _load_preferences()


def _line_separator(layout: UILayout, factor: float = 1.0):
    if bpy.app.version >= (4, 2, 0):
        layout.separator(type="LINE", factor=factor)
    else:
        layout.separator(factor=factor)


def get_addon_preferences(context: Optional[bpy.types.Context] = None) -> SollumzAddonPreferences:
    return (context or bpy.context).preferences.addons[__package__].preferences


def get_import_settings(context: Optional[bpy.types.Context] = None) -> SollumzImportSettings:
    """Get import user preferences. Import code should use `import_context().settings` instead of accessing the
    preferences directly (user scripts can override these settings)."""
    return get_addon_preferences(context).import_settings


def get_export_settings(context: Optional[bpy.types.Context] = None) -> SollumzExportSettings:
    """Get export user preferences. Export code should use `export_context().settings` instead of accessing the
    preferences directly (user scripts can override these settings)."""
    return get_addon_preferences(context).export_settings


def get_theme_settings(context: Optional[bpy.types.Context] = None) -> SollumzThemeSettings:
    return get_addon_preferences(context).theme


def _save_preferences():
    if _is_loading_preferences:
        # Don't save while loading preferences from disk; otherwise each setattr in the property
        # update callbacks would trigger a redundant full-file rewrite.
        return

    addon_prefs = get_addon_preferences(bpy.context)
    prefs_path = prefs_file_path()

    # interpolation=None so values containing '%' are written and read verbatim instead of being
    # treated as interpolation tokens.
    config = ConfigParser(interpolation=None)
    prefs_dict = _get_bpy_struct_as_dict(addon_prefs)
    main_prefs: dict[str, Any] = {}

    for key, value in prefs_dict.items():
        if isinstance(value, dict):
            config[key] = value
            continue

        main_prefs[key] = value

    config["main"] = main_prefs

    # Write atomically (temp file + os.replace) so an interrupted or failed write never truncates or
    # corrupts the existing preferences file.
    tmp_path = prefs_path + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            config.write(f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, prefs_path)
    except OSError:
        from . import logger
        logger.error(f"Failed to save Sollumz preferences to '{prefs_path}'.\n{traceback.format_exc()}")
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _load_preferences():
    # Preferences are loaded via an ini file in <user_blender_path>/<version>/config/sollumz_prefs.ini
    global _is_loading_preferences

    addon_prefs = get_addon_preferences(bpy.context)

    prefs_path = prefs_file_path()
    if not os.path.isfile(prefs_path):
        return

    try:
        config = ConfigParser(interpolation=None)
        config.read(prefs_path)
        config_dict = {}
        for section in config.keys():
            if section == "DEFAULT":
                continue

            if section == "main":
                config_dict.update(config["main"])
            else:
                config_dict[section] = dict(config[section])

        _is_loading_preferences = True
        try:
            _update_bpy_struct_from_dict(addon_prefs, config_dict, eval_strings=True)
        finally:
            _is_loading_preferences = False
    except Exception:
        # Loading runs from register(), so any error here would propagate out of the add-on registration and prevent it
        # from being enabled. Catch everything, fall back to the default preferences, and back up the unreadable file
        # so it isn't silently lost.
        from . import logger
        logger.error(
            f"Failed to load Sollumz preferences from '{prefs_path}'. Falling back to default "
            f"preferences.\n{traceback.format_exc()}"
        )
        try:
            os.replace(prefs_path, prefs_path + ".bak")
        except OSError:
            pass


def _get_bpy_struct_as_dict(struct: bpy_struct) -> dict:
    def _prop_to_value(key: str):
        prop = getattr(struct, key)
        if isinstance(prop, str):
            prop = repr(prop)  # repr adds quotes and escapes the string, so ast.literal_eval can parse it correctly later
        elif isinstance(prop, bpy_prop_array):
            prop = tuple(prop)
        elif isinstance(prop, bpy_prop_collection):
            prop = _get_bpy_collection_as_list(prop)
        elif isinstance(prop, bpy_struct):
            prop = _get_bpy_struct_as_dict(prop)

        return prop

    return {
        key: _prop_to_value(key)
        for key in struct.__annotations__.keys()
    }


def _update_bpy_struct_from_dict(struct: bpy_struct, values: dict, eval_strings: bool = False):
    for key in struct.__annotations__.keys():
        value = values.get(key, None)
        if value is None:
            continue

        if eval_strings and isinstance(value, str):
            value = ast.literal_eval(value)

        prop = getattr(struct, key)
        if isinstance(prop, bpy_prop_collection):
            assert isinstance(value, list)
            _update_bpy_collection_from_list(prop, value)
        elif isinstance(prop, bpy_struct):
            assert isinstance(value, dict)
            _update_bpy_struct_from_dict(prop, value, eval_strings=eval_strings)
        else:
            setattr(struct, key, value)


def _get_bpy_collection_as_list(collection: bpy_prop_collection) -> list:
    return list(
        entry_tuple if len(entry_tuple) > 1 else entry_tuple[0]
        for entry_tuple in map(_get_bpy_struct_as_tuple, collection)
    )


def _update_bpy_collection_from_list(collection: bpy_prop_collection, entries: list):
    collection.clear()
    for entry_tuple in entries:
        entry = collection.add()
        _update_bpy_struct_from_tuple(entry, entry_tuple)


def _get_bpy_struct_as_tuple(struct: bpy_struct) -> tuple:
    return tuple(
        getattr(struct, key)
        for key in struct.__annotations__.keys()
    )


def _update_bpy_struct_from_tuple(struct: bpy_struct, values: tuple | object):
    keys = list(struct.__annotations__.keys())
    values = values if isinstance(values, tuple) else (values,)

    if len(keys) != len(values):
        from . import logger
        logger.warning(
            f"Sollumz preferences: entry for '{type(struct).__name__}' has {len(values)} value(s), "
            f"expected {len(keys)}. Loading overlapping fields and leaving the rest at their defaults."
        )

    for key, value in zip(keys, values):
        setattr(struct, key, value)


def register():
    bpy.utils.register_class(SollumzAddonPreferences)
    _update_name_tables()


def unregister():
    bpy.utils.unregister_class(SollumzAddonPreferences)
