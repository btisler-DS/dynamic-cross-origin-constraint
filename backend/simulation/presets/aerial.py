"""Aerial constraint preset (Constraint Set B).

Low friction, fast movement, wide field of view but low resolution.
"""

from ..engine import SimulationConfig

AERIAL_CONFIG = SimulationConfig(
    grid_size=30,
    num_obstacles=5,
    z_layers=6,
    max_steps=80,
    energy_budget=120.0,
    move_cost=0.5,
    collision_penalty=3.0,
    signal_dim=8,
    hidden_dim=64,
    learning_rate=1e-3,
    gamma=0.99,
    communication_tax_rate=0.005,
    survival_bonus=0.05,
    num_epochs=100,
    episodes_per_epoch=10,
)

AERIAL_META = {
    "name": "Aerial",
    "description": "Low friction, wide space, few obstacles. "
    "Agents have energy to spare but must coordinate over distance.",
    "constraints": [
        "Lower move cost (0.5x)",
        "Fewer obstacles (5)",
        "Larger grid (30x30)",
        "Low communication tax",
        "Higher energy budget",
    ],
}
