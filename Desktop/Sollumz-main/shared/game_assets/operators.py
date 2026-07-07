import os
import functools
from pathlib import Path

import bpy
from bpy.props import (
    EnumProperty,
    StringProperty,
    IntProperty,
)
from bpy.types import (
    Operator,
)

from ...sollumz_preferences import get_addon_preferences
from .library import (
    asset_cache_path,
    build_library,
    build_library_cache,
)

NEW_TAG = "<<NEW>>"


def _output_directory_choice_items(self, context):
    prefs = get_addon_preferences(context)
    items = []
    for d in prefs.shared_assets_directories:
        if not d.path:
            continue
        items.append((d.path, f"{d.name} | {d.path}", ""))
    items.append((NEW_TAG, "New...", "Save it to a new asset library directory"))
    return items


_build_library_progress = None

# TODO(ymap): remove 'Import To Asset Library' from regular import settings and make a special operator here
#             Should help with people accidentally toggling it on


def temporary_ui(layout):
    layout.operator(SOLLUMZ_OT_build_game_asset_library.bl_idname)
    if _build_library_progress is not None:
        completed, total = _build_library_progress
        layout.progress(
            text=f"正在创建资产库 ({completed}/{total})...",
            factor=completed / total if total > 0 else 0,
        )
    layout.operator(SOLLUMZ_OT_rebuild_game_asset_cache.bl_idname)


class SOLLUMZ_OT_build_game_asset_library(Operator):
    bl_idname = "sollumz.build_game_asset_library"
    bl_label = "构建资产库"
    bl_description = (
        "从目录中导入 .ytyp 游戏文件，并在配置的共享资产目录中创建 .blend 资产库文件"
    )

    directory: StringProperty(
        name="源目录",
        description="包含 .ytyp 文件及其资产的目录",
        subtype="DIR_PATH",
        options={"HIDDEN"},
    )

    filter_glob: StringProperty(
        default="*.ytyp;*.ytyp.xml",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    output_directory: StringProperty(
        name="输出目录",
        description="保存 .blend 库的目录",
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    output_directory_choice: EnumProperty(
        name="输出库",
        description="将 .blend 库写入哪个目录",
        items=_output_directory_choice_items,
        options={"SKIP_SAVE"},
    )
    new_output_directory_name: StringProperty(
        name="名称",
        description="新资产库的名称",
    )
    new_output_directory_path: StringProperty(
        name="路径",
        description="用于存储新资产库的目录路径",
    )

    pattern: StringProperty(
        name="匹配模式",
        description=(
            "用于过滤导入的 .ytyp 文件名的正则表达式。"
            "留空则导入全部"
        ),
    )
    num_subprocesses: IntProperty(
        name="子进程数",
        description=(
            "用于并行构建库的 Blender 子进程数。"
            "每个工作进程运行独立的 Blender 实例，因此数值越高构建越快，但占用更多内存和 CPU"
        ),
        default=max(1, os.cpu_count() // 4),
        min=1,
        max=os.cpu_count(),
    )

    @classmethod
    def poll(cls, context):
        if bpy.app.version < (4, 2, 0):
            # 当前使用 Blender CLI 命令生成子进程工作器，该功能在 4.2 中加入
            cls.poll_message_set("当前 Blender 版本无法构建库。请升级到 Blender 4.2 或更新版本。")
            return False

        return True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(self, "output_directory_choice")
        if self.output_directory_choice == NEW_TAG:
            col.prop(self, "new_output_directory_name")
            col.prop(self, "new_output_directory_path")

        layout.prop(self, "pattern")
        layout.prop(self, "num_subprocesses")

    def execute(self, context):
        if not self.output_directory:
            prefs = get_addon_preferences(context)
            if self.output_directory_choice == NEW_TAG:
                new_directory = Path(bpy.path.abspath(self.new_output_directory_path))
                try:
                    new_directory.mkdir(parents=True, exist_ok=True)
                except FileExistsError:
                    self.report({"ERROR"}, f"期望为目录而非文件: {str(new_directory)}")
                    return {"CANCELLED"}

                self.output_directory = self.new_output_directory_path
                bpy.ops.sollumz.prefs_shared_assets_directory_add(
                    name=self.new_output_directory_name, path=self.new_output_directory_path
                )
            else:
                if not prefs.shared_assets_directories:
                    self.report({"ERROR"}, "未配置共享资产目录。请在偏好设置 > Sollumz 中添加一个。")
                    return {"CANCELLED"}

                configured_paths = [d.path for d in prefs.shared_assets_directories if d.path]
                if len(configured_paths) > 1:
                    if self.output_directory_choice and self.output_directory_choice in configured_paths:
                        self.output_directory = self.output_directory_choice
                    else:
                        self.report({"WARNING"}, "未选择输出库，将使用第一个配置的目录。")
                        self.output_directory = configured_paths[0]
                else:
                    self.output_directory = configured_paths[0]

        output_directory = Path(bpy.path.abspath(self.output_directory))
        output_directory.mkdir(parents=True, exist_ok=True)

        source_directory = Path(bpy.path.abspath(self.directory))
        if not source_directory.is_dir():
            self.report({"ERROR"}, f"Source directory does not exist: '{source_directory}'")
            return {"CANCELLED"}

        work_iter = build_library(
            source_directory,
            output_directory,
            game_catalog="GTA5",
            num_subprocesses=self.num_subprocesses,
            typ_pattern=self.pattern,
            report_progress_cb=_report_build_library_progress,
        )
        bpy.app.timers.register(functools.partial(_timer_do_work, work_iter), first_interval=0.0, persistent=True)
        return {"FINISHED"}


def _report_build_library_progress(num_completed: int | None, num_total: int | None):
    global _build_library_progress
    if num_completed is None:
        # finished
        _build_library_progress = None
    else:
        _build_library_progress = num_completed, num_total


def _timer_do_work(work_iter):
    interval = next(work_iter, None)
    return interval


class SOLLUMZ_OT_rebuild_game_asset_cache(Operator):
    bl_idname = "sollumz.rebuild_game_asset_cache"
    bl_label = "调试 - 重建资产缓存"
    bl_description = "从共享资产目录中现有的 .blend 文件重建 SQLite 资产缓存"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return len(prefs.shared_assets_directories) > 0

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if not prefs.shared_assets_directories:
            self.report({"ERROR"}, "未配置共享资产目录。")
            return {"CANCELLED"}

        directories = []
        for d in prefs.shared_assets_directories:
            if not d.path:
                continue
            path = Path(bpy.path.abspath(d.path))
            if not path.is_dir():
                self.report({"WARNING"}, f"共享资产目录不存在，跳过: '{path}'")
                continue
            directories.append(path)

        if not directories:
            self.report({"ERROR"}, "未找到有效的共享资产目录。")
            return {"CANCELLED"}

        build_library_cache(directories)
        self.report({"INFO"}, f"资产缓存已在 '{asset_cache_path()}' 重建")
        return {"FINISHED"}
