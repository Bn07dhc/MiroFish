# Stochastic Processes for Social Simulation

## Markov Chains in Agent Behavior

### Agent State Machine
Model each agent as a finite-state Markov chain with states:
- **Active**: posting, commenting, sharing
- **Lurking**: reading but not engaging
- **Reactive**: only responds to direct mentions or trending topics
- **Dormant**: temporarily inactive (simulates real user dropout)

### Transition Matrix (per round)
```
            Active  Lurking  Reactive  Dormant
Active      0.60    0.25     0.10      0.05
Lurking     0.15    0.65     0.15      0.05
Reactive    0.20    0.20     0.50      0.10
Dormant     0.05    0.10     0.05      0.80
```

**Calibration by archetype:**
- Brokers: higher Active→Active (0.75), lower Dormant transition
- Consumers: higher Lurking→Lurking (0.80), lower Active retention
- Amplifiers: high Active→Active (0.70), high Reactive→Active (0.40)
- Skeptics: moderate all transitions, higher Reactive→Active on trigger events

### Stationary Distribution
The long-run behavior of agents converges to a stationary distribution:
- For the matrix above: Active=25%, Lurking=35%, Reactive=18%, Dormant=22%
- This matches the 90-9-1 rule roughly: ~25% active, ~53% semi-active, ~22% inactive

### Event-Triggered Transitions
External events modify transition probabilities temporarily:
- Breaking news: all agents get +0.20 to Active transition probability for 3 rounds
- Controversy: Reactive→Active increases by +0.30 for skeptics
- Viral content: Lurking→Active increases by +0.15 for all agents

## Birth-Death Processes for Topic Lifecycle

### Topic Popularity Model
Each hot_topic follows a birth-death process:
- Birth rate λ(t): new mentions per round (driven by agent creation + amplification)
- Death rate μ(t): topic decay per round (attention shifts)
- Net growth: λ(t) - μ(t)

### Typical Topic Lifecycle
1. **Seeding** (rounds 1-3): λ >> μ, topic grows from 0 to initial threshold
2. **Viral growth** (rounds 3-8): λ/μ > 1, exponential growth phase
3. **Peak** (rounds 8-12): λ ≈ μ, maximum attention
4. **Decay** (rounds 12-20): λ < μ, attention shifts to new topics
5. **Long tail** (rounds 20+): low but persistent mentions

### Competing Topics
When multiple topics compete for finite attention:
- Total attention budget per round is fixed (proportional to active agents)
- Topics compete via Lotka-Volterra dynamics
- Dominant topic can suppress emerging topics (attention monopoly)
- Disruption: new high-salience topic can break existing monopoly

## Poisson Processes for Event Modeling

### Homogeneous Poisson Process
Events arrive at constant rate:
- Agent posting: Poisson(λ=posts_per_hour)
- Platform events (trending, algorithm change): Poisson(λ=0.05 per round)
- External shocks (news, market events): Poisson(λ=0.03 per round)

### Non-Homogeneous Poisson Process
Rate varies with time — more realistic:
- λ(t) = λ_base × time_multiplier(hour_of_day)
- Peak hours: λ(t) = λ_base × 1.5
- Off-peak: λ(t) = λ_base × 0.15
- This naturally produces the activity patterns observed in real platforms

### Compound Poisson Process
Each event has a random magnitude:
- Post impact: Poisson arrivals × LogNormal(magnitude)
- Most posts have small impact (LogNormal μ=0, σ=1)
- Viral posts are rare but have magnitude 10-100x the median

## Brownian Motion for Opinion Evolution

### Standard Brownian Motion
Agent opinion evolves as: O(t+1) = O(t) + σ√Δt × Z, where Z ~ Normal(0,1)

**Parameters:**
- σ = 0.05 for stable agents (executives, regulators)
- σ = 0.15 for volatile agents (amplifiers, consumers)
- Δt = 1 round

### Drift-Diffusion Model
Add directional pressure: O(t+1) = O(t) + μΔt + σ√Δt × Z

**μ (drift) sources:**
- Narrative direction: shifts all agents toward narrative stance
- Peer pressure: shifts toward mean opinion of interacted agents
- Phase events: temporary μ spike during phase transitions
- External evidence: permanent μ shift when new facts emerge

### Mean-Reverting Process (Ornstein-Uhlenbeck)
Opinions tend to revert to a baseline: dO = θ(μ - O)dt + σdW

**Why this is better than pure Brownian motion:**
- Prevents opinions from drifting to extremes without bound
- θ controls reversion speed (0.1 = slow, 0.5 = fast)
- μ = baseline opinion (can change with phases)
- Produces realistic oscillation around a shifting center

## Queuing Theory for Information Flow

### M/M/1 Queue: Agent Attention
Each agent has finite attention capacity:
- Arrival rate λ: incoming content (posts in feed)
- Service rate μ: rate at which agent processes/engages with content
- If λ > μ: information overload → agent ignores most content
- If λ < μ: agent has spare attention → more likely to engage with each item

### Little's Law
L = λW (average items in queue = arrival rate × average wait time)
- For a sim with 30 agents, 10 active per round, 3 posts per active agent: λ = 30 posts/round
- Average time before a post gets engagement (W): depends on feed algorithm
- L = posts "waiting" in feed without engagement at any given time

**Practical implication:** If feed_recent_posts=10, agents see the most recent 10 posts. With 30 posts per round, 67% of posts are never seen. This creates natural information loss and explains why high-influence agents dominate — their posts stay in the "recent" window longer.

## Renewal Theory for Agent Activity Cycles

### Inter-Activity Times
Time between consecutive actions by the same agent:
- Not exponential (memoryless) — agents have memory and rhythms
- Better modeled as Weibull(k, λ):
  - k < 1: decreasing hazard (the longer since last action, the less likely to act)
  - k = 1: exponential (memoryless, Poisson)
  - k > 1: increasing hazard (the longer since last action, the more likely to act)
- For social media: k ≈ 0.7-0.9 (slightly bursty — actions cluster then quiet)

### Renewal Reward
Total agent contribution = number of renewal cycles × average reward per cycle:
- Cycle: active period → dormant period → active period
- Reward: actions produced during active period
- Long-run average: total actions / total time = λ_effective
- This explains why activity_level alone doesn't determine total contribution — burst patterns matter
