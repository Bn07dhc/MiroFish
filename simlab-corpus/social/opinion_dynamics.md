# Opinion Dynamics in Social Simulation

## Classical Models

### Bounded Confidence (Hegselmann-Krause)
Agents only interact with others whose opinions are within a confidence bound ε. Key properties:
- Small ε (< 0.2): society fragments into many opinion clusters
- Large ε (> 0.4): consensus emerges
- ε ≈ 0.25-0.3: 2-3 stable opinion clusters (most realistic for polarized topics)

**Simulation implication:** Sentiment bias ranges in agent configs should reflect bounded confidence. Agents with sentiment_bias > 0.3 apart rarely convince each other. Use this to calibrate echo chamber effects.

### DeGroot Consensus Model
Agents update opinions as weighted averages of their neighbors. Key properties:
- Converges if influence network is strongly connected
- Speed of convergence depends on network structure
- High-influence nodes accelerate convergence but can create fragile consensus

**Simulation implication:** influence_weight in agent configs directly maps to DeGroot weights. Keep max/min influence ratio below 5:1 to prevent single-agent dominance.

## Information Cascades (Bikhchandani et al.)
Sequential agents observe predecessors' actions and rationally follow, regardless of private information:
- Cascades form quickly (3-5 sequential adopters)
- Cascades are fragile — easily broken by credible contrarian signals
- Late-round agents have more information but less influence on cascade direction

**Simulation implication:** In early rounds, broker agents set the narrative. Skeptics become most valuable in mid-to-late rounds when they can break false cascades. Phase transitions should reflect this timing.

## Echo Chamber Formation
Echo chambers emerge when:
1. Agents preferentially interact with similar-opinion agents (homophily)
2. Platform algorithms amplify popular content within clusters
3. Cross-cluster bridges (conduit agents) are too few or too weak

**Simulation implication:** Include conduit/bridge agents at 5-10% of population. Set echo_chamber_strength parameter carefully — values above 0.7 produce unrealistic single-cluster convergence.

## Sentiment Bias Calibration
- Narrow range [-0.3, +0.3]: Mild disagreement, consensus likely
- Medium range [-0.6, +0.6]: Clear polarization, 2-3 clusters likely
- Wide range [-0.8, +0.8]: Extreme polarization, fragmentation likely
- For most simulations: [-0.6, +0.6] produces realistic dynamics
