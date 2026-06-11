# Large-scale scenario testing (dry-run)

Validate the simulation pipeline with a **large number of agents** on a current
trending topic — **without spending any LLM credits**. In dry-run mode agents
perform randomized scripted actions (`CREATE_POST` / `LIKE_POST` / `DO_NOTHING`)
instead of `LLMAction`, so the full OASIS environment (agent graph, recsys,
database, action logging) and MiroFish's dynamic-event / intervention paths are
exercised end-to-end with no network or API key.

## 1. Generate a trending scenario

```bash
cd backend
python scripts/make_scenario.py \
  --topic "全国高温预警下的电力保供" \
  --agents 500 --rounds 20 --platform reddit \
  --out /tmp/scn_trending --seed 7
```

This writes `reddit_profiles.json` (agents with mixed support/oppose/neutral/observer
stances) and `simulation_config.json` (with `active_fraction`, seed posts, and two
mid-run `scheduled_events`).

## 2. Dry-run it

```bash
python scripts/run_parallel_simulation.py \
  --config /tmp/scn_trending/simulation_config.json \
  --reddit-only --dry-run --no-wait
```

`--dry-run` works with `--twitter-only`, `--reddit-only`, or parallel (both).
Results land in `/tmp/scn_trending/{reddit,twitter}/actions.jsonl`.

From the API, pass `"dry_run": true` to `POST /api/simulation/start`.

## 3. Inject a God's-eye intervention (optional)

Queue a runtime intervention that the active loop picks up at the next round:

```python
import sys; sys.path.insert(0, "scripts")
import simulation_events as se
se.queue_intervention("/tmp/scn_trending",
    "突发：某地变电站故障导致大面积停电，应急部门已介入",
    platform="reddit", label="external shock")
```

(Or, on a running sim, `POST /api/simulation/<id>/intervention`.)

## Scaling note: `active_fraction`

Historically each round activated a population-**independent** absolute number of
agents (~5–30), so with 1000 agents ~97% never acted and the crowd was inert.
`time_config.active_fraction` (set by `make_scenario.py`) makes participation grow
with the candidate pool:

```
active = max(absolute_target, round(n_candidates * active_fraction * time_multiplier))
```

capped by `max_active_per_round`. `active_fraction = 0` preserves the legacy behavior.

Observed on a 500-agent / 20-round reddit dry-run: **244/500 agents participated**,
realistic action mix, and a clear day/night activity curve (night lull → midday peak).
