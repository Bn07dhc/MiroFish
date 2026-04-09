"""
Layered Simulation Spec - Schema and Validation
Replaces graph-dependent config generation with a direct, deterministic spec format.
"""
import yaml
import json
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path

@dataclass
class Force:
    """Macro force that affects all agents"""
    name: str
    description: str = ""
    decay_rate: float = 0.0  # per round
    threshold: float = 0.0
    affects: List[str] = field(default_factory=list)  # archetype names

@dataclass
class WorldEvent:
    """Exogenous event - scheduled or probabilistic"""
    name: str
    type: str = "scheduled"  # "scheduled" or "probabilistic"
    trigger_round: Optional[int] = None  # for scheduled
    probability_per_round: float = 0.0  # for probabilistic
    affects: List[str] = field(default_factory=list)  # archetype names or "all"
    effect: str = ""  # description of effect
    prompt_injection: str = ""  # text injected into agent prompts when triggered

@dataclass
class PhaseTransition:
    """Phase change at a specific round"""
    round: int
    name: str
    prompt_injection: str  # text appended to all active agent prompts
    affects: List[str] = field(default_factory=list)  # empty = all agents

@dataclass
class WorldModel:
    """Layer 1: Static environment definition"""
    domain: str  # e.g. "attention_economy", "corporate_governance", "geopolitical"
    description: str = ""
    language: str = "en"  # "en", "zh", "ko" - output language for agents
    resources: List[str] = field(default_factory=list)  # abstract resources agents compete for
    channels: List[str] = field(default_factory=lambda: ["twitter"])
    forces: List[Force] = field(default_factory=list)
    events: List[WorldEvent] = field(default_factory=list)
    phases: List[PhaseTransition] = field(default_factory=list)
    hot_topics: List[str] = field(default_factory=list)
    narrative_direction: str = ""

@dataclass
class ArchetypeSpec:
    """Template for generating agents of a specific role"""
    name: str  # e.g. "broker", "amplifier", "skeptic", "consumer"
    count: int = 1
    description: str = ""
    # Role-specific system prompt template (injected into persona)
    system_prompt_template: str = ""
    # Parameter ranges (agents generated with variance within these)
    influence_range: tuple = (1.0, 1.5)
    activity_level_range: tuple = (0.4, 0.7)
    sentiment_bias_range: tuple = (-0.3, 0.3)
    temperature: float = 0.7
    posts_per_hour_range: tuple = (0.5, 2.0)
    comments_per_hour_range: tuple = (1.0, 3.0)
    active_hours: List[int] = field(default_factory=lambda: list(range(8, 23)))

@dataclass
class NamedAgent:
    """Explicit agent definition (for known entities like DCI sims)"""
    name: str
    role: str  # maps to archetype name
    description: str = ""
    system_prompt: str = ""  # overrides archetype template
    stance: str = "neutral"
    influence_weight: float = 1.0
    activity_level: float = 0.5
    sentiment_bias: float = 0.0
    temperature: float = 0.7
    posts_per_hour: float = 1.0
    comments_per_hour: float = 2.0
    active_hours: List[int] = field(default_factory=lambda: list(range(8, 23)))
    response_delay_min: int = 5
    response_delay_max: int = 60
    # Optional persona fields
    age: Optional[int] = None
    gender: Optional[str] = None
    mbti: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None

@dataclass
class PopulationSpec:
    """Layer 2: Agent population definition"""
    mode: str = "template"  # "template" (archetypes + variance) or "named" (explicit agents)
    total_agents: int = 30
    archetypes: List[ArchetypeSpec] = field(default_factory=list)
    named_agents: List[NamedAgent] = field(default_factory=list)
    # Within-archetype variance (applied when mode=template)
    variance: Dict[str, float] = field(default_factory=lambda: {
        "activity_level": 0.2,  # ±20%
        "sentiment_bias": 0.3,  # ±0.3
        "influence_weight": 0.2,  # ±20%
    })

@dataclass
class ActionWeights:
    """Forced action type probability distribution"""
    like_post: float = 0.40
    comment: float = 0.25
    create_post: float = 0.20
    quote_post: float = 0.10
    repost: float = 0.05
    follow: float = 0.00
    do_nothing: float = 0.00

@dataclass
class ConvergenceConfig:
    """Auto-detection of simulation steady state"""
    enabled: bool = True
    min_rounds: int = 15  # don't check before this
    action_rate_stability_threshold: float = 0.1  # coefficient of variation
    topic_entropy_threshold: float = 0.3
    check_window: int = 5  # rolling window size

@dataclass
class DynamicsSpec:
    """Layer 3: Runtime rules and mechanics"""
    action_weights: ActionWeights = field(default_factory=ActionWeights)
    # Time config
    total_simulation_hours: int = 30
    minutes_per_round: int = 60
    start_hour: int = 8  # skip dead hours, start at first active hour
    # Activity multipliers
    peak_hours: List[int] = field(default_factory=lambda: [19, 20, 21, 22])
    peak_multiplier: float = 1.5
    off_peak_hours: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    off_peak_multiplier: float = 0.15  # raised from 0.05 to prevent dead rounds
    # Feed context limits
    feed_recent_posts: int = 10
    feed_popular_posts: int = 5
    max_persona_chars: int = 200  # compress at action time
    # Influence
    max_system_agent_influence: float = 1.0  # cap non-character entities
    # Convergence
    convergence: ConvergenceConfig = field(default_factory=ConvergenceConfig)
    # Self-interaction prevention
    prevent_self_quote: bool = True

@dataclass
class LayeredSimSpec:
    """Complete layered simulation specification"""
    name: str
    version: str = "1.0"
    description: str = ""
    world: WorldModel = field(default_factory=WorldModel)
    population: PopulationSpec = field(default_factory=PopulationSpec)
    dynamics: DynamicsSpec = field(default_factory=DynamicsSpec)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml(cls, path: str) -> 'LayeredSimSpec':
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayeredSimSpec':
        """Recursively construct from dict"""
        world_data = data.get('world', {})
        world = WorldModel(
            domain=world_data.get('domain', ''),
            description=world_data.get('description', ''),
            language=world_data.get('language', 'en'),
            resources=world_data.get('resources', []),
            channels=world_data.get('channels', ['twitter']),
            forces=[Force(**f) for f in world_data.get('forces', [])],
            events=[WorldEvent(**e) for e in world_data.get('events', [])],
            phases=[PhaseTransition(**p) for p in world_data.get('phases', [])],
            hot_topics=world_data.get('hot_topics', []),
            narrative_direction=world_data.get('narrative_direction', ''),
        )

        pop_data = data.get('population', {})
        population = PopulationSpec(
            mode=pop_data.get('mode', 'template'),
            total_agents=pop_data.get('total_agents', 30),
            archetypes=[ArchetypeSpec(
                name=a['name'],
                count=a.get('count', 1),
                description=a.get('description', ''),
                system_prompt_template=a.get('system_prompt_template', ''),
                influence_range=tuple(a.get('influence_range', [1.0, 1.5])),
                activity_level_range=tuple(a.get('activity_level_range', [0.4, 0.7])),
                sentiment_bias_range=tuple(a.get('sentiment_bias_range', [-0.3, 0.3])),
                temperature=a.get('temperature', 0.7),
                posts_per_hour_range=tuple(a.get('posts_per_hour_range', [0.5, 2.0])),
                comments_per_hour_range=tuple(a.get('comments_per_hour_range', [1.0, 3.0])),
                active_hours=a.get('active_hours', list(range(8, 23))),
            ) for a in pop_data.get('archetypes', [])],
            named_agents=[NamedAgent(**na) for na in pop_data.get('named_agents', [])],
            variance=pop_data.get('variance', {"activity_level": 0.2, "sentiment_bias": 0.3, "influence_weight": 0.2}),
        )

        dyn_data = data.get('dynamics', {})
        aw_data = dyn_data.get('action_weights', {})
        conv_data = dyn_data.get('convergence', {})
        dynamics = DynamicsSpec(
            action_weights=ActionWeights(**aw_data) if aw_data else ActionWeights(),
            total_simulation_hours=dyn_data.get('total_simulation_hours', 30),
            minutes_per_round=dyn_data.get('minutes_per_round', 60),
            start_hour=dyn_data.get('start_hour', 8),
            peak_hours=dyn_data.get('peak_hours', [19, 20, 21, 22]),
            peak_multiplier=dyn_data.get('peak_multiplier', 1.5),
            off_peak_hours=dyn_data.get('off_peak_hours', [0, 1, 2, 3, 4, 5]),
            off_peak_multiplier=dyn_data.get('off_peak_multiplier', 0.15),
            feed_recent_posts=dyn_data.get('feed_recent_posts', 10),
            feed_popular_posts=dyn_data.get('feed_popular_posts', 5),
            max_persona_chars=dyn_data.get('max_persona_chars', 200),
            max_system_agent_influence=dyn_data.get('max_system_agent_influence', 1.0),
            convergence=ConvergenceConfig(**conv_data) if conv_data else ConvergenceConfig(),
            prevent_self_quote=dyn_data.get('prevent_self_quote', True),
        )

        return cls(
            name=data.get('name', ''),
            version=data.get('version', '1.0'),
            description=data.get('description', ''),
            world=world,
            population=population,
            dynamics=dynamics,
        )

def validate_spec(spec: LayeredSimSpec) -> List[str]:
    """Validate a spec and return list of errors (empty = valid)"""
    errors = []
    if not spec.name:
        errors.append("spec.name is required")
    if not spec.world.domain:
        errors.append("world.domain is required")

    # Check action weights sum to ~1.0
    aw = spec.dynamics.action_weights
    total = aw.like_post + aw.comment + aw.create_post + aw.quote_post + aw.repost + aw.follow + aw.do_nothing
    if abs(total - 1.0) > 0.01:
        errors.append(f"action_weights must sum to 1.0 (got {total:.3f})")

    # Check population
    if spec.population.mode == "template":
        if not spec.population.archetypes:
            errors.append("template mode requires at least one archetype")
        total_from_archetypes = sum(a.count for a in spec.population.archetypes)
        if total_from_archetypes != spec.population.total_agents:
            errors.append(f"archetype counts ({total_from_archetypes}) != total_agents ({spec.population.total_agents})")
    elif spec.population.mode == "named":
        if not spec.population.named_agents:
            errors.append("named mode requires at least one named_agent")

    # Check phases are within round range
    total_rounds = (spec.dynamics.total_simulation_hours * 60) // spec.dynamics.minutes_per_round
    for phase in spec.world.phases:
        if phase.round > total_rounds:
            errors.append(f"phase '{phase.name}' at round {phase.round} exceeds total rounds ({total_rounds})")

    return errors
