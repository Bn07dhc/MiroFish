"""
Convert LayeredSimSpec -> MiroFish simulation_config.json

This is the bridge between the layered spec and MiroFish's existing sim engine.
The converter produces the exact same JSON format that SimulationConfigGenerator outputs,
so the existing run_twitter_simulation.py / run_reddit_simulation.py work unchanged.
"""
import json
import random
import uuid
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from .schema import (
    LayeredSimSpec, ArchetypeSpec, NamedAgent,
    validate_spec, ActionWeights
)


def spec_to_config(spec: LayeredSimSpec, simulation_id: str = None) -> Dict[str, Any]:
    """
    Convert a LayeredSimSpec to MiroFish simulation_config.json format.

    Returns the same structure as SimulationConfigGenerator.generate_config()
    so the existing sim runners work unchanged.
    """
    errors = validate_spec(spec)
    if errors:
        raise ValueError(f"Invalid spec: {'; '.join(errors)}")

    if not simulation_id:
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"

    # Build agent configs
    agent_configs = _build_agent_configs(spec)

    # Build time config
    time_config = _build_time_config(spec)

    # Build event config
    event_config = _build_event_config(spec, agent_configs)

    # Build platform configs
    twitter_config = None
    reddit_config = None
    if "twitter" in spec.world.channels:
        twitter_config = {
            "platform": "twitter",
            "recency_weight": 0.4,
            "popularity_weight": 0.3,
            "relevance_weight": 0.3,
            "viral_threshold": 10,
            "echo_chamber_strength": 0.5,
        }
    if "reddit" in spec.world.channels:
        reddit_config = {
            "platform": "reddit",
            "recency_weight": 0.3,
            "popularity_weight": 0.4,
            "relevance_weight": 0.3,
            "viral_threshold": 15,
            "echo_chamber_strength": 0.6,
        }

    config = {
        "simulation_id": simulation_id,
        "project_id": f"layered_{spec.name}",
        "graph_id": "",  # No graph needed
        "simulation_requirement": spec.description or f"Layered sim: {spec.name}",
        "time_config": time_config,
        "agent_configs": agent_configs,
        "event_config": event_config,
        "twitter_config": twitter_config,
        "reddit_config": reddit_config,
        "llm_model": "",
        "llm_base_url": "",
        "generated_at": datetime.now().isoformat(),
        "generation_reasoning": f"Generated from layered spec '{spec.name}' v{spec.version}",
        # Layered-specific extensions (read by enhanced runner)
        "layered_spec": {
            "version": spec.version,
            "world": {
                "domain": spec.world.domain,
                "language": spec.world.language,
                "forces": [{"name": f.name, "description": f.description, "decay_rate": f.decay_rate, "threshold": f.threshold, "affects": f.affects} for f in spec.world.forces],
                "phases": [{"round": p.round, "name": p.name, "prompt_injection": p.prompt_injection, "affects": p.affects} for p in spec.world.phases],
                "events": [{"name": e.name, "type": e.type, "trigger_round": e.trigger_round, "probability_per_round": e.probability_per_round, "affects": e.affects, "effect": e.effect, "prompt_injection": e.prompt_injection} for e in spec.world.events],
            },
            "dynamics": {
                "action_weights": {
                    "like_post": spec.dynamics.action_weights.like_post,
                    "comment": spec.dynamics.action_weights.comment,
                    "create_post": spec.dynamics.action_weights.create_post,
                    "quote_post": spec.dynamics.action_weights.quote_post,
                    "repost": spec.dynamics.action_weights.repost,
                    "follow": spec.dynamics.action_weights.follow,
                    "do_nothing": spec.dynamics.action_weights.do_nothing,
                },
                "feed_recent_posts": spec.dynamics.feed_recent_posts,
                "feed_popular_posts": spec.dynamics.feed_popular_posts,
                "max_persona_chars": spec.dynamics.max_persona_chars,
                "prevent_self_quote": spec.dynamics.prevent_self_quote,
                "convergence": {
                    "enabled": spec.dynamics.convergence.enabled,
                    "min_rounds": spec.dynamics.convergence.min_rounds,
                    "action_rate_stability_threshold": spec.dynamics.convergence.action_rate_stability_threshold,
                    "topic_entropy_threshold": spec.dynamics.convergence.topic_entropy_threshold,
                    "check_window": spec.dynamics.convergence.check_window,
                },
            },
        },
    }

    return config


def _build_time_config(spec: LayeredSimSpec) -> Dict[str, Any]:
    """Build MiroFish time_config from spec dynamics"""
    total_agents = spec.population.total_agents
    if spec.population.mode == "named":
        total_agents = len(spec.population.named_agents)

    return {
        "total_simulation_hours": spec.dynamics.total_simulation_hours,
        "minutes_per_round": spec.dynamics.minutes_per_round,
        "agents_per_hour_min": max(3, total_agents // 5),
        "agents_per_hour_max": total_agents,
        "peak_hours": spec.dynamics.peak_hours,
        "peak_activity_multiplier": spec.dynamics.peak_multiplier,
        "off_peak_hours": spec.dynamics.off_peak_hours,
        "off_peak_activity_multiplier": spec.dynamics.off_peak_multiplier,
        "morning_hours": [6, 7, 8],
        "morning_activity_multiplier": 0.4,
        "work_hours": list(range(9, 19)),
        "work_activity_multiplier": 0.7,
    }


def _build_agent_configs(spec: LayeredSimSpec) -> List[Dict[str, Any]]:
    """Generate agent_configs from population spec"""
    agents = []
    agent_id = 0

    if spec.population.mode == "named":
        for na in spec.population.named_agents:
            agents.append({
                "agent_id": agent_id,
                "entity_uuid": f"named_{na.name.lower().replace(' ', '_')}",
                "entity_name": na.name,
                "entity_type": na.role,
                "activity_level": na.activity_level,
                "posts_per_hour": na.posts_per_hour,
                "comments_per_hour": na.comments_per_hour,
                "active_hours": na.active_hours,
                "response_delay_min": na.response_delay_min,
                "response_delay_max": na.response_delay_max,
                "sentiment_bias": na.sentiment_bias,
                "stance": na.stance,
                "influence_weight": na.influence_weight,
                # Layered extensions
                "role": na.role,
                "system_prompt": na.system_prompt,
                "temperature": na.temperature,
            })
            agent_id += 1
    else:
        # Template mode: generate agents from archetypes with variance
        variance = spec.population.variance
        for archetype in spec.population.archetypes:
            for i in range(archetype.count):
                # Apply variance
                al_var = variance.get("activity_level", 0.2)
                sb_var = variance.get("sentiment_bias", 0.3)
                iw_var = variance.get("influence_weight", 0.2)

                activity = _sample_range(archetype.activity_level_range, al_var)
                sentiment = _sample_range(archetype.sentiment_bias_range, sb_var)
                influence = _sample_range(archetype.influence_range, iw_var)
                posts = _sample_range(archetype.posts_per_hour_range, 0.1)
                comments = _sample_range(archetype.comments_per_hour_range, 0.1)

                # Cap system agent influence
                if archetype.name.lower() in ("system", "platform", "news_feed"):
                    influence = min(influence, spec.dynamics.max_system_agent_influence)

                # Stagger active hours slightly per agent
                hours = list(archetype.active_hours)
                if len(hours) > 4:
                    shift = random.randint(-1, 1)
                    hours = [max(0, min(23, h + shift)) for h in hours]

                agent_name = f"{archetype.name}_{i+1}"
                agents.append({
                    "agent_id": agent_id,
                    "entity_uuid": f"tmpl_{archetype.name}_{i}",
                    "entity_name": agent_name,
                    "entity_type": archetype.name,
                    "activity_level": round(activity, 2),
                    "posts_per_hour": round(posts, 1),
                    "comments_per_hour": round(comments, 1),
                    "active_hours": sorted(set(hours)),
                    "response_delay_min": 5,
                    "response_delay_max": 60,
                    "sentiment_bias": round(sentiment, 2),
                    "stance": _sentiment_to_stance(sentiment),
                    "influence_weight": round(influence, 2),
                    # Layered extensions
                    "role": archetype.name,
                    "system_prompt": archetype.system_prompt_template,
                    "temperature": archetype.temperature,
                })
                agent_id += 1

    return agents


def _build_event_config(spec: LayeredSimSpec, agent_configs: List[Dict]) -> Dict[str, Any]:
    """Build event_config from world model"""
    initial_posts = []

    # Generate initial posts from scheduled events at round 0
    for event in spec.world.events:
        if event.type == "scheduled" and event.trigger_round == 0:
            # Find a matching agent to post
            target_agents = _find_agents_by_role(agent_configs, event.affects)
            if target_agents:
                poster = random.choice(target_agents)
                initial_posts.append({
                    "poster_agent_id": poster["agent_id"],
                    "content": event.prompt_injection or event.name,
                })

    # If no initial posts defined, create one from narrative
    if not initial_posts and spec.world.narrative_direction and agent_configs:
        # Pick a high-influence agent
        sorted_agents = sorted(agent_configs, key=lambda a: a.get("influence_weight", 0), reverse=True)
        initial_posts.append({
            "poster_agent_id": sorted_agents[0]["agent_id"],
            "content": spec.world.narrative_direction[:500],
        })

    return {
        "initial_posts": initial_posts,
        "scheduled_events": [],
        "hot_topics": spec.world.hot_topics,
        "narrative_direction": spec.world.narrative_direction,
    }


def _sample_range(range_tuple, variance: float) -> float:
    """Sample a value from a range with additional variance"""
    low, high = range_tuple
    base = random.uniform(low, high)
    jitter = random.uniform(-variance, variance) * (high - low)
    return max(low * 0.5, min(high * 1.5, base + jitter))


def _sentiment_to_stance(sentiment: float) -> str:
    """Convert sentiment bias to stance label"""
    if sentiment > 0.3:
        return "supportive"
    elif sentiment < -0.3:
        return "opposing"
    elif abs(sentiment) < 0.1:
        return "observer"
    return "neutral"


def _find_agents_by_role(agent_configs: List[Dict], roles: List[str]) -> List[Dict]:
    """Find agents matching any of the given roles"""
    if not roles or "all" in roles:
        return agent_configs
    return [a for a in agent_configs if a.get("role", "").lower() in [r.lower() for r in roles]]


def save_config(config: Dict[str, Any], output_dir: str) -> str:
    """Save config to simulation_config.json in the output directory"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    config_file = output_path / "simulation_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return str(config_file)
