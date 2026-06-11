"""
模拟动态事件与"上帝视角"干预 (God's-eye-view interventions)

为运行中的模拟提供两类运行时事件注入能力：

1. 定时事件 (scheduled_events)
   配置文件 ``event_config.scheduled_events`` 中预设、在指定模拟时间自动触发的帖子。
   每个事件形如::

       {
           "id": "event-1",            # 可选，用于去重；缺省时使用列表索引
           "trigger_round": 12,        # 在第 12 轮（1-based，与动作日志一致）触发
           "trigger_hour": 9,          # 或：在模拟小时数首次等于 9 时触发
           "content": "突发：……",      # 帖子正文（必填）
           "poster_agent_id": 0,       # 可选，发帖 agent；缺省由引擎选择
           "platform": "both",         # 可选，twitter/reddit/both，默认 both
           "description": "政策变量"     # 可选，仅用于日志标注
       }

2. 实时干预 (interventions)
   模拟运行期间由用户通过 API 动态注入的帖子（突发新闻、政策变量等）。
   Flask 端调用 :func:`queue_intervention` 写入待处理队列，引擎端在每轮开始时
   调用 :func:`drain_pending_interventions` 取出并注入。

本模块刻意不依赖 ``oasis`` 或 Flask ``app`` 包，因此既能被模拟脚本
（``backend/scripts/run_parallel_simulation.py``）以同级模块方式导入，也能被
Flask 后端导入，并且可以独立进行单元测试。真正的"动作"注入（通过
``ManualAction(CREATE_POST)`` 调用 OASIS）由调用方完成。
"""

import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# 干预队列在模拟目录下的子目录名
INTERVENTIONS_DIRNAME = "interventions"

# 合法的平台
_VALID_PLATFORMS = ("twitter", "reddit")


def normalize_platform(platform: Optional[str]) -> List[str]:
    """
    将平台参数归一化为目标平台列表。

    - None / "both" / "all" / "" -> ["twitter", "reddit"]
    - "twitter" -> ["twitter"]
    - "reddit"  -> ["reddit"]
    其它值抛出 ValueError。
    """
    if platform is None:
        return list(_VALID_PLATFORMS)
    p = str(platform).strip().lower()
    if p in ("", "both", "all"):
        return list(_VALID_PLATFORMS)
    if p in _VALID_PLATFORMS:
        return [p]
    raise ValueError(f"无效的平台: {platform}")


def _event_matches_platform(event: Dict[str, Any], platform: str) -> bool:
    """判断定时事件是否适用于给定平台。"""
    targets = normalize_platform(event.get("platform"))
    return platform in targets


def select_due_events(
    scheduled_events: Optional[List[Dict[str, Any]]],
    round_num: int,
    simulated_hour: int,
    fired_ids: set,
    platform: Optional[str] = None,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    返回当前轮应当触发的定时事件（纯函数，便于测试）。

    触发条件（满足任一即触发，``trigger_round`` 优先于 ``trigger_hour``）：
      - ``trigger_round``: 在该轮（1-based）触发
      - ``trigger_hour``:  在模拟小时数等于该值时触发

    已在 ``fired_ids`` 中的事件不会再次触发（去重，确保每个事件只注入一次）。
    没有 ``content`` 的事件会被忽略。

    Args:
        scheduled_events: 配置中的定时事件列表
        round_num: 当前轮次（1-based）
        simulated_hour: 当前模拟小时数 (0-23)
        fired_ids: 已触发事件 id 集合（本函数会读取，调用方负责在注入后加入）
        platform: 若指定，仅返回适用于该平台的事件

    Returns:
        ``[(event_id, event_dict), ...]``
    """
    due: List[Tuple[str, Dict[str, Any]]] = []
    for idx, ev in enumerate(scheduled_events or []):
        if not isinstance(ev, dict):
            continue

        ev_id = str(ev.get("id", idx))
        if ev_id in fired_ids:
            continue

        if platform is not None and not _event_matches_platform(ev, platform):
            continue

        if not (ev.get("content") or "").strip():
            continue

        triggered = False
        trigger_round = ev.get("trigger_round")
        trigger_hour = ev.get("trigger_hour")

        if trigger_round is not None:
            try:
                triggered = int(trigger_round) == int(round_num)
            except (TypeError, ValueError):
                triggered = False
        elif trigger_hour is not None:
            try:
                triggered = int(trigger_hour) == int(simulated_hour)
            except (TypeError, ValueError):
                triggered = False

        if triggered:
            due.append((ev_id, ev))

    return due


def _platform_dir(simulation_dir: str, platform: str) -> str:
    return os.path.join(simulation_dir, INTERVENTIONS_DIRNAME, platform)


def queue_intervention(
    simulation_dir: str,
    content: str,
    platform: Optional[str] = None,
    poster_agent_id: Optional[int] = None,
    label: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """
    将一次实时干预写入待处理队列（Flask 端调用）。

    干预以 JSON 文件形式落盘到 ``<simulation_dir>/interventions/<platform>/``，
    每个目标平台一份；引擎端的对应平台循环会原子地取走并注入。写入使用
    临时文件 + ``os.replace`` 保证读侧不会看到半写文件。

    Args:
        simulation_dir: 模拟目录
        content: 帖子正文
        platform: twitter / reddit / both（默认 both）
        poster_agent_id: 发帖 agent id（可选，缺省由引擎选择）
        label: 备注标签（可选，用于日志/报告标注）

    Returns:
        ``(intervention_id, targets)``
    """
    content = (content or "").strip()
    if not content:
        raise ValueError("干预内容不能为空")

    targets = normalize_platform(platform)
    intervention_id = uuid.uuid4().hex[:12]
    record = {
        "id": intervention_id,
        "content": content,
        "poster_agent_id": poster_agent_id,
        "label": label or "",
        "created_at": datetime.now().isoformat(),
    }

    for plat in targets:
        plat_dir = _platform_dir(simulation_dir, plat)
        os.makedirs(os.path.join(plat_dir, "processed"), exist_ok=True)
        path = os.path.join(plat_dir, f"{intervention_id}.json")
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
        os.replace(tmp_path, path)

    return intervention_id, targets


def drain_pending_interventions(simulation_dir: str, platform: str) -> List[Dict[str, Any]]:
    """
    取出并标记某平台所有待处理干预（引擎端调用）。

    每条干预被移动到 ``processed/`` 子目录，避免被重复注入。由于每个平台只由
    其对应的模拟循环消费，因此无需加锁即可保证不重复。

    Returns:
        按提交时间排序的干预记录列表（已消费）。
    """
    plat_dir = _platform_dir(simulation_dir, platform)
    if not os.path.isdir(plat_dir):
        return []

    processed_dir = os.path.join(plat_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    records: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(plat_dir)):
        if not name.endswith(".json"):
            continue
        src = os.path.join(plat_dir, name)
        if not os.path.isfile(src):
            continue
        try:
            with open(src, "r", encoding="utf-8") as f:
                record = json.load(f)
        except (json.JSONDecodeError, OSError):
            # 跳过损坏/半写文件，下一轮再试
            continue
        try:
            os.replace(src, os.path.join(processed_dir, name))
        except OSError:
            # 移动失败则跳过，避免重复注入
            continue
        records.append(record)

    return records


def resolve_active_count(
    n_candidates: int,
    absolute_target: int,
    active_fraction: float = 0.0,
    multiplier: float = 1.0,
    max_cap: int = 0,
) -> int:
    """
    计算本轮应激活的 agent 数量（纯函数，便于测试）。

    历史行为使用一个与人群规模无关的绝对值 ``absolute_target``（约 5-30），
    导致在"大量 agent"场景下绝大多数个体从不发声、人群几乎静止。

    引入 ``active_fraction`` 后，活跃规模可随候选人群规模等比增长：
        frac_target = round(n_candidates * active_fraction * multiplier)
        target      = max(absolute_target, frac_target)
    再受 ``max_cap`` 上限保护（>0 时生效），避免一次性激活过多 agent 压垮 LLM。

    - ``active_fraction <= 0`` 时退化为历史行为（仅用绝对值），保持向后兼容。
    - 返回值始终被裁剪到 ``[0, n_candidates]``。
    """
    if n_candidates <= 0:
        return 0

    target = max(0, int(absolute_target))
    if active_fraction and active_fraction > 0:
        frac_target = int(round(n_candidates * active_fraction * max(0.0, multiplier)))
        target = max(target, frac_target)

    if max_cap and max_cap > 0:
        target = min(target, int(max_cap))

    return max(0, min(target, n_candidates))
