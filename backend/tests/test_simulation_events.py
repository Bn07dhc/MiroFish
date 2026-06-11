"""
simulation_events 单元测试

覆盖动态事件/干预的纯逻辑（无需 oasis 或 Flask）：
- select_due_events: 定时事件触发与去重
- normalize_platform: 平台归一化
- queue_intervention / drain_pending_interventions: 干预队列读写
"""

import os
import sys

import pytest

# 把 backend/scripts 加入路径，以便导入与模拟脚本共享的实现
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scripts")
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import simulation_events as se  # noqa: E402


# ----------------------- normalize_platform -----------------------

@pytest.mark.parametrize("value,expected", [
    (None, ["twitter", "reddit"]),
    ("both", ["twitter", "reddit"]),
    ("all", ["twitter", "reddit"]),
    ("", ["twitter", "reddit"]),
    ("twitter", ["twitter"]),
    ("reddit", ["reddit"]),
    ("TWITTER", ["twitter"]),
])
def test_normalize_platform_valid(value, expected):
    assert se.normalize_platform(value) == expected


def test_normalize_platform_invalid():
    with pytest.raises(ValueError):
        se.normalize_platform("facebook")


# ----------------------- select_due_events -----------------------

def test_select_due_events_by_round():
    events = [{"id": "e1", "trigger_round": 5, "content": "hi"}]
    fired = set()
    assert se.select_due_events(events, 4, 0, fired) == []
    due = se.select_due_events(events, 5, 0, fired)
    assert [eid for eid, _ in due] == ["e1"]


def test_select_due_events_dedup_via_fired_ids():
    events = [{"id": "e1", "trigger_round": 5, "content": "hi"}]
    fired = {"e1"}
    # 已触发的事件不再返回
    assert se.select_due_events(events, 5, 0, fired) == []


def test_select_due_events_by_hour():
    events = [{"id": "e1", "trigger_hour": 9, "content": "hi"}]
    fired = set()
    assert se.select_due_events(events, 3, 8, fired) == []
    due = se.select_due_events(events, 3, 9, fired)
    assert len(due) == 1


def test_select_due_events_round_takes_priority_over_hour():
    # 同时给出 round 与 hour 时，以 round 为准
    events = [{"id": "e1", "trigger_round": 2, "trigger_hour": 9, "content": "hi"}]
    fired = set()
    # hour 命中但 round 未命中 -> 不触发
    assert se.select_due_events(events, 1, 9, fired) == []
    assert len(se.select_due_events(events, 2, 0, fired)) == 1


def test_select_due_events_platform_filter():
    events = [{"id": "e1", "trigger_round": 1, "content": "hi", "platform": "twitter"}]
    fired = set()
    assert se.select_due_events(events, 1, 0, fired, platform="reddit") == []
    assert len(se.select_due_events(events, 1, 0, fired, platform="twitter")) == 1


def test_select_due_events_skips_empty_content_and_non_dict():
    events = [
        {"id": "e1", "trigger_round": 1, "content": "   "},  # 空白内容
        "not-a-dict",
        {"id": "e3", "trigger_round": 1, "content": "ok"},
    ]
    fired = set()
    due = se.select_due_events(events, 1, 0, fired)
    assert [eid for eid, _ in due] == ["e3"]


def test_select_due_events_uses_index_when_no_id():
    events = [{"trigger_round": 1, "content": "hi"}]
    fired = set()
    due = se.select_due_events(events, 1, 0, fired)
    assert due[0][0] == "0"  # 回退到索引


def test_select_due_events_handles_empty_and_none():
    assert se.select_due_events(None, 1, 0, set()) == []
    assert se.select_due_events([], 1, 0, set()) == []


# ----------------- queue / drain interventions -----------------

def test_queue_and_drain_roundtrip(tmp_path):
    sim_dir = str(tmp_path)
    iid, targets = se.queue_intervention(sim_dir, "breaking news", platform="both")
    assert targets == ["twitter", "reddit"]
    assert iid

    tw = se.drain_pending_interventions(sim_dir, "twitter")
    assert len(tw) == 1
    assert tw[0]["content"] == "breaking news"
    assert tw[0]["id"] == iid

    # 二次排空应为空（已移动到 processed）
    assert se.drain_pending_interventions(sim_dir, "twitter") == []
    # reddit 仍有一份待处理
    rd = se.drain_pending_interventions(sim_dir, "reddit")
    assert len(rd) == 1


def test_queue_single_platform(tmp_path):
    sim_dir = str(tmp_path)
    _, targets = se.queue_intervention(sim_dir, "x", platform="reddit")
    assert targets == ["reddit"]
    assert se.drain_pending_interventions(sim_dir, "twitter") == []
    assert len(se.drain_pending_interventions(sim_dir, "reddit")) == 1


def test_queue_preserves_fields(tmp_path):
    sim_dir = str(tmp_path)
    se.queue_intervention(
        sim_dir, "content", platform="twitter", poster_agent_id=7, label="policy"
    )
    rec = se.drain_pending_interventions(sim_dir, "twitter")[0]
    assert rec["poster_agent_id"] == 7
    assert rec["label"] == "policy"


def test_queue_empty_content_raises(tmp_path):
    with pytest.raises(ValueError):
        se.queue_intervention(str(tmp_path), "   ", platform="both")


def test_queue_writes_atomically_no_tmp_left(tmp_path):
    sim_dir = str(tmp_path)
    se.queue_intervention(sim_dir, "x", platform="twitter")
    plat_dir = os.path.join(sim_dir, se.INTERVENTIONS_DIRNAME, "twitter")
    leftovers = [n for n in os.listdir(plat_dir) if n.endswith(".tmp")]
    assert leftovers == []


def test_drain_missing_dir_returns_empty(tmp_path):
    assert se.drain_pending_interventions(str(tmp_path), "twitter") == []


# ----------------------- resolve_active_count -----------------------

def test_resolve_active_count_legacy_ignores_population():
    # active_fraction=0 -> 仅用绝对值，与人群规模无关（历史行为）
    assert se.resolve_active_count(1000, absolute_target=15, active_fraction=0.0) == 15
    assert se.resolve_active_count(50, absolute_target=15, active_fraction=0.0) == 15


def test_resolve_active_count_scales_with_population():
    # active_fraction>0 -> 随候选人群规模等比增长
    assert se.resolve_active_count(1000, absolute_target=15, active_fraction=0.10) == 100
    assert se.resolve_active_count(200, absolute_target=15, active_fraction=0.10) == 20


def test_resolve_active_count_takes_max_of_absolute_and_fraction():
    # 比例值低于绝对值时，取绝对值（保证最低活跃量）
    assert se.resolve_active_count(50, absolute_target=15, active_fraction=0.10) == 15


def test_resolve_active_count_applies_multiplier():
    assert se.resolve_active_count(100, absolute_target=0, active_fraction=0.20, multiplier=1.5) == 30
    assert se.resolve_active_count(100, absolute_target=0, active_fraction=0.20, multiplier=0.3) == 6


def test_resolve_active_count_respects_max_cap():
    assert se.resolve_active_count(1000, absolute_target=15, active_fraction=0.50, max_cap=120) == 120


def test_resolve_active_count_never_exceeds_candidates():
    assert se.resolve_active_count(10, absolute_target=50, active_fraction=0.0) == 10
    assert se.resolve_active_count(10, absolute_target=5, active_fraction=2.0) == 10


def test_resolve_active_count_zero_candidates():
    assert se.resolve_active_count(0, absolute_target=15, active_fraction=0.2) == 0
