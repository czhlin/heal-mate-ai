"""
领域核心层 (Core Domain): 用户上下文管理

本模块负责聚合用户的各类领域对象（配置、计划、任务、状态），
并对外提供一个统一的只读上下文 (UserContext)。
在架构设计中，UserContext 是无状态的、不可变的数据传输对象 (DTO/Value Object)，
它隔离了底层的数据存储与上层的视图渲染逻辑，避免了视图层直接耦合 Repository 导致的代码腐化。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from repos.tasks_repo import load_daily_tasks_by_id, load_latest_daily_tasks
from services.plan_service import load_latest_plan, load_plan_by_id
from services.profile_service import load_latest_user_profile, load_user_profile_by_id
from services.user_state_service import get_user_state


class UserStatus(Enum):
    """
    用户业务状态机 (Business State Machine)
    定义了用户在产品生命周期中所处的阶段，这决定了系统将引导用户进行哪一步操作。
    """

    NOT_STARTED = "NOT_STARTED"  # 新用户，尚未完成初始信息采集
    PROFILE_READY = "PROFILE_READY"  # 已有健康档案，但未生成或未激活干预计划
    PLAN_READY = "PLAN_READY"  # 核心功能阶段：已具备可执行的健康计划与日常任务


def get_user_status(user_id: str) -> UserStatus:
    """
    状态推断引擎：
    根据持久化的用户指针记录（类似于游标），动态推导出当前用户的阶段。
    """
    state = get_user_state(user_id)
    if not state:
        return UserStatus.NOT_STARTED

    if state.get("current_plan_id") and state.get("current_tasks_id"):
        return UserStatus.PLAN_READY

    if state.get("current_profile_id"):
        return UserStatus.PROFILE_READY

    return UserStatus.NOT_STARTED


@dataclass(frozen=True)
class UserContext:
    """
    用户领域聚合根 (Domain Aggregate Root / Context)
    frozen=True 保证了该对象的不可变性，确保在跨层传递（Core -> Service -> View）时
    不会被意外修改，维持数据流的单向性。
    """

    user_id: str
    state: dict[str, Any]
    status: UserStatus
    profile: dict[str, Any] | None
    plan: dict[str, Any] | None
    tasks: list


def load_user_context(user_id: str) -> UserContext:
    """
    上下文工厂方法 (Context Factory):
    采用 "指针优先 -> Fallback 兜底" 的策略加载用户数据。
    如果 state 表中记录了当前生效的版本（指针），则优先加载该版本；
    否则降级加载时间线上的最新版本。这种设计支持了未来可能的版本回溯功能。
    """
    state = get_user_state(user_id) or {}
    status = get_user_status(user_id)

    profile = None
    current_profile_id = state.get("current_profile_id")
    if current_profile_id:
        profile = load_user_profile_by_id(current_profile_id)
    if profile is None:
        profile = load_latest_user_profile(user_id)

    plan = None
    current_plan_id = state.get("current_plan_id")
    if current_plan_id:
        plan = load_plan_by_id(current_plan_id)
    if plan is None:
        plan = load_latest_plan(user_id)

    tasks = []
    current_tasks_id = state.get("current_tasks_id")
    if current_tasks_id:
        tasks = load_daily_tasks_by_id(current_tasks_id)
    if not tasks:
        tasks = load_latest_daily_tasks(user_id)

    return UserContext(
        user_id=user_id,
        state=state,
        status=status,
        profile=profile,
        plan=plan,
        tasks=tasks,
    )
