import bpy
from ...sollumz_properties import FlagPropertyGroup


class RoomFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 10

    flag1: bpy.props.BoolProperty(
        name="冻结载具", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="冻结行人", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="无方向光", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="无外部灯光", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="强制冻结", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="减少载具", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="减少行人", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="强制打开方向光", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="不渲染外部", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="镜面潜在可见", update=FlagPropertyGroup.update_flag)


class PortalFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 14

    flag1: bpy.props.BoolProperty(
        name="单向", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="链接内部", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Mirror", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="禁用时间周期修改器", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="镜面使用高成本着色器", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="仅低 LOD", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="门关闭时隐藏", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="镜面可见方向光", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="镜面使用 Portal 遍历", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="镜面地板", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="镜面可见外部视图", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="水面", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="水面延伸至地平线", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="使用光溢出", update=FlagPropertyGroup.update_flag)


class EntityFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="允许完全旋转", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="流送低优先级", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="禁用内嵌碰撞", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="父级 YMAP 中的 LOD", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="LOD 领养", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="静态实体", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="室内 LOD", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="未知 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="未知 9", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="未知 10", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="未知 11", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="未知 12", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="未知 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="未知 14", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="未知 15", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="LOD 使用备用淡出", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="不接触水面", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(name="不生成行人",
                                   update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="投射静态阴影", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="投射动态阴影", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="忽略日夜设置", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="禁用实体阴影", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="禁用实体，仍投射阴影", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="不在反射中渲染", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="仅在反射中渲染", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="不在水面反射中渲染", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="仅在水面反射中渲染", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="不在镜面反射中渲染", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="仅在镜面反射中渲染", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="未知 31", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="未知 32", update=FlagPropertyGroup.update_flag)

    # Cannot rename properties due to backward compatibility (or at least would need versioning).
    # Just create wrappers for the few flags we may directly use
    @property
    def lod_in_parent_map(self) -> bool:
        return self.flag4


class ArchetypeFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="湿路反射", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="不淡出", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="最后绘制", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="AI 可攀爬", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="抑制 HD TXD", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Static", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="禁用 Alpha 排序", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="防弹", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="是通用", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="有动画 (YCD)", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="UV 动画 (YCD)", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="仅阴影", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="破损模型", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="不投射阴影", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="投射贴图阴影", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="不与飞行物碰撞", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="双面渲染", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Dynamic", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(
        name="覆盖物理边界", update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="自动启动动画", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="有预反射水面代理", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="有水面反射的可绘制体代理", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="不提供 AI 掩体", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="不提供玩家掩体", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="是梯子（已弃用）", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="有布料", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="启用车门物理", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="导航中固定", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="行人不避让", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="使用环境缩放", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="是调试", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="有 Alpha 阴影", update=FlagPropertyGroup.update_flag)


class MloFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 16

    flag1: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Subway", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Office", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="允许奔跑", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="仅过场动画", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="锁定时 LOD", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="无水面反射", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="有低 LOD Portal", update=FlagPropertyGroup.update_flag)
