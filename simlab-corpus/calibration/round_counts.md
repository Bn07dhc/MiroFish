# Simulation Round Count Calibration

## Round Count by Purpose

### Quick Exploration (15-20 rounds)
- Purpose: rapid prototyping, testing agent configurations
- Sufficient for: initial behavior patterns, basic interaction dynamics
- Not sufficient for: convergence, emergent behavior, phase transitions

### Standard Simulation (25-35 rounds)
- Purpose: full simulation with meaningful dynamics
- Sweet spot: 30 rounds for most use cases
- Sufficient for: 2-3 phase transitions, convergence detection
- Empirically validated: most sims reach steady state by round 25-30

### Deep Analysis (40-60 rounds)
- Purpose: studying long-term dynamics, multiple equilibria
- Useful for: political polarization, market cycles, organizational change
- Warning: diminishing returns after round 50 (empirically validated)
- Cost: linear with round count (each round = LLM calls for all active agents)

## Dead Round Prevention
Simulations using time-of-day modeling (peak/off-peak hours) often waste rounds on dead periods. Key findings:
- Off-peak multiplier of 0.05 = rounds with 0 active agents (wasted compute)
- Minimum viable off-peak multiplier: 0.15 (ensures some activity every round)
- Better approach: start simulation at first active hour (skip midnight-6am)
- Best approach: use start_hour parameter to begin at 8:00

## Convergence Detection
Rather than fixed round counts, use automatic convergence detection:
1. Track action count per round in a sliding window (5 rounds)
2. Compute coefficient of variation (CV = std/mean)
3. If CV < 0.1 for 5 consecutive rounds, simulation has converged
4. Additional criteria: topic entropy < 0.3, agent participation stability
5. Never check before round 15 (allow dynamics to develop)
