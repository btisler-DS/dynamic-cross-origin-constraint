"""Deep-Sea constraint preset (Constraint Set A).

High energy cost, limited visibility, acoustic-only perception.
"""

from ..engine import SimulationConfig

DEEP_SEA_CONFIG = SimulationConfig(
    grid_size=25,
    num_obstacles=15,
    z_layers=12,
    max_steps=150,
    energy_budget=80.0,
    move_cost=1.5,
    collision_penalty=8.0,
    signal_dim=8,
    hidden_dim=64,
    learning_rate=1e-3,
    gamma=0.99,
    communication_tax_rate=0.02,
    survival_bonus=0.15,
    num_epochs=100,
    episodes_per_epoch=10,
)

DEEP_SEA_META = {
    "name": "Deep-Sea",
    "description": "High pressure, high cost. Acoustic echo only. "
    "Agents must develop efficient protocols to survive.",
    "constraints": [
        "Higher move cost (1.5x)",
        "More obstacles (15)",
        "Larger grid (25x25)",
        "Higher communication tax",
        "Reduced energy budget",
    ],
}
