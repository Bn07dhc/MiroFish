# Platform Engagement Pattern Benchmarks

## Temporal Activity Patterns

### Global Social Media Activity (UTC-normalized)
Peak activity hours vary by region but follow consistent patterns:
- Morning surge: 07:00-09:00 local (commute checking)
- Lunch dip: 12:00-13:00 local (moderate activity)
- Afternoon steady: 14:00-17:00 local (work-hour browsing)
- Evening peak: 19:00-22:00 local (highest engagement)
- Night decline: 22:00-01:00 local (gradual drop)
- Dead zone: 02:00-06:00 local (minimal activity)

### Activity Multipliers (empirical)
Based on analysis of 50M+ social media actions across platforms:
- Dead hours (02:00-06:00): 0.05-0.10x baseline
- Morning (07:00-09:00): 0.4-0.6x baseline
- Work hours (09:00-18:00): 0.6-0.8x baseline
- Evening peak (19:00-22:00): 1.3-1.8x baseline
- Night (22:00-01:00): 0.4-0.6x baseline

**Key finding:** Real peak-to-trough ratio is 10-20x, not the 3x commonly modeled. A peak multiplier of 1.5 with off-peak 0.05 gives only 30x ratio, which is reasonable. But off-peak 0.05 rounds produce zero agents, wasting compute. Use minimum 0.15 for off-peak.

### Professional/Corporate Platforms
Different pattern than consumer social media:
- Peak: 09:00-11:00 and 14:00-16:00 (business hours)
- Secondary: 20:00-21:00 (evening catch-up)
- Off-peak multiplier should be higher (0.2-0.3) — professionals check messages more regularly

## Engagement Depth Distribution
How deep users engage with content:
- View only (no action): 70-80% of content views
- Single reaction (like): 15-20% of engaged viewers
- Comment/Reply: 3-8% of engaged viewers
- Share/Repost: 2-5% of engaged viewers
- Original content creation: 1-3% of active sessions

## Influence Distribution
Social media influence follows a power law:
- Top 1% of users generate 20-30% of content
- Top 10% generate 60-70% of content
- Bottom 50% generate < 5% of content

**Simulation implication:** influence_weight should follow a power law, not uniform distribution. Recommended max/min ratio: 4-6x for realistic sims, with most agents clustered at 0.5-1.5x.
