import bpy
from bpy.types import (
    Object,
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    PointerProperty,
)
import bmesh
from enum import IntEnum

from ..tools.blenderhelper import remove_number_suffix
from ..sollumz_properties import (
    SOLLUMZ_UI_NAMES,
    SollumType,
    VehicleLightID,
    MIN_VEHICLE_LIGHT_ID,
    MAX_VEHICLE_LIGHT_ID,
    items_from_enums,
    FlagPropertyGroup,
)
from ..ydr.shader_materials import (
    VEHICLE_PREVIEW_NODE_DIRT_COLOR,
    VEHICLE_PREVIEW_NODE_DIRT_LEVEL,
    VEHICLE_PREVIEW_NODE_DIRT_WETNESS,
    VEHICLE_PREVIEW_NODE_BODY_COLOR,
    VEHICLE_PREVIEW_NODE_LIGHT_EMISSIVE_TOGGLE,
    get_vehicle_material_paint_layer,
    set_vehicle_material_paint_layer,
    update_vehicle_material_paint_name,
)
from szio.gta5 import (
    FragmentTemplateAsset,
)


class FragArchetypeProperties(bpy.types.PropertyGroup):
    max_speed: bpy.props.FloatProperty(name="最大速度", default=150)
    max_ang_speed: bpy.props.FloatProperty(name="最大角速度", default=6.2831855)
    gravity_factor: bpy.props.FloatProperty(name="重力系数", default=1)
    buoyancy_factor: bpy.props.FloatProperty(name="浮力系数", default=1)


class LODProperties(bpy.types.PropertyGroup):
    min_move_force: bpy.props.FloatProperty(name="最小移动力")
    unbroken_cg_offset: bpy.props.FloatVectorProperty(name="未破损重心偏移", subtype="XYZ")
    damping_linear_c: bpy.props.FloatVectorProperty(name="线性阻尼 C", default=(0.02, 0.02, 0.02))
    damping_linear_v: bpy.props.FloatVectorProperty(name="线性阻尼 V", default=(0.02, 0.02, 0.02))
    damping_linear_v2: bpy.props.FloatVectorProperty(name="线性阻尼 V2", default=(0.01, 0.01, 0.01))
    damping_angular_c: bpy.props.FloatVectorProperty(name="角度阻尼 C", default=(0.02, 0.02, 0.02))
    damping_angular_v: bpy.props.FloatVectorProperty(name="角度阻尼 V", default=(0.02, 0.02, 0.02))
    damping_angular_v2: bpy.props.FloatVectorProperty(name="角度阻尼 V2", default=(0.01, 0.01, 0.01))

    archetype_properties: bpy.props.PointerProperty(type=FragArchetypeProperties)


GlassTypes = (
    ("Pane", "Pane", "Pane", 0),
    ("Security", "Security", "Security", 1),
    ("Pane_Weak", "Pane Weak", "Pane Weak", 2),
)


def get_glass_type_index(glass_type_enum: str) -> int:
    for enum_name, _, _, index in GlassTypes:
        if glass_type_enum == enum_name:
            return index
    return -1


class GroupFlagBit(IntEnum):
    DISAPPEAR_WHEN_DEAD = 0
    USE_GLASS_WINDOW = 1
    DAMAGE_WHEN_BROKEN = 2
    DOESNT_AFFECT_VEHICLES = 3
    DOESNT_PUSH_VEHICLES_DOWN = 4
    # TODO: HAS_CLOTH is needed in some dynamic fragment props with cloth so the cloth stays attached to broken parts,
    #       we might be able to automatically set it on export but I haven't seen a clear pattern yet, sometimes only
    #       the direct parent from the cloth bone has it set, sometimes the whole parent tree.
    HAS_CLOTH = 5


class GroupProperties(bpy.types.PropertyGroup):
    flags: bpy.props.BoolVectorProperty(name="标记", size=len(GroupFlagBit))
    glass_type: bpy.props.EnumProperty(name="玻璃类型", items=GlassTypes)
    strength: bpy.props.FloatProperty(name="强度", default=100)
    force_transmission_scale_up: bpy.props.FloatProperty(name="力传递放大缩放", default=0.25)
    force_transmission_scale_down: bpy.props.FloatProperty(name="力传递缩小缩放", default=0.25)
    joint_stiffness: bpy.props.FloatProperty(name="关节刚度")
    min_soft_angle_1: bpy.props.FloatProperty(name="最小柔角 1", default=-1)
    max_soft_angle_1: bpy.props.FloatProperty(name="最大柔角 1", default=1)
    max_soft_angle_2: bpy.props.FloatProperty(name="最大柔角 2", default=1)
    max_soft_angle_3: bpy.props.FloatProperty(name="最大柔角 3", default=1)
    rotation_speed: bpy.props.FloatProperty(name="旋转速度")
    rotation_strength: bpy.props.FloatProperty(name="旋转强度")
    restoring_strength: bpy.props.FloatProperty(name="恢复强度")
    restoring_max_torque: bpy.props.FloatProperty(name="恢复最大扭矩")
    latch_strength: bpy.props.FloatProperty(name="锁定强度")
    min_damage_force: bpy.props.FloatProperty(name="最小破坏力", default=100)
    damage_health: bpy.props.FloatProperty(name="破坏生命值", default=1000)
    weapon_health: bpy.props.FloatProperty(name="武器生命值")
    weapon_scale: bpy.props.FloatProperty(name="武器缩放", default=1)
    vehicle_scale: bpy.props.FloatProperty(name="载具缩放", default=1)
    ped_scale: bpy.props.FloatProperty(name="行人缩放", default=1)
    ragdoll_scale: bpy.props.FloatProperty(name="布娃娃缩放", default=1)
    explosion_scale: bpy.props.FloatProperty(name="爆炸缩放", default=1)
    object_scale: bpy.props.FloatProperty(name="对象缩放", default=1)
    ped_inv_mass_scale: bpy.props.FloatProperty(name="行人反质量缩放", default=1)
    melee_scale: bpy.props.FloatProperty(name="近战缩放", default=1)


class ChildProperties(bpy.types.PropertyGroup):
    mass: bpy.props.FloatProperty(name="Mass", min=0)
    damaged: bpy.props.BoolProperty(name="Damaged")

    window_mat: bpy.props.PointerProperty(
        type=bpy.types.Material, name="车窗材质", description="The material of the window mesh (usually a vehglass shader)")
    is_veh_window: bpy.props.BoolProperty(
        name="是否为玻璃车窗")


class VehicleWindowProperties(bpy.types.PropertyGroup):
    data_min: bpy.props.FloatProperty(name="数据最小")
    data_max: bpy.props.FloatProperty(name="数据最大")
    cracks_texture_tiling: bpy.props.FloatProperty(name="裂纹贴图平铺", default=1.5)


class VehiclePaintLayer(IntEnum):
    CUSTOM = 0
    PRIMARY = 1
    SECONDARY = 2
    PEARLESCENT = 3
    WHEEL = 4
    DEFAULT = 5
    INTERIOR_TRIM = 6
    INTERIOR_DASH = 7

    @property
    def ui_label(self) -> str:
        match self:
            case VehiclePaintLayer.CUSTOM:
                return "Custom - Not Paintable"
            case VehiclePaintLayer.PRIMARY:
                return "Primary"
            case VehiclePaintLayer.SECONDARY:
                return "Secondary"
            case VehiclePaintLayer.PEARLESCENT:
                return "Pearlescent"
            case VehiclePaintLayer.WHEEL:
                return "Wheel"
            case VehiclePaintLayer.DEFAULT:
                return "Default - Not Paintable"
            case VehiclePaintLayer.INTERIOR_TRIM:
                return "Interior Trim"
            case VehiclePaintLayer.INTERIOR_DASH:
                return "Dashboard"
            case _:
                assert False, f"Unknown paint layer {self}"


VehiclePaintLayerEnumItems = tuple((enum.name, enum.ui_label, desc, enum.value) for enum, desc in (
    (VehiclePaintLayer.CUSTOM,
        "Custom - cannot be painted at mod shops. Use 'matDiffuseColor' parameter as paint color"),
    (VehiclePaintLayer.DEFAULT,
        "Default - cannot be painted at mod shops. Use white as paint color, or grey when vehicle is scorched"),
    (VehiclePaintLayer.PRIMARY,
        "Use Primary paint color on this material"),
    (VehiclePaintLayer.SECONDARY,
        "Use Secondary paint color on this material"),
    (VehiclePaintLayer.PEARLESCENT,
        "Use Pearlescent paint color on this material. Note, this does not apply the pearlescent effect, but simply "
        "use the color chosen for pearlescent to paint this material as well"),
    (VehiclePaintLayer.WHEEL,
        "Use Wheel paint color on this material"),
    (VehiclePaintLayer.INTERIOR_TRIM,
        "Use Interior Trim paint color on this material"),
    (VehiclePaintLayer.INTERIOR_DASH,
        "Use Interior Dashboard paint color on this material"),
))


class VehicleRenderPreview(bpy.types.PropertyGroup):
    DEFAULT_DIRT_COLOR = (70/255, 60/255, 50/255)
    DEFAULT_BODY_COLOR = (1.0, 1.0, 1.0)

    def _on_each_node_tree(self, callback, callback_context):
        # NOTE: obj may be a fragment or drawable, both can use vehicle shaders
        obj = self.id_data
        if not obj:
            return

        materials_visited = set()
        for child_obj in obj.children_recursive:
            if child_obj.type != "MESH":
                continue

            mesh = child_obj.data
            for material in mesh.materials:
                if material is None or material in materials_visited:
                    continue

                materials_visited.add(material)

                node_tree = material.node_tree
                if node_tree is None:
                    continue

                callback(node_tree, callback_context)

    @staticmethod
    def _dirt_level_update_callback():
        def _apply(node_tree, value):
            node = node_tree.nodes.get(VEHICLE_PREVIEW_NODE_DIRT_LEVEL, None)
            if node is None:
                return

            node.outputs[0].default_value = value

        def _update(self, context):
            value = self.dirt_level
            self._on_each_node_tree(_apply, value)

        return _update

    @staticmethod
    def _dirt_wetness_update_callback():
        def _apply(node_tree, value):
            node = node_tree.nodes.get(VEHICLE_PREVIEW_NODE_DIRT_WETNESS, None)
            if node is None:
                return

            node.outputs[0].default_value = value

        def _update(self, context):
            value = self.dirt_wetness
            self._on_each_node_tree(_apply, value)

        return _update

    @staticmethod
    def _dirt_color_update_callback():
        def _apply(node_tree, value):
            node = node_tree.nodes.get(VEHICLE_PREVIEW_NODE_DIRT_COLOR, None)
            if node is None:
                return

            node.inputs[0].default_value = value[0]
            node.inputs[1].default_value = value[1]
            node.inputs[2].default_value = value[2]

        def _update(self, context):
            value = self.dirt_color
            self._on_each_node_tree(_apply, value)

        return _update

    dirt_level: bpy.props.FloatProperty(
        name="污垢程度",
        min=0.0, max=1.0,
        subtype="FACTOR",
        default=0.0,
        update=_dirt_level_update_callback(),
    )

    dirt_wetness: bpy.props.FloatProperty(
        name="污垢湿润度",
        min=0.0, max=1.0,
        subtype="FACTOR",
        default=0.0,
        update=_dirt_wetness_update_callback(),
    )

    dirt_color: bpy.props.FloatVectorProperty(
        name="污垢颜色",
        min=0.0, max=1.0,
        size=3, subtype="COLOR",
        default=DEFAULT_DIRT_COLOR,
        update=_dirt_color_update_callback(),
    )

    @staticmethod
    def _define_light_id_property(light_id: int):
        prop_name = f"light_id_{light_id}"
        node_name = VEHICLE_PREVIEW_NODE_LIGHT_EMISSIVE_TOGGLE[light_id]

        def _apply(node_tree, value):
            node = node_tree.nodes.get(node_name, None)
            if node is None:
                return

            node.outputs[0].default_value = value

        def _update(self, context):
            value = 1.0 if self[prop_name] else 0.0

            self._on_each_node_tree(_apply, value)

        VehicleRenderPreview.__annotations__[prop_name] = bpy.props.BoolProperty(
            name=SOLLUMZ_UI_NAMES[VehicleLightID(str(light_id))],
            default=True,
            update=_update,
        )

    @staticmethod
    def _define_body_color_property(paint_layer_id: int):
        prop_name = f"body_color_{paint_layer_id}"
        node_name = VEHICLE_PREVIEW_NODE_BODY_COLOR[paint_layer_id]

        def _apply(node_tree, value):
            node = node_tree.nodes.get(node_name, None)
            if node is None:
                return

            node.inputs[0].default_value = value[0]
            node.inputs[1].default_value = value[1]
            node.inputs[2].default_value = value[2]

        def _update(self, context):
            value = self[prop_name]

            self._on_each_node_tree(_apply, value)

        VehicleRenderPreview.__annotations__[prop_name] = bpy.props.FloatVectorProperty(
            name=VehiclePaintLayer(paint_layer_id).ui_label,
            min=0.0, max=1.0,
            size=3, subtype="COLOR",
            default=VehicleRenderPreview.DEFAULT_BODY_COLOR,
            update=_update,
        )


for light_id in range(MIN_VEHICLE_LIGHT_ID, MAX_VEHICLE_LIGHT_ID+1):
    VehicleRenderPreview._define_light_id_property(light_id)
for paint_layer_id in range(1, 7+1):
    VehicleRenderPreview._define_body_color_property(paint_layer_id)


class ClothTuningFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 11

    wind_feedback: bpy.props.BoolProperty(
        name="风反馈",
        description="基于风向旋转对象。参见 'prop_air_windsock' 对象示例",
        update=FlagPropertyGroup.update_flag
    )
    flip_indices_order: bpy.props.BoolProperty(
        name="翻转索引顺序",
        description="???",
        update=FlagPropertyGroup.update_flag
    )
    # actually CLOTH_TUNE_IGNORE_DISTURBANCES but that name doesn't make sense given what this flag actually does
    flip_wind: bpy.props.BoolProperty(
        name="翻转风",
        description="反转风力方向",
        update=FlagPropertyGroup.update_flag
    )
    is_in_interior: bpy.props.BoolProperty(
        name="在室内",
        description="禁用风力",
        update=FlagPropertyGroup.update_flag
    )
    no_ped_collision: bpy.props.BoolProperty(
        name="无行人碰撞",
        description="禁用布料与行人的交互",
        update=FlagPropertyGroup.update_flag
    )
    use_distance_threshold: bpy.props.BoolProperty(
        name="使用距离阈值",
        description="???. Not compatible with 'Force Vertex Resistance'",
        update=FlagPropertyGroup.update_flag
    )
    clamp_horizontal_force: bpy.props.BoolProperty(
        name="限制水平力",
        description="忽略 X 和 Y 轴上的力",
        update=FlagPropertyGroup.update_flag
    )
    flip_gravity: bpy.props.BoolProperty(
        name="翻转重力",
        description="反转重力方向",
        update=FlagPropertyGroup.update_flag
    )
    activate_on_hit: bpy.props.BoolProperty(
        name="被击中时激活",
        description="???",
        update=FlagPropertyGroup.update_flag
    )
    force_vertex_resistance: bpy.props.BoolProperty(
        name="强制顶点阻力",
        description="???. Not compatible with 'Use Distance Threshold'",
        update=FlagPropertyGroup.update_flag
    )
    update_if_visible: bpy.props.BoolProperty(
        name="可见时更新",
        description="仅在对象可见时执行布料模拟",
        update=FlagPropertyGroup.update_flag
    )


class ClothProperties(bpy.types.PropertyGroup):
    def _world_bounds_filter(self, obj: Object) -> bool:
        return obj.sollum_type == SollumType.BOUND_COMPOSITE and obj.parent is None

    world_bounds: PointerProperty(
        type=Object, poll=_world_bounds_filter,
        name="世界边界",
        description=(
            f"{SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]} the cloth will collide with. These bounds should be "
            "positioned at world coordinates.\n\n"
            f"Only {SOLLUMZ_UI_NAMES[SollumType.BOUND_CAPSULE]} and {SOLLUMZ_UI_NAMES[SollumType.BOUND_PLANE]} "
            "types are supported.\n\n"
            "Cloth simulation does not interact with regular world collisions due to performance optimizations. "
            "Instead, these simplified bounds are used, typically consisting of a single plane behind the cloth to "
            "prevent it from clipping into buildings"
        )
    )

    weight: FloatProperty(name="权重", default=1.0)
    enable_tuning: BoolProperty(name="调校")
    tuning_flags: PointerProperty(type=ClothTuningFlags)
    extra_force: FloatVectorProperty(
        name="额外力",
        description="施加到布料上的额外力",
        subtype="XYZ",
        size=3
    )
    weight_override: FloatProperty(
        name="权重覆盖",
        description="如果为正，覆盖布料质量",
        default=-1.0
    )
    distance_threshold: FloatProperty(
        name="距离阈值或顶点阻力",
        description=(
            "When the flag 'Use Distance Threshold' is enabled, this is the distance threshold value used. When the "
            "flag 'Force Vertex Resistance' is enabled, this is the vertex resistance value used. Otherwise, has no "
            "effect"
        )
    )
    # Wind feedback-specific properties
    rotation_rate: FloatProperty(
        name="旋转速率",
        description="将对象旋转至风向的速率",
        default=3.14159274,
        subtype="ANGLE",
        unit="ROTATION"
    )
    angle_threshold: FloatProperty(
        name="角度阈值",
        description="停止将对象从目标风向旋转的最大角度",
        default=0.5235988,
        subtype="ANGLE",
        unit="ROTATION"
    )
    pin_vert: IntProperty(
        name="固定顶点",
        description=(
            "Index of a pinned vertex of the cloth. Used along with the middle-point of the other two non-pinned "
            "vertices to determine the current cloth direction"
        )
    )
    non_pin_vert0: IntProperty(
        name="非固定顶点 0",
        description=(
            "Index of a non-pinned vertex of the cloth. Used along with the other two pinned and non-pinned vertices "
            "to determine the current cloth direction"
        )
    )
    non_pin_vert1: IntProperty(
        name="非固定顶点 1",
        description=(
            "Index of a non-pinned vertex of the cloth. Used along with the other two pinned and non-pinned vertices "
            "to determine the current cloth direction"
        )
    )


FragmentTemplateAssetEnumItems = tuple((enum.name, label, desc, enum.value) for enum, label, desc in (
    (FragmentTemplateAsset.NONE, "无", "Use physics defined in this fragment"),
    (FragmentTemplateAsset.FRED, "Fred", "Use 'z_z_fred' physics"),
    (FragmentTemplateAsset.WILMA, "Wilma", "Use 'z_z_wilma' physics"),
    (FragmentTemplateAsset.FRED_LARGE, "Fred (Large)", "Use 'z_z_fred_large' physics"),
    (FragmentTemplateAsset.WILMA_LARGE, "Wilma (Large)", "Use 'z_z_wilma_large' physics"),
    (FragmentTemplateAsset.ALIEN, "Alien", "Use 'z_z_alien' physics"),
))


class FragmentProperties(bpy.types.PropertyGroup):
    unbroken_elasticity: bpy.props.FloatProperty(name="未破损弹性")
    gravity_factor: bpy.props.FloatProperty(name="重力系数", default=1.0)
    buoyancy_factor: bpy.props.FloatProperty(name="浮力系数", default=1.0)
    template_asset: bpy.props.EnumProperty(
        name="物理模板（仅行人）", items=FragmentTemplateAssetEnumItems,
        default=FragmentTemplateAsset.NONE.name
    )

    lod_properties: bpy.props.PointerProperty(type=LODProperties)

    cloth: bpy.props.PointerProperty(type=ClothProperties)

    vehicle_render_preview: bpy.props.PointerProperty(type=VehicleRenderPreview)


def get_light_id_of_selection(self):
    face_mode = bpy.context.scene.tool_settings.mesh_select_mode[2]

    if not face_mode or bpy.context.mode != "EDIT_MESH":
        return -1

    mesh_objs = bpy.context.objects_in_mode_unique_data[:]
    if not mesh_objs:
        return -1

    light_id = -1

    for obj in mesh_objs:
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        try:
            if not bm.loops.layers.color:
                continue

            color_layer = bm.loops.layers.color[0]

            for face in bm.faces:
                if not face.select:
                    continue

                for loop in face.loops:
                    loop_light_id = int(loop[color_layer][3] * 255)

                    if light_id != -1 and loop_light_id != light_id:
                        return -1
                    elif loop_light_id != light_id and light_id == -1:
                        light_id = loop_light_id
        finally:
            # Make sure the bmesh is freed after each loop iteration. It can crash
            # while the user edits the mesh otherwise.
            bm.free()

    return light_id


def register():
    bpy.types.Object.fragment_properties = bpy.props.PointerProperty(
        type=FragmentProperties)
    bpy.types.Object.child_properties = bpy.props.PointerProperty(
        type=ChildProperties)
    bpy.types.Object.vehicle_window_properties = bpy.props.PointerProperty(
        type=VehicleWindowProperties)
    bpy.types.Object.sollumz_is_physics_child_mesh = bpy.props.BoolProperty(
        name="是物理子级", description="Whether or not this fragment mesh is a physics child. Usually wheels meshes are physics children")

    bpy.types.Scene.create_fragment_type = bpy.props.EnumProperty(
        items=[
            (SollumType.FRAGMENT.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGMENT], "Create a fragment object"),
            (SollumType.FRAGLOD.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGLOD], "Create a fragment LOD object"),
            (SollumType.FRAGGROUP.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGGROUP], "Create a fragment group object"),
            (SollumType.FRAGCHILD.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGCHILD], "Create a fragment child object"),
        ],
        name="类型",
        default=SollumType.FRAGMENT.value
    )

    bpy.types.Bone.group_properties = bpy.props.PointerProperty(
        type=GroupProperties)
    bpy.types.Bone.sollumz_use_physics = bpy.props.BoolProperty(
        name="使用物理", description="Whether or not to use physics for this fragment bone")

    bpy.types.Scene.create_bones_fragment = bpy.props.PointerProperty(type=bpy.types.Object,
                                                                      name="碎片", description="The Fragment to add the bones to")
    bpy.types.Scene.create_bones_parent_to_selected = bpy.props.BoolProperty(
        name="父级到所选骨骼", description="Parent all bones to the currently selected bone")
    bpy.types.Scene.set_mass_amount = bpy.props.FloatProperty(
        name="Mass", description="Mass", min=0)

    bpy.types.Scene.set_vehicle_light_id = bpy.props.EnumProperty(items=items_from_enums(
        VehicleLightID, exclude=VehicleLightID.NONE), name="载具灯光 ID", description="Determines which action causes the emissive shader to activate (this is stored in the alpha channel of the vertex colors)")
    bpy.types.Scene.select_vehicle_light_id = bpy.props.EnumProperty(items=items_from_enums(
        VehicleLightID, exclude=VehicleLightID.NONE), name="载具灯光 ID", description="Determines which action causes the emissive shader to activate (this is stored in the alpha channel of the vertex colors)")
    bpy.types.Scene.set_custom_vehicle_light_id = bpy.props.IntProperty(
        name="自定义")
    bpy.types.Scene.select_custom_vehicle_light_id = bpy.props.IntProperty(
        name="自定义")
    bpy.types.Scene.selected_vehicle_light_id = bpy.props.IntProperty(
        name="灯光 ID", get=get_light_id_of_selection)

    bpy.types.Material.sz_paint_layer = bpy.props.EnumProperty(
        name="绘制层",
        items=VehiclePaintLayerEnumItems,
        default=VehiclePaintLayer.CUSTOM.value,
        get=get_vehicle_material_paint_layer,
        set=set_vehicle_material_paint_layer,
        update=lambda self, context: update_vehicle_material_paint_name(self),
    )


def unregister():
    del bpy.types.Object.fragment_properties
    del bpy.types.Object.child_properties
    del bpy.types.Object.vehicle_window_properties
    del bpy.types.Object.sollumz_is_physics_child_mesh

    del bpy.types.Bone.group_properties
    del bpy.types.Bone.sollumz_use_physics

    del bpy.types.Scene.create_bones_fragment
    del bpy.types.Scene.create_bones_parent_to_selected
    del bpy.types.Scene.set_mass_amount
    del bpy.types.Scene.set_vehicle_light_id
    del bpy.types.Scene.select_vehicle_light_id
    del bpy.types.Scene.set_custom_vehicle_light_id
    del bpy.types.Scene.select_custom_vehicle_light_id
    del bpy.types.Scene.selected_vehicle_light_id
    del bpy.types.Material.sz_paint_layer
