# Agent Count and Archetype Ratio Calibration

## Optimal Agent Counts by Simulation Type

### Small-Scale (10-20 agents)
Best for: focused organizational dynamics, small team simulations
- Minimum viable: 10 agents for meaningful interaction patterns
- Sweet spot: 15 agents for org/deal sims
- Each agent should be individually characterized (named mode)
- Risk: too few agents = artificial convergence, echo chamber effects dominate

### Medium-Scale (20-40 agents)
Best for: market dynamics, community simulations, attention economy
- Sweet spot: 25-30 agents for general social sims
- Template mode with 4-6 archetypes works well
- Sufficient diversity for emergent behavior without excessive compute

### Large-Scale (40-100 agents)
Best for: population-level opinion dynamics, viral spreading, network effects
- Requires careful archetype ratio management
- Consumer/passive agents should be 40-50% of total
- Active content creators should be 15-25% of total
- Compute scales linearly with agent count (1 LLM call per active agent per round)

## Archetype Ratio Guidelines

### Attention Economy / Information Market
- Information Brokers: 10-15% (3-4 agents in a 30-agent sim)
- Amplifiers: 15-20% (5-6 agents)
- Skeptics/Critics: 12-18% (4-5 agents)
- Consumers/Passive: 35-45% (10-13 agents)
- Conduits/Bridges: 5-8% (2 agents)

### Corporate/Organizational
- Executives: 15-20% (4-5 agents)
- Board/Governance: 10-15% (3-4 agents)
- Competitors: 8-12% (2-3 agents)
- Market/External: 12-18% (3-5 agents)
- Operational: 15-20% (4-5 agents)
- Regulatory: 5-10% (1-2 agents)
- Conduits: 8-12% (2-3 agents)

### Key Principle: Passive Majority
Real social media follows a 90-9-1 rule: 90% lurk, 9% occasionally participate, 1% create most content. Simulations should reflect this asymmetry. Even in "active" simulations, consumer/passive agents should represent at least 35% of the population.

## Statistical Validity Thresholds
- Minimum actions per agent for distribution analysis: 10+
- Minimum total actions per phase for statistical significance: 30+
- Minimum simulation rounds for convergence: 15-20
- Recommended: 30-35 rounds for most simulations
- Diminishing returns after: 50 rounds (validated empirically)
