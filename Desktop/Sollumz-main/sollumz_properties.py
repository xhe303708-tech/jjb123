import bpy
from enum import Enum
from typing import Sequence
from .tools.utils import flag_list_to_int, flag_prop_to_list, int_to_bool_list
from szio.gta5 import LodLevel as IOLodLevel, LightType as IOLightType


# NOTE: Do not reorder these enums or insert new entries in the middle. That will break compatibility with
#       existing .blend and require new versioning code. New entries can be added at the end.
class SollumType(str, Enum):
    NONE = "sollumz_none"

    FRAGMENT = "sollumz_fragment"
    FRAGGROUP = "sollumz_fraggroup"
    FRAGCHILD = "sollumz_fragchild"
    FRAGLOD = "sollumz_lod"
    SHATTERMAP = "sollumz_frag_vehicle_window"

    DRAWABLE_DICTIONARY = "sollumz_drawable_dictionary"
    DRAWABLE = "sollumz_drawable"
    DRAWABLE_MODEL = "sollumz_drawable_model"
    DRAWABLE_GEOMETRY = "sollumz_drawable_geometry"
    SKELETON = "sollumz_skeleton"
    LIGHT = "sollumz_light"

    BOUND_BOX = "sollumz_bound_box"
    BOUND_SPHERE = "sollumz_bound_sphere"
    BOUND_CAPSULE = "sollumz_bound_capsule"
    BOUND_CYLINDER = "sollumz_bound_cylinder"
    BOUND_DISC = "sollumz_bound_disc"
    BOUND_PLANE = "sollumz_bound_plane"
    BOUND_GEOMETRY = "sollumz_bound_geometry"
    BOUND_GEOMETRYBVH = "sollumz_bound_geometrybvh"
    BOUND_COMPOSITE = "sollumz_bound_composite"

    BOUND_POLY_BOX = "sollumz_bound_poly_box"
    BOUND_POLY_SPHERE = "sollumz_bound_poly_sphere"
    BOUND_POLY_CAPSULE = "sollumz_bound_poly_capsule"
    BOUND_POLY_CYLINDER = "sollumz_bound_poly_cylinder"
    BOUND_POLY_TRIANGLE = "sollumz_bound_poly_triangle"

    NAVMESH = "sollumz_navmesh"
    NAVMESH_POLY_MESH = "sollumz_navmesh_mesh"
    NAVMESH_PORTAL = "sollumz_navmesh_portal"
    NAVMESH_POINT = "sollumz_navmesh_point"

    CLIP_DICTIONARY = "sollumz_clip_dictionary"
    CLIPS = "sollumz_clips"
    CLIP = "sollumz_clip"
    ANIMATIONS = "sollumz_animations"
    ANIMATION = "sollumz_animation"

    DEPRECATED__YMAP = "sollumz_ymap"
    DEPRECATED__YMAP_ENTITY_GROUP = "sollumz_ymap_entity_group"
    DEPRECATED__YMAP_BOX_OCCLUDER_GROUP = "sollumz_ymap_box_occluder_group"
    DEPRECATED__YMAP_MODEL_OCCLUDER_GROUP = "sollumz_ymap_model_occluder_group"
    DEPRECATED__YMAP_CAR_GENERATOR_GROUP = "sollumz_ymap_car_generator_group"
    DEPRECATED__YMAP_BOX_OCCLUDER = "sollumz_ymap_box_occluder"
    DEPRECATED__YMAP_MODEL_OCCLUDER = "sollumz_ymap_model_occluder"
    DEPRECATED__YMAP_CAR_GENERATOR = "sollumz_ymap_car_generator"

    CHARACTER_CLOTH_MESH = "sollumz_character_cloth_mesh"


class LightType(str, Enum):
    NONE = "sollumz_light_none"
    POINT = "sollumz_light_point"
    SPOT = "sollumz_light_spot"
    CAPSULE = "sollumz_light_capsule"

    def to_io(self) -> IOLightType:
        match self:
            case LightType.POINT:
                return IOLightType.POINT
            case LightType.SPOT:
                return IOLightType.SPOT
            case LightType.CAPSULE:
                return IOLightType.CAPSULE
            case LightType.NONE:
                raise ValueError("Cannot to convert NONE to asset I/O format")
            case _:
                raise ValueError(f"Unknown light type '{self}'")

    @staticmethod
    def from_io(light_type: IOLightType) -> "LightType":
        match light_type:
            case IOLightType.POINT:
                return LightType.POINT
            case IOLightType.SPOT:
                return LightType.SPOT
            case IOLightType.CAPSULE:
                return LightType.CAPSULE
            case _:
                raise ValueError(f"Unknown light type '{light_type}'")


class MaterialType(str, Enum):
    NONE = "sollumz_material_none",
    SHADER = "sollumz_material_shader",
    COLLISION = "sollumz_material_collision"
    DEPRECATED__SHATTER_MAP = "sollumz_material_shard"  # unused


class LODLevel(str, Enum):
    VERYHIGH = "sollumz_veryhigh"
    HIGH = "sollumz_high"
    MEDIUM = "sollumz_medium"
    LOW = "sollumz_low"
    VERYLOW = "sollumz_verylow"

    def to_io(self) -> IOLodLevel:
        match self:
            case LODLevel.HIGH:
                return IOLodLevel.HIGH
            case LODLevel.MEDIUM:
                return IOLodLevel.MEDIUM
            case LODLevel.LOW:
                return IOLodLevel.LOW
            case LODLevel.VERYLOW:
                return IOLodLevel.VERYLOW
            case LODLevel.VERYHIGH:
                return IOLodLevel.HIGH
            case _:
                raise ValueError(f"Unknown LOD '{self}'")

    @staticmethod
    def from_io(lod_level: IOLodLevel) -> "LODLevel":
        match lod_level:
            case IOLodLevel.HIGH:
                return LODLevel.HIGH
            case IOLodLevel.MEDIUM:
                return LODLevel.MEDIUM
            case IOLodLevel.LOW:
                return LODLevel.LOW
            case IOLodLevel.VERYLOW:
                return LODLevel.VERYLOW
            case _:
                raise ValueError(f"Unknown LOD '{lod_level}'")


LODLevelEnumItems = (
    (LODLevel.HIGH, "高", "", 0),
    (LODLevel.MEDIUM, "中", "", 1),
    (LODLevel.LOW, "低", "", 2),
    (LODLevel.VERYLOW, "极低", "", 3),
    (LODLevel.VERYHIGH, "极高", "", 4),
)


class EntityLodLevel(str, Enum):
    LODTYPES_DEPTH_HD = "sollumz_lodtypes_depth_hd"
    LODTYPES_DEPTH_LOD = "sollumz_lodtypes_depth_lod"
    LODTYPES_DEPTH_SLOD1 = "sollumz_lodtypes_depth_slod1"
    LODTYPES_DEPTH_SLOD2 = "sollumz_lodtypes_depth_slod2"
    LODTYPES_DEPTH_SLOD3 = "sollumz_lodtypes_depth_slod3"
    LODTYPES_DEPTH_SLOD4 = "sollumz_lodtypes_depth_slod4"
    LODTYPES_DEPTH_ORPHANHD = "sollumz_lodtypes_depth_orphanhd"


class EntityPriorityLevel(str, Enum):
    PRI_REQUIRED = "sollumz_pri_required"
    PRI_OPTIONAL_HIGH = "sollumz_pri_optional_high"
    PRI_OPTIONAL_MEDIUM = "sollumz_pri_optional_medium"
    PRI_OPTIONAL_LOW = "sollumz_pri_optional_low"


class ArchetypeType(str, Enum):
    BASE = "sollumz_archetype_base"
    TIME = "sollumz_archetype_time"
    MLO = "sollumz_archetype_mlo"


class AssetType(str, Enum):
    UNINITIALIZED = "sollumz_asset_uninitialized"
    FRAGMENT = "sollumz_asset_fragment"
    DRAWABLE = "sollumz_asset_drawable"
    DRAWABLE_DICTIONARY = "sollumz_asset_drawable_dictionary"
    ASSETLESS = "sollumz_asset_assetless"


class VehicleLightID(str, Enum):
    NONE = "none"
    ALWAYS_ON = "0"
    LEFT_HEADLIGHT = "1"
    RIGHT_HEADLIGHT = "2"
    LEFT_TAILLIGHT = "3"
    RIGHT_TAILLIGHT = "4"
    FRONT_LEFT_INDICATOR = "5"
    FRONT_RIGHT_INDICATOR = "6"
    REAR_LEFT_INDICATOR = "7"
    REAR_RIGHT_INDICATOR = "8"
    LEFT_BRAKELIGHT = "9"
    RIGHT_BRAKELIGHT = "10"
    CENTER_BRAKELIGHT = "11"
    LEFT_REVERSE_LIGHT = "12"
    RIGHT_REVERSE_LIGHT = "13"
    EXTRA_FRONT_LEFT = "14"
    EXTRA_FRONT_RIGHT = "15"
    EXTRA_REAR_LEFT = "16"
    EXTRA_REAR_RIGHT = "17"
    CUSTOM = "custom"


MIN_VEHICLE_LIGHT_ID = 0
MAX_VEHICLE_LIGHT_ID = 17


FRAGMENT_TYPES = [
    SollumType.FRAGMENT,
    SollumType.FRAGGROUP,
    SollumType.FRAGCHILD,
    SollumType.FRAGLOD,
    SollumType.SHATTERMAP,
]

BOUND_TYPES = [
    SollumType.BOUND_COMPOSITE,
    SollumType.BOUND_BOX,
    SollumType.BOUND_SPHERE,
    SollumType.BOUND_CYLINDER,
    SollumType.BOUND_CAPSULE,
    SollumType.BOUND_DISC,
    SollumType.BOUND_PLANE,
    SollumType.BOUND_GEOMETRY,
    SollumType.BOUND_GEOMETRYBVH,
]

BOUND_SHAPE_TYPES = [
    SollumType.BOUND_BOX,
    SollumType.BOUND_SPHERE,
    SollumType.BOUND_CYLINDER,
    SollumType.BOUND_CAPSULE,
    SollumType.BOUND_DISC,
    SollumType.BOUND_POLY_BOX,
    SollumType.BOUND_POLY_SPHERE,
    SollumType.BOUND_POLY_CAPSULE,
    SollumType.BOUND_POLY_CYLINDER,
    SollumType.BOUND_POLY_TRIANGLE,
]

BOUND_POLYGON_TYPES = [
    SollumType.BOUND_POLY_BOX,
    SollumType.BOUND_POLY_SPHERE,
    SollumType.BOUND_POLY_CAPSULE,
    SollumType.BOUND_POLY_CYLINDER,
    SollumType.BOUND_POLY_TRIANGLE,
]

DRAWABLE_TYPES = [
    SollumType.DRAWABLE_DICTIONARY,
    SollumType.DRAWABLE,
    SollumType.DRAWABLE_MODEL,
    SollumType.DRAWABLE_GEOMETRY,
    SollumType.SKELETON,
]


SOLLUMZ_UI_NAMES = {
    SollumType.BOUND_BOX: "边界盒",
    SollumType.BOUND_SPHERE: "边界球",
    SollumType.BOUND_CAPSULE: "边界胶囊体",
    SollumType.BOUND_CYLINDER: "边界圆柱体",
    SollumType.BOUND_DISC: "边界圆盘",
    SollumType.BOUND_PLANE: "边界平面",
    SollumType.BOUND_GEOMETRY: "边界几何体",
    SollumType.BOUND_GEOMETRYBVH: "边界几何体BVH",
    SollumType.BOUND_COMPOSITE: "边界组合体",

    SollumType.BOUND_POLY_BOX: "多边形边界盒",
    SollumType.BOUND_POLY_SPHERE: "多边形边界球",
    SollumType.BOUND_POLY_CAPSULE: "多边形边界胶囊体",
    SollumType.BOUND_POLY_CYLINDER: "多边形边界圆柱体",
    SollumType.BOUND_POLY_TRIANGLE: "多边形边界网格",

    SollumType.FRAGMENT: "碎片",
    SollumType.FRAGGROUP: "碎片组",
    SollumType.FRAGCHILD: "碎片子项",
    SollumType.FRAGLOD: "碎片 LOD",
    SollumType.SHATTERMAP: "破碎贴图",

    SollumType.NONE: "无",
    SollumType.DRAWABLE_DICTIONARY: "可绘制字典",
    SollumType.DRAWABLE: "可绘制体",
    SollumType.DRAWABLE_MODEL: "可绘制模型",
    SollumType.DRAWABLE_GEOMETRY: "可绘制几何体",
    SollumType.SKELETON: "骨骼",
    SollumType.LIGHT: "灯光",
    SollumType.CHARACTER_CLOTH_MESH: "角色布料网格",

    SollumType.NAVMESH: "导航网格",
    SollumType.NAVMESH_POLY_MESH: "导航多边形网格",
    SollumType.NAVMESH_PORTAL: "导航门户",
    SollumType.NAVMESH_POINT: "导航点",

    SollumType.CLIP_DICTIONARY: "动画片段字典",
    SollumType.CLIPS: "动画片段集",
    SollumType.CLIP: "动画片段",
    SollumType.ANIMATIONS: "动画集合",
    SollumType.ANIMATION: "动画",

    SollumType.DEPRECATED__YMAP: "（已弃用）Ymap",
    SollumType.DEPRECATED__YMAP_ENTITY_GROUP: "（已弃用）实体组",
    SollumType.DEPRECATED__YMAP_BOX_OCCLUDER_GROUP: "（已弃用）盒形遮挡器组",
    SollumType.DEPRECATED__YMAP_MODEL_OCCLUDER_GROUP: "（已弃用）模型遮挡器组",
    SollumType.DEPRECATED__YMAP_CAR_GENERATOR_GROUP: "（已弃用）载具生成器组",
    SollumType.DEPRECATED__YMAP_BOX_OCCLUDER: "（已弃用）盒形遮挡器",
    SollumType.DEPRECATED__YMAP_MODEL_OCCLUDER: "（已弃用）模型遮挡器",
    SollumType.DEPRECATED__YMAP_CAR_GENERATOR: "（已弃用）载具生成器",

    MaterialType.NONE: "无",
    MaterialType.SHADER: "Sollumz 材质",
    MaterialType.COLLISION: "Sollumz 碰撞材质",
    MaterialType.DEPRECATED__SHATTER_MAP: "（已弃用）Sollumz 破碎贴图",

    LODLevel.VERYHIGH: "极高",
    LODLevel.HIGH: "高",
    LODLevel.MEDIUM: "中",
    LODLevel.LOW: "低",
    LODLevel.VERYLOW: "极低",

    EntityLodLevel.LODTYPES_DEPTH_HD: "HD",
    EntityLodLevel.LODTYPES_DEPTH_LOD: "LOD",
    EntityLodLevel.LODTYPES_DEPTH_SLOD1: "SLOD1",
    EntityLodLevel.LODTYPES_DEPTH_SLOD2: "SLOD2",
    EntityLodLevel.LODTYPES_DEPTH_SLOD3: "SLOD3",
    EntityLodLevel.LODTYPES_DEPTH_SLOD4: "SLOD4",
    EntityLodLevel.LODTYPES_DEPTH_ORPHANHD: "ORPHAN HD",

    EntityPriorityLevel.PRI_REQUIRED: "必需",
    EntityPriorityLevel.PRI_OPTIONAL_HIGH: "可选 - 高",
    EntityPriorityLevel.PRI_OPTIONAL_MEDIUM: "可选 - 中",
    EntityPriorityLevel.PRI_OPTIONAL_LOW: "可选 - 低",

    LightType.NONE: "无",
    LightType.POINT: "点光",
    LightType.SPOT: "聚光",
    LightType.CAPSULE: "胶囊光",

    ArchetypeType.BASE: "基础",
    ArchetypeType.TIME: "时间",
    ArchetypeType.MLO: "MLO",

    AssetType.UNINITIALIZED: "未初始化",
    AssetType.FRAGMENT: "碎片",
    AssetType.DRAWABLE: "可绘制体",
    AssetType.DRAWABLE_DICTIONARY: "可绘制字典",
    AssetType.ASSETLESS: "无资产",

    VehicleLightID.NONE: "无",
    VehicleLightID.CUSTOM: "自定义",
    VehicleLightID.ALWAYS_ON: "常亮",
    VehicleLightID.LEFT_HEADLIGHT: "左前大灯 (headlight_l)",
    VehicleLightID.RIGHT_HEADLIGHT: "右前大灯 (headlight_r)",
    VehicleLightID.LEFT_TAILLIGHT: "左后尾灯 (taillight_l)",
    VehicleLightID.RIGHT_TAILLIGHT: "右后尾灯 (taillight_r)",
    VehicleLightID.FRONT_LEFT_INDICATOR: "左前转向灯 (indicator_lf)",
    VehicleLightID.FRONT_RIGHT_INDICATOR: "右前转向灯 (indicator_rf)",
    VehicleLightID.REAR_LEFT_INDICATOR: "左后转向灯 (indicator_lr)",
    VehicleLightID.REAR_RIGHT_INDICATOR: "右后转向灯 (indicator_rr)",
    VehicleLightID.LEFT_BRAKELIGHT: "左刹车灯 (brakelight_l)",
    VehicleLightID.RIGHT_BRAKELIGHT: "右刹车灯 (brakelight_r)",
    VehicleLightID.CENTER_BRAKELIGHT: "中央刹车灯 (brakelight_m)",
    VehicleLightID.LEFT_REVERSE_LIGHT: "左倒车灯 (reversinglight_l)",
    VehicleLightID.RIGHT_REVERSE_LIGHT: "右倒车灯 (reversinglight_r)",
    VehicleLightID.EXTRA_FRONT_LEFT: "额外左前灯 (extralight_1)",
    VehicleLightID.EXTRA_FRONT_RIGHT: "额外右前灯 (extralight_2)",
    VehicleLightID.EXTRA_REAR_LEFT: "额外左后灯 (extralight_3)",
    VehicleLightID.EXTRA_REAR_RIGHT: "额外右后灯 (extralight_4)",

}


# Generate items from provided enums
def items_from_enums(*enums, exclude=None):
    items = []
    for enum in enums:
        for item in enum:
            if exclude is not None and item in exclude:
                continue
            if item not in SOLLUMZ_UI_NAMES:
                raise KeyError(
                    f"UI name mapping not found for key {item} of {enum}.")
            items.append(
                (item.value, SOLLUMZ_UI_NAMES[item], ""))
    return items


class FlagPropertyGroup:
    def get_flag_names(self) -> Sequence[str]:
        return self.flag_names if self.flag_names else self.__annotations__.keys()

    def update_flags_total(self, context):
        # Ensure string can be converted to int
        try:
            int((self.total))
        except ValueError:
            self.total = "0"

        flags = int_to_bool_list(int(self.total), size=self.size)
        for index, flag_name in enumerate(self.get_flag_names()):
            if index >= self.size:
                break

            self[flag_name] = flags[index]

    def update_flag(self, context):
        flags = flag_prop_to_list(self.get_flag_names(), self, size=self.size)
        flags.pop()
        self.total = str(flag_list_to_int(flags))

    # Can be set to a list of strings to override the flags used or their order, otherwise, use the annotations.
    # Useful when the class annotations don't have all the flags (e.g. some flags are defined in base/mixin class)
    flag_names = None

    size = 32

    total: bpy.props.StringProperty(name="Flags", update=update_flags_total, default="0")

    # Preset capture/apply only round-trips `total`, setting it updates all the per-flag BoolProperty fields
    __sz_preset_capture__ = ("total",)


time_items = [("0", "上午 12:00", ""),
              ("1", "上午 1:00", ""),
              ("2", "上午 2:00", ""),
              ("3", "上午 3:00", ""),
              ("4", "上午 4:00", ""),
              ("5", "上午 5:00", ""),
              ("6", "上午 6:00", ""),
              ("7", "上午 7:00", ""),
              ("8", "上午 8:00", ""),
              ("9", "上午 9:00", ""),
              ("10", "上午 10:00", ""),
              ("11", "上午 11:00", ""),
              ("12", "下午 12:00", ""),
              ("13", "下午 1:00", ""),
              ("14", "下午 2:00", ""),
              ("15", "下午 3:00", ""),
              ("16", "下午 4:00", ""),
              ("17", "下午 5:00", ""),
              ("18", "下午 6:00", ""),
              ("19", "下午 7:00", ""),
              ("20", "下午 8:00", ""),
              ("21", "下午 9:00", ""),
              ("22", "下午 10:00", ""),
              ("23", "下午 11:00", "")]


class TimeFlagsMixin(FlagPropertyGroup):
    size = 24
    flag_names = [f"hour{i + 1}" for i in range(0, 24)]
    hour1: bpy.props.BoolProperty(name="上午 12:00 - 上午 1:00", update=FlagPropertyGroup.update_flag)
    hour2: bpy.props.BoolProperty(name="上午 1:00 - 上午 2:00", update=FlagPropertyGroup.update_flag)
    hour3: bpy.props.BoolProperty(name="上午 2:00 - 上午 3:00", update=FlagPropertyGroup.update_flag)
    hour4: bpy.props.BoolProperty(name="上午 3:00 - 上午 4:00", update=FlagPropertyGroup.update_flag)
    hour5: bpy.props.BoolProperty(name="上午 4:00 - 上午 5:00", update=FlagPropertyGroup.update_flag)
    hour6: bpy.props.BoolProperty(name="上午 5:00 - 上午 6:00", update=FlagPropertyGroup.update_flag)
    hour7: bpy.props.BoolProperty(name="上午 6:00 - 上午 7:00", update=FlagPropertyGroup.update_flag)
    hour8: bpy.props.BoolProperty(name="上午 7:00 - 上午 8:00", update=FlagPropertyGroup.update_flag)
    hour9: bpy.props.BoolProperty(name="上午 8:00 - 上午 9:00", update=FlagPropertyGroup.update_flag)
    hour10: bpy.props.BoolProperty(name="上午 9:00 - 上午 10:00", update=FlagPropertyGroup.update_flag)
    hour11: bpy.props.BoolProperty(name="上午 10:00 - 上午 11:00", update=FlagPropertyGroup.update_flag)
    hour12: bpy.props.BoolProperty(name="上午 11:00 - 下午 12:00", update=FlagPropertyGroup.update_flag)
    hour13: bpy.props.BoolProperty(name="下午 12:00 - 下午 1:00", update=FlagPropertyGroup.update_flag)
    hour14: bpy.props.BoolProperty(name="下午 1:00 - 下午 2:00", update=FlagPropertyGroup.update_flag)
    hour15: bpy.props.BoolProperty(name="下午 2:00 - 下午 3:00", update=FlagPropertyGroup.update_flag)
    hour16: bpy.props.BoolProperty(name="下午 3:00 - 下午 4:00", update=FlagPropertyGroup.update_flag)
    hour17: bpy.props.BoolProperty(name="下午 4:00 - 下午 5:00", update=FlagPropertyGroup.update_flag)
    hour18: bpy.props.BoolProperty(name="下午 5:00 - 下午 6:00", update=FlagPropertyGroup.update_flag)
    hour19: bpy.props.BoolProperty(name="下午 6:00 - 下午 7:00", update=FlagPropertyGroup.update_flag)
    hour20: bpy.props.BoolProperty(name="下午 7:00 - 下午 8:00", update=FlagPropertyGroup.update_flag)
    hour21: bpy.props.BoolProperty(name="下午 8:00 - 下午 9:00", update=FlagPropertyGroup.update_flag)
    hour22: bpy.props.BoolProperty(name="下午 9:00 - 下午 10:00", update=FlagPropertyGroup.update_flag)
    hour23: bpy.props.BoolProperty(name="下午 10:00 - 下午 11:00", update=FlagPropertyGroup.update_flag)
    hour24: bpy.props.BoolProperty(name="下午 11:00 - 上午 12:00", update=FlagPropertyGroup.update_flag)

    time_flags_start: bpy.props.EnumProperty(items=time_items, name="起始时间")
    time_flags_end: bpy.props.EnumProperty(items=time_items, name="结束时间")


class EntityProperties:
    archetype_name: bpy.props.StringProperty(name="架构名")
    flags: bpy.props.IntProperty(name="标记", default=32)
    guid: bpy.props.FloatProperty(name="GUID")
    parent_index: bpy.props.IntProperty(name="父索引", default=-1)
    lod_dist: bpy.props.FloatProperty(name="LOD 距离", default=200)
    child_lod_dist: bpy.props.FloatProperty(name="子级 LOD 距离")
    lod_level: bpy.props.EnumProperty(
        items=items_from_enums(EntityLodLevel),
        name="LOD 级别",
        default=EntityLodLevel.LODTYPES_DEPTH_ORPHANHD,
        options={"HIDDEN"}
    )
    num_children: bpy.props.IntProperty(name="子级数量")
    priority_level: bpy.props.EnumProperty(
        items=items_from_enums(EntityPriorityLevel),
        name="优先级",
        default=EntityPriorityLevel.PRI_REQUIRED,
        options={"HIDDEN"}
    )
    # TODO(ymap-next): make ambient_occlusion_multiplier, artificial_ambient_occlusion, and tint_value integers
    ambient_occlusion_multiplier: bpy.props.FloatProperty(
        name="环境光遮蔽乘数", default=255)
    artificial_ambient_occlusion: bpy.props.FloatProperty(
        name="人工环境光遮蔽", default=255)
    tint_value: bpy.props.FloatProperty(name="色调值")


class ObjectEntityProperties(bpy.types.PropertyGroup, EntityProperties):
    pass


def register():
    bpy.types.Object.sollum_type = bpy.props.EnumProperty(
        items=items_from_enums(SollumType),
        name="Sollum 类型",
        default=SollumType.NONE,
        options={"HIDDEN"}
    )

    bpy.types.Material.sollum_type = bpy.props.EnumProperty(
        items=items_from_enums(MaterialType),
        name="Sollumz 材质类型",
        default=MaterialType.NONE,
        options={"HIDDEN"}
    )

    bpy.types.ShaderNode.is_sollumz = bpy.props.BoolProperty(default=False)

    bpy.types.Object.entity_properties = bpy.props.PointerProperty(
        type=ObjectEntityProperties)

    bpy.types.Scene.vert_paint_color1 = bpy.props.FloatVectorProperty(
        name="顶点颜色 1",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color2 = bpy.props.FloatVectorProperty(
        name="顶点颜色 2",
        subtype="COLOR_GAMMA",
        default=(0.0, 0.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color3 = bpy.props.FloatVectorProperty(
        name="顶点颜色 3",
        subtype="COLOR_GAMMA",
        default=(0.0, 1.0, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color4 = bpy.props.FloatVectorProperty(
        name="顶点颜色 4",
        subtype="COLOR_GAMMA",
        default=(1.0, 0.0, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color5 = bpy.props.FloatVectorProperty(
        name="顶点颜色 5",
        subtype="COLOR_GAMMA",
        default=(1.0, 0.501961, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color6 = bpy.props.FloatVectorProperty(
        name="顶点颜色 6",
        subtype="COLOR_GAMMA",
        default=(0.0, 0.0, 0.0, 0.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.all_sollum_type = bpy.props.EnumProperty(
        items=sorted(items_from_enums(SollumType), key=lambda i: i[0]),
        name="Sollum 类型",
        options={"HIDDEN"}
    )

    bpy.types.Scene.sollumz_export_path = bpy.props.StringProperty(
        name="导出路径",
        default="",
        description="文件将被导出到的路径。如果未设置，将打开导出对话框",
        subtype="DIR_PATH",
    )


def unregister():
    del bpy.types.Object.sollum_type
    del bpy.types.Material.sollum_type
    del bpy.types.ShaderNode.is_sollumz
    del bpy.types.Object.entity_properties
    del bpy.types.Scene.vert_paint_color1
    del bpy.types.Scene.vert_paint_color2
    del bpy.types.Scene.vert_paint_color3
    del bpy.types.Scene.vert_paint_color4
    del bpy.types.Scene.vert_paint_color5
    del bpy.types.Scene.vert_paint_color6
    del bpy.types.Scene.all_sollum_type
    del bpy.types.Scene.sollumz_export_path
