"""risk-metric-bench: a metric-agnostic benchmark for surrogate safety
metrics on SUMO Monte Carlo scenarios with ground-truth collision labels.

The question this package answers is narrow and empirical: given the state
of a vehicle and its neighbors at time t, how well does a risk metric's
score predict whether that vehicle is actually involved in a collision
within the next H seconds? Metrics are plug-ins; the harness does not care
what is being scored. Shipped adapters: inverse TTC, negated TTS margin,
and PORA (via the pora-replication package).
"""
