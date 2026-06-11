"""
生成"当前热点"模拟场景（用于大规模演练 / 真实运行）

根据一个热点话题，批量生成带有不同立场（支持/反对/中立/围观）的 agent 人设，
以及一份可直接被 ``run_parallel_simulation.py`` 读取的 ``simulation_config.json``，
并配置：
  - active_fraction —— 让活跃规模随人群规模等比增长（大规模场景下人群不再静止）
  - initial_posts   —— 话题的种子帖
  - scheduled_events —— 模拟中途自动触发的"事态升级"事件

用法::

    # 生成一个 500 agent 的热点场景到指定目录
    python make_scenario.py --topic "某城市新出台的限行政策" --agents 500 \
        --platform reddit --rounds 20 --out /tmp/sim_trending

    # 不消耗 LLM 额度地大规模演练该场景
    python run_parallel_simulation.py --config /tmp/sim_trending/simulation_config.json \
        --reddit-only --dry-run --no-wait

此脚本仅生成离线文件，不依赖 oasis / LLM / 网络。
"""

import argparse
import csv
import json
import os
import random
import uuid
from datetime import datetime

# 立场分布（围观者占多数，更贴近真实社媒）
STANCES = ["support", "oppose", "neutral", "observer"]
STANCE_WEIGHTS = [0.25, 0.20, 0.15, 0.40]

PROFESSIONS = [
    "学生", "教师", "工程师", "记者", "个体经营者", "公务员", "医生",
    "设计师", "退休人员", "自由职业者", "销售", "程序员", "律师", "司机",
]
COUNTRIES = ["CN", "US", "UK", "JP", "DE", "SG", "CA", "AU"]
GENDERS = ["male", "female", "other"]
MBTIS = ["INTP", "ENFP", "ISTJ", "ESFJ", "INTJ", "ENTP", "ISFP", "ESTP"]

STANCE_BIO = {
    "support": "对{topic}持积极支持态度，倾向于传播正面信息",
    "oppose": "对{topic}持批评态度，常指出潜在问题",
    "neutral": "对{topic}保持中立，喜欢理性分析多方观点",
    "observer": "对{topic}保持关注但较少主动发声，偶尔转发或点赞",
}

# 不同立场的活跃度（observer 最低）
STANCE_ACTIVITY = {
    "support": (0.45, 0.85),
    "oppose": (0.45, 0.85),
    "neutral": (0.30, 0.60),
    "observer": (0.10, 0.35),
}


def _rand_active_hours():
    """随机生成一段连续的活跃时段。"""
    start = random.randint(6, 12)
    length = random.randint(8, 14)
    return [(start + i) % 24 for i in range(length)]


def build_agents(n: int, topic: str):
    """生成 n 个 agent 的人设 + 对应的 agent_config。"""
    profiles = []
    agent_configs = []
    for i in range(n):
        stance = random.choices(STANCES, weights=STANCE_WEIGHTS, k=1)[0]
        name = f"网友{i:04d}"
        username = f"user_{i:04d}"
        bio = STANCE_BIO[stance].format(topic=topic)
        persona = (
            f"你是一名{random.choice(PROFESSIONS)}，立场为「{stance}」。"
            f"在讨论『{topic}』时，{bio}。请符合该人设发言。"
        )
        lo, hi = STANCE_ACTIVITY[stance]
        activity_level = round(random.uniform(lo, hi), 2)

        profiles.append({
            "user_id": i,
            "username": username,
            "name": name,
            "bio": bio,
            "persona": persona,
            "age": random.randint(18, 65),
            "gender": random.choice(GENDERS),
            "mbti": random.choice(MBTIS),
            "country": random.choice(COUNTRIES),
            "profession": random.choice(PROFESSIONS),
            "interested_topics": [topic],
            "stance": stance,
        })
        agent_configs.append({
            "agent_id": i,
            "entity_name": name,
            "active_hours": _rand_active_hours(),
            "activity_level": activity_level,
            "stance": stance,
        })
    return profiles, agent_configs


def build_config(topic, agent_configs, n, rounds, platform):
    """构造 simulation_config.json 内容。"""
    # 选几个高活跃 agent 作为种子发帖者
    seed_agents = [c["agent_id"] for c in agent_configs[: min(5, n)]]
    initial_posts = [
        {"poster_agent_id": seed_agents[0],
         "content": f"【热议】关于『{topic}』，大家怎么看？"},
    ]
    if len(seed_agents) > 1:
        initial_posts.append(
            {"poster_agent_id": seed_agents[1],
             "content": f"刚刚看到『{topic}』的消息，感觉会有不小影响。"}
        )

    # 中途自动触发的"事态升级"定时事件
    scheduled_events = [
        {"id": "escalation-1", "trigger_round": max(2, rounds // 3),
         "content": f"【最新进展】『{topic}』出现新情况，引发更多讨论。",
         "platform": "both", "description": "事态升级"},
        {"id": "official-1", "trigger_round": max(3, (rounds * 2) // 3),
         "content": f"【官方回应】有关部门就『{topic}』作出正式回应。",
         "platform": "both", "description": "官方回应"},
    ]

    # active_fraction 让活跃规模随人群规模增长；max_active_per_round 作为保护上限
    active_fraction = 0.12
    max_active = max(30, int(n * 0.25))

    return {
        "simulation_id": f"scn_{uuid.uuid4().hex[:10]}",
        "project_id": "trending-scenario",
        "graph_id": "",
        "llm_model": "gpt-4o-mini",
        "generated_at": datetime.now().isoformat(),
        "scenario_topic": topic,
        "time_config": {
            # minutes_per_round=60 时 total_rounds == total_simulation_hours，
            # 因此让 --rounds 直接决定运行轮数
            "total_simulation_hours": max(1, rounds),
            "minutes_per_round": 60,
            "agents_per_hour_min": 5,
            "agents_per_hour_max": 20,
            "peak_hours": [9, 10, 11, 14, 15, 20, 21, 22],
            "off_peak_hours": [0, 1, 2, 3, 4, 5],
            "peak_activity_multiplier": 1.5,
            "off_peak_activity_multiplier": 0.3,
            "active_fraction": active_fraction,
            "max_active_per_round": max_active,
        },
        "agent_configs": agent_configs,
        "event_config": {
            "initial_posts": initial_posts,
            "scheduled_events": scheduled_events,
            "hot_topics": [topic],
            "narrative_direction": f"围绕『{topic}』的舆论自然演化",
        },
    }


def write_reddit_profiles(path, profiles):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def write_twitter_profiles(path, profiles):
    """OASIS twitter 读取 CSV，需要 username / description / user_char 列。"""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "username", "name", "description", "user_char"])
        for p in profiles:
            writer.writerow([
                p["user_id"], p["username"], p["name"], p["bio"], p["persona"],
            ])


def main():
    parser = argparse.ArgumentParser(description="生成当前热点模拟场景")
    parser.add_argument("--topic", required=True, help="热点话题")
    parser.add_argument("--agents", type=int, default=200, help="agent 数量")
    parser.add_argument("--rounds", type=int, default=20, help="计划模拟轮数（影响定时事件时间点）")
    parser.add_argument("--platform", choices=["reddit", "twitter", "both"], default="reddit")
    parser.add_argument("--out", required=True, help="输出目录")
    parser.add_argument("--seed", type=int, default=None, help="随机种子（可复现）")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    os.makedirs(args.out, exist_ok=True)
    profiles, agent_configs = build_agents(args.agents, args.topic)
    config = build_config(args.topic, agent_configs, args.agents, args.rounds, args.platform)

    if args.platform in ("reddit", "both"):
        write_reddit_profiles(os.path.join(args.out, "reddit_profiles.json"), profiles)
    if args.platform in ("twitter", "both"):
        write_twitter_profiles(os.path.join(args.out, "twitter_profiles.csv"), profiles)

    config_path = os.path.join(args.out, "simulation_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    only_flag = "" if args.platform == "both" else f"--{args.platform}-only "
    print(f"已生成场景: {args.agents} agents, 话题=『{args.topic}』")
    print(f"  配置文件: {config_path}")
    print(f"  active_fraction={config['time_config']['active_fraction']}, "
          f"max_active_per_round={config['time_config']['max_active_per_round']}")
    print("\n演练运行（不消耗 LLM 额度）:")
    print(f"  python {os.path.basename(__file__)} 所在目录的 run_parallel_simulation.py \\")
    print(f"    --config {config_path} {only_flag}--dry-run --no-wait")


if __name__ == "__main__":
    main()
