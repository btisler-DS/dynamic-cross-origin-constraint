"""Social constraint preset (Constraint Set C).

Dense environment, high agent interaction, communication is cheap
but collisions are expensive.
"""

from ..engine import SimulationConfig

SOCIAL_CONFIG = SimulationConfig(
    grid_size=15,
    num_obstacles=12,
    z_layers=8,
    max_steps=120,
    energy_budget=100.0,
    move_cost=1.0,
    collision_penalty=10.0,
    signal_dim=12,
    hidden_dim=64,
    learning_rate=1e-3,
    gamma=0.99,
    communication_tax_rate=0.005,
    survival_bonus=0.2,
    num_epochs=100,
    episodes_per_epoch=10,
)

SOCIAL_META = {
    "name": "Social",
    "description": "Dense, collision-heavy environment. Communication is cheap, "
    "but navigating requires constant coordination.",
    "constraints": [
        "Small grid (15x15)",
        "Dense obstacles (12)",
        "High collision penalty (10)",
        "Cheap communication",
        "Higher survival bonus",
    ],
}
