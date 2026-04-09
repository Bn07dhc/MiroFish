# Agent Archetype Design Principles

## Core Archetype Categories

### Information Producers
Agents who generate original content. In real social networks, this is 1-10% of users.
- **Broker/Gatekeeper:** Controls information flow. High credibility, strategic timing. Low temperature (0.3-0.5) for measured output.
- **Creator/Journalist:** Generates original analysis. Medium-high activity. Medium temperature (0.5-0.7).
- **Whistleblower/Leaker:** Rare but high-impact. Very low activity_level but very high influence_weight.

### Information Amplifiers
Agents who spread content. 9-15% of real users.
- **Amplifier/Evangelist:** High activity, high enthusiasm, low critical thinking. High temperature (0.8-1.0).
- **Bot/Automated:** Very high activity, low variance in behavior. Very high temperature for variety or very low for repetition.

### Information Filters
Agents who evaluate and critique. 5-10% of real users.
- **Skeptic/Critic:** Analytical, evidence-driven. Medium activity, negative sentiment bias. Low temperature (0.4-0.6).
- **Fact-Checker:** Responds specifically to claims. Low posts_per_hour, high comments_per_hour.

### Information Consumers
Passive agents. 70-85% of real users.
- **Lurker:** Very low activity (0.1-0.2), mostly likes. Low influence.
- **Casual Consumer:** Moderate activity (0.2-0.4), occasional comments. Medium influence.
- **Reactive Consumer:** Low creation, high reaction. Influenced by network effects.

### Information Bridges
Critical for preventing echo chambers. 3-8% of agents.
- **Conduit:** Connects different groups. Wide active_hours, high comments, neutral stance.
- **Translator:** Reframes information for different audiences. Medium creation, high quoting.

## Archetype Differentiation Rules

### Within-Archetype Variance
Even agents of the same archetype should differ. Rules:
1. Activity level: ±20% variance from archetype baseline
2. Sentiment bias: ±0.3 variance from archetype baseline
3. Influence weight: ±20% variance from archetype baseline
4. Active hours: stagger by ±1 hour across agents of same type
5. Temperature: ±0.1 from archetype baseline

### Cross-Archetype Interaction Patterns
- Brokers post → Amplifiers spread → Skeptics challenge → Consumers react
- Conduits bridge between clusters
- Regulatory agents interject at low frequency but high impact
- Consumers' collective like/comment behavior drives algorithmic amplification

## Temperature-Role Mapping
Temperature controls creativity and unpredictability in LLM output:
- 0.3-0.4: Formal, measured (executives, regulators, brokers)
- 0.5-0.6: Analytical, balanced (skeptics, conduits, analysts)
- 0.7-0.8: Expressive, varied (consumers, operational staff)
- 0.9-1.0: Creative, unpredictable (amplifiers, activists)
