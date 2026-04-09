# Game Theory for Multi-Agent Simulation

## Foundational Games in Social Simulation

### Prisoner's Dilemma (Cooperation vs Defection)
Two agents choose independently to cooperate or defect:
- Mutual cooperation: both get moderate reward (3, 3)
- Mutual defection: both get low reward (1, 1)
- One cooperates, one defects: defector gets high (5), cooperator gets nothing (0)

**In simulation:** Models information sharing dynamics
- Brokers face PD every round: share exclusive info (cooperate) or hoard it (defect)
- Iterated PD with reputation → cooperation emerges among repeated interactors
- One-shot interactions (new agents, anonymous platforms) → more defection

### Stag Hunt (Coordination Game)
Two agents choose independently: hunt stag (risky, high reward if both cooperate) or hunt hare (safe, low reward):
- Both stag: (4, 4)
- Both hare: (2, 2)
- Mixed: stag hunter gets (0), hare hunter gets (2)

**In simulation:** Models collective action and consensus
- Board alignment in corporate sims: all align = deal succeeds, any defects = deal weakens
- Consensus formation: supporting a narrative = stag (high value if others join), staying neutral = hare
- Risk aversion drives agents toward safe (hare) unless trust is established

### Chicken Game (Anti-Coordination)
Two agents drive toward each other:
- Both swerve: (2, 2) — mild embarrassment
- One swerves: swerver gets (1), straight gets (3)
- Neither swerves: (-10, -10) — disaster

**In simulation:** Models escalation dynamics
- Competitors in deal sims: both bid aggressively = value destruction
- Public arguments between skeptics and amplifiers: neither backs down = credibility damage
- Key dynamic: who has higher influence_weight is more likely to play "straight"

## Nash Equilibrium in Multi-Agent Sims

### Mixed Strategy Equilibria
When agents randomize between actions:
- Agent doesn't always post, doesn't always lurk — mixed strategy
- Equilibrium: each agent's mixed strategy makes others indifferent
- action_weights in sim config approximate a mixed strategy equilibrium

### Computing Equilibrium Action Ratios
For a simplified 3-action game (post, react, do_nothing):
- If posting has expected payoff π_p = influence × audience
- Reacting has payoff π_r = smaller but guaranteed
- Doing nothing has payoff 0
- In equilibrium: agents post when π_p > threshold, react when π_r > threshold
- This produces natural power-law distribution of posting frequency

### Correlated Equilibrium
A traffic signal (shared information) helps agents coordinate:
- In sim: phase transitions act as coordination signals
- "Due diligence phase" → agents know to shift from speculation to analysis
- Phase injections create correlated equilibrium by giving all agents common knowledge

## Mechanism Design for Simulation Rules

### Incentive Compatibility
The sim rules should make truthful/natural behavior optimal:
- If action_weights force likes but agents can't "see" the like action, the mechanism fails
- agents should find it "natural" to follow the configured action distribution
- Temperature calibration helps: lower temp = more predictable, follows incentive structure

### Revelation Principle
Any outcome achievable by a complex mechanism is achievable by a direct mechanism:
- Don't design complex multi-step agent decision trees
- Instead: let agents directly choose from available actions
- The sim environment (action_weights, influence, feed) shapes the "mechanism"

### Auction Theory for Attention Markets
Content competes for finite attention (like bidding in an auction):
- Each post has a "quality" score (influence × content relevance)
- Feed algorithm runs a second-price auction: top-k posts shown
- Agents bid with their influence_weight × post quality
- Winner's curse: high-influence agents may over-invest in content

## Evolutionary Game Theory

### Replicator Dynamics
Agent strategies evolve over time based on payoff:
- Successful strategies (high engagement) → more agents adopt that style
- Failing strategies (low engagement) → agents switch away
- In sim: agents learn from successful peers in their feed

### Evolutionary Stable Strategy (ESS)
A strategy mix that can't be invaded by a mutant:
- In attention economy: certain ratio of brokers:amplifiers:skeptics is stable
- If too many amplifiers → signal-to-noise drops → skeptics gain advantage
- If too many skeptics → discourse becomes negative → amplifiers gain advantage
- Equilibrium archetype ratio is an ESS

### Hawk-Dove for Influence Competition
Hawks (aggressive, high-activity) vs Doves (passive, low-activity):
- Hawk vs Hawk: both pay cost of conflict (mutual aggression = audience fatigue)
- Hawk vs Dove: Hawk wins attention
- Dove vs Dove: split attention equally
- ESS: mixed population with ~40% Hawks, ~60% Doves (depends on cost of conflict)

**Simulation implication:** Natural archetype ratio emerges:
- ~15-20% high-activity agents (hawks/brokers/amplifiers)
- ~80-85% low-to-medium activity agents (doves/consumers)
- This aligns with the 90-9-1 rule and power law engagement distributions

## Information Economics

### Signaling (Spence)
Agents use costly actions to signal credibility:
- Long, detailed posts signal expertise (costly to produce)
- Quick likes/retweets signal attention but not analysis
- In sim: posts_per_hour inversely correlates with average post quality for brokers

### Adverse Selection
When agent quality is hidden:
- Anonymous agents → market for lemons problem
- High-quality analysis gets drowned by low-quality noise
- Platform reputation (influence_weight evolution) helps mitigate

### Moral Hazard
When agent actions are unobservable:
- Agents may free-ride on others' information production
- Consumer agents benefit from broker analysis without reciprocating
- In sim: this is the natural consumer archetype behavior — not a bug but a feature

## Application to Simulation Design

### For Corporate Deal Sims
- Executive-Board interaction: Stag Hunt (alignment game)
- Competitor dynamics: Chicken (escalation game)
- Information sharing: Iterated PD with reputation
- Phase transitions: correlated equilibrium signals

### For Attention Market Sims
- Content competition: attention auction
- Strategy evolution: replicator dynamics on archetype mix
- Information quality: signaling equilibrium
- Viral dynamics: branching process with evolutionary selection

### For Geopolitical Sims
- Alliance formation: repeated Stag Hunt
- Escalation: Chicken with nuclear option
- Trade: iterated PD with tariff strategies
- Information warfare: asymmetric signaling games
