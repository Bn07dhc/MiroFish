# Probability Distributions for Agent-Based Simulation

## Key Distributions and When to Use Them

### Power Law (Pareto Distribution)
Social influence, content virality, and wealth follow power laws — a few agents dominate while most have minimal impact.

**In simulation:**
- influence_weight should follow Pareto with α ≈ 1.5-2.0
- Content engagement (likes, shares) follows power law: most posts get <5 interactions, a few get 100+
- Agent follower counts: 80/20 rule — 20% of agents generate 80% of engagement

**Calibration:**
- For 30 agents: top 3 should have influence 2.5-3.0x, middle 10 at 1.0-1.5x, bottom 17 at 0.5-1.0x
- Don't use uniform distribution for influence — it produces unrealistically flat dynamics
- Python: `numpy.random.pareto(a=1.5, size=N) + 0.5` then clip to [0.5, 3.0]

### Normal (Gaussian) Distribution
Sentiment bias, activity timing, and response delays are well-modeled by normal distributions.

**In simulation:**
- sentiment_bias: Normal(μ=0, σ=0.3) for neutral topics, Normal(μ=±0.2, σ=0.4) for polarized
- response_delay: LogNormal(μ=3, σ=1) minutes — most respond quickly, some take hours
- active_hours: center around archetype peak ± Normal(0, 1.5) hours

**Calibration:**
- 68% of agents within ±1σ of archetype mean
- 95% within ±2σ — agents outside this are outliers that add realism
- Use truncated normal to enforce bounds (e.g., activity_level clipped to [0.1, 1.0])

### Poisson Distribution
Event arrival — how many posts/comments per time unit.

**In simulation:**
- posts_per_hour: Poisson(λ) where λ = archetype's posts_per_hour setting
- For broker (λ=1.5): P(0)=22%, P(1)=33%, P(2)=25%, P(3)=13% — natural variation
- For amplifier (λ=3.0): P(0)=5%, P(1)=15%, P(2)=22%, P(3)=22% — consistently active
- For consumer (λ=0.3): P(0)=74%, P(1)=22%, P(2)=3% — mostly silent

**Key insight:** Don't use fixed posts_per_hour. Use it as λ for Poisson sampling each round. This produces realistic bursty behavior — agents don't post exactly 2 times per hour every hour.

### Exponential Distribution
Inter-event timing — time between consecutive actions by the same agent.

**In simulation:**
- Time between posts: Exponential(1/λ) where λ = posts_per_hour
- Produces realistic clustering: sometimes rapid-fire posts, sometimes long silence
- response_delay_min/max should define the bounds of an exponential with mean = (min+max)/3

### Beta Distribution
Bounded quantities like activity_level, echo_chamber_strength, sentiment_bias.

**In simulation:**
- activity_level: Beta(α=2, β=5) — right-skewed, most agents are moderately inactive
- echo_chamber_strength: Beta(α=2, β=2) — symmetric, centered around 0.5
- For within-archetype variance: Beta(α=5, β=5) centered on archetype mean, scaled to range

**Why Beta:** It's naturally bounded [0,1] and shape-flexible. α>β = right-skewed (more high values), α<β = left-skewed (more low values), α=β = symmetric.

### Zipf Distribution
Topic popularity and content diversity.

**In simulation:**
- hot_topics follow Zipf: topic 1 gets ~50% attention, topic 2 gets ~25%, topic 3 gets ~12%
- Agent vocabulary/interest diversity: most agents focus on 1-2 topics
- Hashtag usage: follows Zipf with exponent ≈ 1.0-1.5

## Stochastic Process Models

### Markov Chains for Agent State
Agents transition between behavioral states:
- Active → Lurking (probability 0.3 per round for consumers)
- Lurking → Active (probability 0.1 per round, higher if trending topic)
- Neutral → Supportive (probability proportional to positive exposure)
- Neutral → Opposing (probability proportional to negative exposure)

State transition matrices are a powerful way to model agent behavior evolution without explicit LLM reasoning.

### Random Walk for Sentiment
Agent sentiment evolves as a bounded random walk:
- Each round: sentiment += Normal(0, step_size)
- step_size = 0.05 for stable agents, 0.15 for volatile agents
- Bounded to [-1, 1] with reflecting barriers
- External events shift the mean: positive news → sentiment += 0.2 for all agents

### Branching Process for Viral Spread
Content virality follows a Galton-Watson branching process:
- Each share generates Poisson(R) new shares
- R < 1: content dies out (most content)
- R = 1: critical threshold
- R > 1: viral spread (rare but dominant when it happens)
- For simulation: set viral_threshold based on R estimation from early engagement

## Statistical Validity in Simulation Output

### Minimum Sample Sizes
- Per-agent action distribution: need ≥10 actions per agent for meaningful analysis
- Per-phase analysis: need ≥30 actions per phase
- Sentiment convergence: need ≥5 rounds at steady state
- Cross-simulation comparison: need ≥3 replicate runs with different seeds

### Confidence Intervals
When reporting simulation results:
- Mean ± 1.96 × SE for 95% CI (SE = σ/√n)
- For proportions (action type ratios): Wilson interval, not Wald
- For small samples (<30): use t-distribution, not z

### Variance Decomposition
In multi-agent sims, total variance = between-archetype variance + within-archetype variance:
- High between/within ratio → archetypes are well-differentiated
- Low ratio → archetypes are too similar (need more differentiation)
- Target: between-archetype variance should be ≥60% of total variance
