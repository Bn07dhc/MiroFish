# Cognitive Biases and Behavioral Economics in Simulation

## Biases That Shape Agent Behavior

### Confirmation Bias
Agents seek and weight information that confirms existing beliefs.

**Implementation in simulation:**
- Agent with sentiment_bias > 0.2: weights positive content 2x in decision-making
- Feed algorithm should surface "confirming" content more often for biased agents
- echo_chamber_strength parameter directly controls this: 0.5 = moderate, 0.8 = strong
- Result: opinion clusters form faster, are more stable, and harder to break

### Anchoring Effect
First piece of information disproportionately influences subsequent judgments.

**Implementation in simulation:**
- Initial posts (round 0-2) set the "anchor" for subsequent discourse
- Agents who see early broker posts are anchored to that framing
- Phase 1 dynamics are critical — first mover advantage is real
- Recommendation: make initial_posts carefully crafted, not random

### Bandwagon Effect (Herding)
Agents follow the majority, especially under uncertainty.

**Implementation in simulation:**
- When >60% of visible posts support a position, neutral agents shift toward it
- Amplifiers are most susceptible (high temperature, positive sentiment bias)
- Skeptics resist herding (low temperature, negative sentiment bias)
- Consumers follow majority with probability proportional to majority size

### Loss Aversion (Kahneman & Tversky)
Losses hurt ~2x more than equivalent gains feel good.

**Implementation in simulation:**
- Negative events (competitor bid, regulatory block) generate 2x the response volume of positive events
- Agents with stakes in status quo react more strongly to threats than opportunities
- In corporate sims: opposition to change is naturally stronger than support for change
- Calibration: negative event prompt_injection should expect 2x action rate

### Availability Heuristic
Recent and vivid information is overweighted in decision-making.

**Implementation in simulation:**
- feed_recent_posts parameter directly controls this
- Lower values (5-8) = stronger availability bias (only very recent posts influence decisions)
- Higher values (15-20) = weaker availability bias (broader context)
- Recommendation: 10 recent posts balances recency bias with sufficient context

### Dunning-Kruger Effect
Low-competence agents overestimate their expertise; high-competence underestimate.

**Implementation in simulation:**
- Consumer agents (low expertise) should have higher posts_per_hour than their expertise warrants
- Expert agents (brokers) should post less frequently but with higher quality
- Temperature mapping: low-expertise + high-confidence = high temperature (lots of low-quality output)

## Prospect Theory in Agent Decision-Making

### Reference Point Dependence
Agents evaluate outcomes relative to a reference point, not absolute value.

**In simulation:**
- Agent's reference point = their initial sentiment_bias
- Movements toward reference feel like "returning to normal"
- Movements away feel like gains or losses
- This explains why agents resist opinion change — any shift from reference feels like a loss

### Probability Weighting
People overweight small probabilities and underweight large ones.

**In simulation:**
- Rare events (probability_per_round = 0.05) get disproportionate attention when triggered
- Common events (probability_per_round = 0.30) get taken for granted
- Recommendation: low-probability events should have high-impact prompt_injection
- High-probability events should have moderate prompt_injection

### Framing Effects
Same information framed differently leads to different decisions.

**In simulation:**
- Two brokers reporting the same event with different framing → different audience reactions
- Positive frame ("70% success rate") vs negative frame ("30% failure rate")
- system_prompt_template should specify framing tendency per archetype
- Brokers: neutral framing; Amplifiers: positive framing; Skeptics: negative framing

## Social Psychology in Multi-Agent Systems

### Social Proof (Cialdini)
People follow others' behavior when uncertain.

**In simulation:**
- Agents check "what are others doing?" before choosing their action
- Posts with high engagement (likes, quotes) attract more engagement
- viral_threshold parameter: once a post gets N interactions, it enters viral feedback loop
- Low threshold (5): easy viral spread; High threshold (20): only exceptional content goes viral

### Authority Bias
Higher-status agents have disproportionate influence.

**In simulation:**
- influence_weight directly models authority
- Posts from high-influence agents should be seen by more agents (weighted feed)
- In corporate sims: CEO post > analyst post, regardless of content quality
- Risk: if influence_weight is too high, one agent dominates entire sim

### In-Group/Out-Group Bias
Agents trust and engage more with similar agents.

**In simulation:**
- Agents of same archetype naturally interact more (shared active_hours, similar topics)
- echo_chamber_strength controls cross-group interaction probability
- Conduit archetype explicitly designed to bridge in-group/out-group divide
- Without conduits: sim fragments into disconnected clusters

### Spiral of Silence (Noelle-Neumann)
Minority opinion holders self-censor when they perceive their view is unpopular.

**In simulation:**
- Agents with minority sentiment_bias reduce posts_per_hour as majority opinion dominates
- Skeptics resist this effect (lower temperature = less susceptible to social pressure)
- This creates a feedback loop: majority appears even larger → more self-censorship
- Counter: conduit agents and phase transitions can break the spiral

## Behavioral Calibration Guide

### By Archetype
| Archetype | Primary Bias | Secondary Bias | Temperature |
|-----------|-------------|----------------|-------------|
| Broker | Anchoring (sets frame) | Authority (high influence) | 0.3-0.5 |
| Amplifier | Bandwagon, Social proof | Availability (reacts to recent) | 0.8-1.0 |
| Skeptic | Contrarian (anti-bandwagon) | Loss aversion (risk-focused) | 0.4-0.6 |
| Consumer | Confirmation, Herding | Spiral of silence | 0.6-0.8 |
| Conduit | Low bias (neutral) | In-group bridge | 0.5-0.7 |
| Regulatory | Authority, Anchoring | Loss aversion (conservative) | 0.2-0.4 |

### Event Response Calibration
| Event Type | Positive Response Multiplier | Negative Response Multiplier |
|------------|-------|---------|
| Breaking news | 1.5x activity | 2.0x activity |
| Phase transition | 1.3x activity | 1.3x activity |
| Competitor move | 1.0x activity | 1.8x activity |
| Regulatory action | 0.8x activity | 2.5x activity |
| Viral content | 2.0x activity | 2.0x activity |
