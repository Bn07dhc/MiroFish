"""
simulation 端点用到的纯辅助函数。

从 simulation.py 中抽离出来的、不涉及 Flask 路由装饰器的工具函数。
保持与原实现一致，仅做了导入路径调整。

将这些函数集中在独立模块中：
- 让 simulation.py 更聚焦于路由声明本身
- 便于单元测试（无需启动 Flask 应用即可导入）
- 后续如要进一步按主题拆分路由，helper 已是中立可复用层
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional, Tuple

from ..config import Config
from ..utils.logger import get_logger
from ..utils.validators import safe_join, validate_safe_identifier

logger = get_logger('mirofish.api.simulation.helpers')

# Interview prompt 优化前缀
# 添加此前缀可以避免 Agent 调用工具，直接用文本回复
INTERVIEW_PROMPT_PREFIX = (
    "结合你的人设、所有的过往记忆与行动，不调用任何工具直接用文本回复我："
)


def optimize_interview_prompt(prompt: str) -> str:
    """优化 Interview 提问，添加前缀避免 Agent 调用工具。

    Args:
        prompt: 原始提问

    Returns:
        优化后的提问（已存在前缀则不重复添加）
    """
    if not prompt:
        return prompt
    if prompt.startswith(INTERVIEW_PROMPT_PREFIX):
        return prompt
    return INTERVIEW_PROMPT_PREFIX + prompt


def check_simulation_prepared(simulation_id: str) -> Tuple[bool, dict]:
    """检查模拟是否已经准备完成。

    检查条件：
    1. state.json 存在且 status 为 "ready" 或后续状态
    2. 必要文件存在：reddit_profiles.json, twitter_profiles.csv, simulation_config.json

    注意：运行脚本(run_*.py)保留在 backend/scripts/ 目录，不再复制到模拟目录。

    Args:
        simulation_id: 模拟ID

    Returns:
        (is_prepared, info)
    """
    # 防止路径穿越：拒绝包含 '/'、'..'、空字节等非法字符的 simulation_id
    try:
        validate_safe_identifier(simulation_id, field_name='simulation_id')
        simulation_dir = safe_join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
    except ValueError as e:
        return False, {"reason": f"非法的 simulation_id: {e}"}

    if not os.path.exists(simulation_dir):
        return False, {"reason": "模拟目录不存在"}

    required_files = [
        "state.json",
        "simulation_config.json",
        "reddit_profiles.json",
        "twitter_profiles.csv",
    ]

    existing_files = []
    missing_files = []
    for f in required_files:
        file_path = os.path.join(simulation_dir, f)
        if os.path.exists(file_path):
            existing_files.append(f)
        else:
            missing_files.append(f)

    if missing_files:
        return False, {
            "reason": "缺少必要文件",
            "missing_files": missing_files,
            "existing_files": existing_files,
        }

    state_file = os.path.join(simulation_dir, "state.json")
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)

        status = state_data.get("status", "")
        config_generated = state_data.get("config_generated", False)

        logger.debug(
            f"检测模拟准备状态: {simulation_id}, status={status}, "
            f"config_generated={config_generated}"
        )

        prepared_statuses = [
            "ready", "preparing", "running", "completed", "stopped", "failed",
        ]
        if status in prepared_statuses and config_generated:
            profiles_file = os.path.join(simulation_dir, "reddit_profiles.json")

            profiles_count = 0
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                    profiles_count = (
                        len(profiles_data) if isinstance(profiles_data, list) else 0
                    )

            # 如果状态是 preparing 但文件已完成，自动更新状态为 ready
            if status == "preparing":
                try:
                    state_data["status"] = "ready"
                    state_data["updated_at"] = datetime.now().isoformat()
                    with open(state_file, 'w', encoding='utf-8') as f:
                        json.dump(state_data, f, ensure_ascii=False, indent=2)
                    logger.info(
                        f"自动更新模拟状态: {simulation_id} preparing -> ready"
                    )
                    status = "ready"
                except OSError as e:
                    logger.warning(f"自动更新状态失败: {e}")

            logger.info(
                f"模拟 {simulation_id} 检测结果: 已准备完成 "
                f"(status={status}, config_generated={config_generated})"
            )
            return True, {
                "status": status,
                "entities_count": state_data.get("entities_count", 0),
                "profiles_count": profiles_count,
                "entity_types": state_data.get("entity_types", []),
                "config_generated": config_generated,
                "created_at": state_data.get("created_at"),
                "updated_at": state_data.get("updated_at"),
                "existing_files": existing_files,
            }

        logger.warning(
            f"模拟 {simulation_id} 检测结果: 未准备完成 "
            f"(status={status}, config_generated={config_generated})"
        )
        return False, {
            "reason": (
                f"状态不在已准备列表中或config_generated为false: "
                f"status={status}, config_generated={config_generated}"
            ),
            "status": status,
            "config_generated": config_generated,
        }

    except (OSError, json.JSONDecodeError) as e:
        return False, {"reason": f"读取状态文件失败: {e}"}


def get_report_id_for_simulation(simulation_id: str) -> Optional[str]:
    """获取 simulation 对应的最新 report_id。

    遍历 reports 目录，找出 simulation_id 匹配的 report；如果有多个则按
    created_at 倒序返回最新的。

    Args:
        simulation_id: 模拟ID

    Returns:
        report_id 或 None
    """
    # reports 目录路径：backend/uploads/reports
    # __file__ 位于 app/api/_simulation_helpers.py，向上三级到 backend/
    reports_dir = os.path.join(
        os.path.dirname(__file__), '..', '..', 'uploads', 'reports'
    )
    if not os.path.exists(reports_dir):
        return None

    matching_reports = []

    try:
        for report_folder in os.listdir(reports_dir):
            report_path = os.path.join(reports_dir, report_folder)
            if not os.path.isdir(report_path):
                continue

            meta_file = os.path.join(report_path, "meta.json")
            if not os.path.exists(meta_file):
                continue

            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)

                if meta.get("simulation_id") == simulation_id:
                    matching_reports.append({
                        "report_id": meta.get("report_id"),
                        "created_at": meta.get("created_at", ""),
                        "status": meta.get("status", ""),
                    })
            except (OSError, json.JSONDecodeError):
                continue

        if not matching_reports:
            return None

        matching_reports.sort(
            key=lambda x: x.get("created_at", ""), reverse=True
        )
        return matching_reports[0].get("report_id")

    except OSError as e:
        logger.warning(f"查找 simulation {simulation_id} 的 report 失败: {e}")
        return None
