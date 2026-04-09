# Monte Carlo Methods for Simulation Validation

## Why Monte Carlo in Agent-Based Simulation

Agent-based simulations are inherently stochastic — random seeds, LLM sampling temperature, and probabilistic agent activation all introduce variance. A single simulation run is an anecdote, not evidence. Monte Carlo methods turn single runs into statistically grounded results.

## Replicate Runs

### How Many Replicates?
- Minimum: 3 runs per configuration (for basic variance estimation)
- Recommended: 5-10 runs for publication-grade results
- For parameter sweeps: 3 runs per parameter combination

### What to Vary Between Replicates
- Random seed (controls agent activation, action selection)
- LLM temperature jitter (±0.05 from configured temperature)
- Agent ordering (shuffle agent evaluation order each run)

### What to Hold Constant
- Agent archetypes and counts
- Phase transitions and timing
- Action weight distributions
- Influence weights and activity levels

## Parameter Sensitivity Analysis

### One-at-a-Time (OAT) Sensitivity
Test each parameter independently while holding others at baseline:
1. Vary off_peak_multiplier: [0.05, 0.10, 0.15, 0.20, 0.30]
2. Vary sentiment_bias range: [±0.2, ±0.4, ±0.6, ±0.8]
3. Vary influence ratio (max/min): [2x, 3x, 5x, 8x]
4. Vary agent count: [15, 20, 25, 30, 40]
5. Measure: action distribution, convergence time, opinion cluster count

### Sobol Sensitivity Indices
For understanding which parameters matter most:
- First-order: direct effect of each parameter
- Total-order: effect including interactions
- Typical finding: influence_weight and action_weights have highest first-order effects; sentiment_bias × echo_chamber_strength has highest interaction effect

## Bootstrap Confidence Intervals

### For Action Ratios
Given N total actions across a simulation:
1. Resample N actions with replacement (1000 bootstrap samples)
2. Compute action type proportions for each sample
3. Report 2.5th and 97.5th percentiles as 95% CI

### For Convergence Time
Given K replicate runs:
1. Record convergence round for each run
2. Bootstrap K values with replacement (1000 samples)
3. Report median and [2.5%, 97.5%] percentiles

## Hypothesis Testing for Simulation Comparison

### Comparing Two Configurations
"Does changing off_peak_multiplier from 0.05 to 0.15 significantly change convergence time?"
- Run both configs N times (N ≥ 5)
- Use Mann-Whitney U test (non-parametric, safe for small N)
- Report effect size (Cohen's d or rank-biserial correlation)

### Comparing Action Distributions
"Does weighted action selection produce more realistic action ratios?"
- Use Chi-squared goodness-of-fit test against real-world benchmarks
- Compare χ² statistic between old config and new config
- Lower χ² = closer to real-world distribution

## Bayesian Calibration

### Approximate Bayesian Computation (ABC)
When you have real-world data to calibrate against:
1. Define prior distributions for parameters (from corpus knowledge)
2. Run simulations with parameter samples from priors
3. Compare simulation output to real-world observations
4. Accept parameter combinations that produce outputs within tolerance ε
5. Posterior = distribution of accepted parameters

### Sequential Monte Carlo (SMC-ABC)
More efficient than basic ABC:
1. Start with wide priors
2. Run wave of simulations
3. Keep top 10% closest to observations
4. Use accepted parameters as priors for next wave
5. Iterate 3-5 waves → narrow posterior

**Practical use:** If you have real social media data for a topic (e.g., actual Twitter engagement on a corporate announcement), use ABC to find the simulation parameters that best reproduce the observed dynamics. Then use those calibrated parameters for counterfactual "what-if" simulations.

## Variance Reduction Techniques

### Common Random Numbers
When comparing two configurations:
- Use the same random seed sequence for both
- Differences in output are due to configuration change, not randomness
- Dramatically reduces variance of the difference estimate

### Antithetic Variates
For each simulation run with seed S:
- Run a paired simulation with inverted random draws
- Average the pair → lower variance than two independent runs
- Works well for agent activation and action selection

### Stratified Sampling for Parameter Sweeps
Instead of random parameter combinations:
- Divide each parameter range into strata
- Sample one point from each stratum (Latin Hypercube Sampling)
- Better coverage of parameter space with fewer runs
- For 5 parameters × 5 levels = 25 runs covers the space efficiently
