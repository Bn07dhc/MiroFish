# Bayesian Reasoning for Simulation Agents

## Bayesian Agents — Theory

In an ideal simulation, agents update beliefs according to Bayes' theorem:
P(hypothesis | evidence) ∝ P(evidence | hypothesis) × P(hypothesis)

This maps directly to simulation dynamics:
- **Prior**: agent's initial sentiment_bias and stance
- **Likelihood**: strength of new evidence (post content, engagement signals)
- **Posterior**: updated sentiment/stance after processing new information

## Belief Update Models

### Simple Bayesian Update
For binary opinions (support/oppose):
- Prior odds: sentiment_bias → odds ratio
- Likelihood ratio: strength of observed evidence
- Posterior odds = prior odds × likelihood ratio

**Example:**
- Agent starts at sentiment_bias = 0.2 (mild support, prior odds = 1.5:1)
- Sees strong opposing evidence (likelihood ratio = 0.3)
- Posterior odds = 1.5 × 0.3 = 0.45:1 → new sentiment_bias ≈ -0.35

**Calibration:**
- Broker evidence: likelihood ratio 0.2-0.5 (strong)
- Amplifier evidence: likelihood ratio 0.4-0.7 (moderate, less trusted)
- Consumer evidence: likelihood ratio 0.7-0.9 (weak, easily dismissed)
- Skeptic counter-evidence: likelihood ratio 0.3-0.6 (moderately strong)

### Continuous Bayesian Update (Kalman Filter)
For continuous opinion values, use a Kalman filter analogy:
- State: agent's true opinion (hidden)
- Observation: content in feed + engagement signals
- Process noise: random opinion drift (σ_process)
- Observation noise: uncertainty in interpreting content (σ_observation)

Update equations:
1. Predict: opinion_predicted = opinion_current + drift
2. Update: opinion_new = opinion_predicted + K × (observed_signal - opinion_predicted)
3. K (Kalman gain) = trust_in_evidence / (trust_in_evidence + trust_in_prior)

**Calibration:**
- High K (0.7-0.9): agent is easily persuaded (consumers, amplifiers)
- Low K (0.1-0.3): agent is stubborn (brokers, regulators)
- Medium K (0.3-0.6): agent weighs evidence against prior (skeptics, conduits)

### Bounded Rationality
Real agents don't perfectly Bayesian-update. They:
1. **Satisfice**: update only when evidence exceeds a threshold (not every post)
2. **Anchor**: update less than Bayes prescribes (anchoring bias)
3. **Overweight vivid evidence**: one dramatic post > ten moderate posts
4. **Forget**: prior belief drifts back toward baseline (mean-reversion)

**Implementation:** Apply a "rationality coefficient" r ∈ [0, 1]:
- Actual update = r × Bayesian update + (1-r) × 0
- r = 0.3 for consumers (mostly ignores evidence)
- r = 0.7 for skeptics (mostly rational)
- r = 0.5 for most agents

## Information Aggregation

### Wisdom of Crowds Conditions (Surowiecki)
Collective intelligence emerges when:
1. **Diversity**: agents have different information/perspectives
2. **Independence**: agents form opinions independently (not herding)
3. **Decentralization**: no single agent controls the narrative
4. **Aggregation**: mechanism exists to combine individual judgments

**Simulation diagnostic:** If your sim produces collective wisdom:
- Check: archetypes have different sentiment ranges (diversity ✓)
- Check: echo_chamber_strength < 0.6 (independence ✓)
- Check: max influence_weight < 3x mean (decentralization ✓)
- Check: conduit agents connect clusters (aggregation ✓)

If any condition is violated, expect pathological outcomes (herding, polarization, single-agent dominance).

### Condorcet Jury Theorem
If each agent is >50% likely to be correct, majority vote accuracy increases with group size. But if agents are <50% accurate (following a wrong cascade), larger groups are *worse*.

**Simulation implication:**
- Quality of initial information (broker accuracy) determines whether crowd aggregation helps or hurts
- A single high-quality skeptic can break a bad cascade and save collective accuracy
- This is why skeptic agents are essential even in "consensus" sims

## Bayesian Games (Incomplete Information)

### Type Uncertainty
Agents don't know each other's true type (sentiment, influence):
- They observe actions and infer types
- High-activity agent might be high-influence broker OR low-influence amplifier
- This uncertainty drives strategic behavior

### Signaling Equilibria
- **Separating equilibrium**: different types take different actions (identifiable)
  - Brokers post long analysis, Amplifiers post short reactions → types visible
- **Pooling equilibrium**: all types take the same action (unidentifiable)
  - Everyone posts similar content → can't distinguish broker from amplifier
- **Simulation goal**: usually separating equilibrium (more interesting dynamics)

### Mechanism Design Implication
To achieve separating equilibrium:
- Give archetypes different system_prompt_templates (different "voices")
- Set different temperature per archetype (different style variation)
- Differentiate active_hours (different timing patterns)
- All three create natural type separation without explicit type labels

## Practical Calibration

### Evidence Strength by Source
| Source | Likelihood Ratio | Belief Update Size |
|--------|-----------------|-------------------|
| High-influence broker | 0.2-0.4 (strong) | Large |
| Medium-influence expert | 0.3-0.5 | Moderate-large |
| Amplifier repost | 0.6-0.8 (weak signal) | Small |
| Consumer like | 0.8-0.95 (very weak) | Minimal |
| Platform trending | 0.4-0.6 (moderate, social proof) | Moderate |
| External event injection | 0.1-0.3 (very strong) | Very large |

### Update Frequency
- Not every round: agents process information in batches
- Update every 2-3 rounds for most agents
- Update every round for amplifiers (highly reactive)
- Update every 4-5 rounds for regulators (slow processing)
- This reduces computational cost and produces more realistic behavior
