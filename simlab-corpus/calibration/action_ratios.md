# Social Media Action Distribution Benchmarks

## Real-World Platform Ratios

### Twitter/X (2024-2026 research)
Based on analysis of 10M+ tweets across diverse topics:
- Like/Heart: 38-45% of all actions
- Reply/Comment: 18-25% of all actions
- Retweet/Repost: 12-18% of all actions
- Quote Tweet: 8-12% of all actions
- Original Post: 15-20% of all actions
- Follow: 2-5% of all actions

### Reddit (2024-2026 research)
- Upvote: 55-65% of all actions
- Comment: 20-28% of all actions
- Original Post: 8-12% of all actions
- Downvote: 5-8% of all actions
- Award: 1-2% of all actions

### Key Insight: LLM Bias Toward Text Generation
Large language models, when given free choice of action in social simulation, overwhelmingly choose text-generating actions (CREATE_POST, QUOTE_POST) at 80-90% of total actions. This is because LLMs are trained on text generation and naturally prefer producing text over simulating non-textual actions like likes or follows.

**Recommendation:** Always use forced action probability weights to override LLM default behavior. Without explicit weighting, simulations will be unrealistically text-heavy and miss the majority passive-engagement pattern that characterizes real social media.

## Calibration Guide
- For general social media sims: like=0.40, comment=0.25, create=0.20, quote=0.10, repost=0.05
- For news/breaking events: like=0.30, comment=0.30, create=0.15, quote=0.15, repost=0.10
- For corporate/professional: like=0.35, comment=0.30, create=0.15, quote=0.10, repost=0.05, follow=0.02, nothing=0.03
- For polarized/political: like=0.25, comment=0.35, create=0.15, quote=0.15, repost=0.10
