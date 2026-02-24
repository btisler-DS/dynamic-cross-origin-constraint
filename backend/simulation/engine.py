"""Simulation engine orchestrator.

Wires together environment, agents, communication buffer, training,
and metrics collection. Runs episodes and epochs, producing metrics
snapshots at each epoch boundary.

Protocol selection is via SimulationConfig.protocol:
    0 — Baseline (flat Landauer tax, no type head gradient — replicates Run 10)
    1 — Interrogative Emergence (Gumbel-Softmax, differential costs)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import torch
import torch.optim as optim
from torch.distributions import Categorical, Normal

from .environment import Environment, EnvironmentConfig
from .comm_buffer import CommBuffer, CommBufferConfig
from .agents import AgentA, AgentB, AgentC
from .training.reinforce import update_agents
from .metrics.shannon_entropy import compute_per_agent_entropy
from .metrics.mutual_information import compute_pairwise_mi
from .metrics.transfer_entropy import compute_all_pairs_te
from .metrics.zipf_analysis import compute_zipf_per_agent
from .metrics.energy_roi import compute_energy_roi
from .metrics.pca_snapshot import collect_signal_samples, fit_pca_and_project
from .protocols import create_protocol
from .utils.seeding import set_all_seeds


@dataclass
class SimulationConfig:
    seed: int = 42
    num_epochs: int = 100
    episodes_per_epoch: int = 10
    grid_size: int = 20
    num_obstacles: int = 8
    z_layers: int = 8
    max_steps: int = 100
    energy_budget: float = 100.0
    move_cost: float = 1.0
    collision_penalty: float = 5.0
    signal_dim: int = 8
    hidden_dim: int = 64
    learning_rate: float = 1e-3
    gamma: float = 0.99
    communication_tax_rate: float = 0.01
    survival_bonus: float = 0.1
    protocol: int = 1      # 0=Baseline, 1=Interrogative Emergence
    declare_cost: float = 1.0   # DECLARE signal cost multiplier (Protocol 1)
    query_cost: float = 1.5     # QUERY signal cost multiplier (Protocol 1)
    respond_cost: float = 0.8   # RESPOND signal cost multiplier (Protocol 1)
    output_dir: str = "."       # Directory for manifest and report output


class SimulationEngine:
    """Main simulation orchestrator."""

    def __init__(
        self,
        config: SimulationConfig | None = None,
        epoch_callback: Callable[[dict], None] | None = None,
    ):
        self.config = config or SimulationConfig()
        self.epoch_callback = epoch_callback
        self._paused = False
        self._stopped = False

        # Initialize seeds
        set_all_seeds(self.config.seed)

        # Protocol manager — drives reward, type resolution, and epoch extras
        self.protocol = create_protocol(
            self.config.protocol,
            declare_cost=self.config.declare_cost,
            query_cost=self.config.query_cost,
            respond_cost=self.config.respond_cost,
        )

        # Environment
        env_config = EnvironmentConfig(
            grid_size=self.config.grid_size,
            num_obstacles=self.config.num_obstacles,
            z_layers=self.config.z_layers,
            max_steps=self.config.max_steps,
            energy_budget=self.config.energy_budget,
            move_cost=self.config.move_cost,
            collision_penalty=self.config.collision_penalty,
        )
        self.env = Environment(env_config)

        # Communication buffer
        comm_config = CommBufferConfig(signal_dim=self.config.signal_dim)
        self.comm_buffer = CommBuffer(comm_config)

        # Build agents
        # Agent A obs_dim: 1 (target) + num_obstacles + 2 (other agents)
        obs_dim_a = 1 + self.config.num_obstacles + 2
        self.agent_a = AgentA(
            obs_dim=obs_dim_a,
            signal_dim=self.config.signal_dim,
            hidden_dim=self.config.hidden_dim,
        )

        self.agent_b = AgentB(
            signal_dim=self.config.signal_dim,
            hidden_dim=self.config.hidden_dim,
        )

        # Agent C obs_dim: pairwise distances
        n_entities = 1 + self.config.num_obstacles + 3  # target + obstacles + 3 agents
        obs_dim_c = n_entities * (n_entities - 1) // 2
        self.agent_c = AgentC(
            obs_dim=obs_dim_c,
            signal_dim=self.config.signal_dim,
            hidden_dim=self.config.hidden_dim,
        )

        self.agents = [self.agent_a, self.agent_b, self.agent_c]

        # Freeze type_head for Protocol 0 — no gradient through type classification
        if not self.protocol.should_train_type_head():
            for agent in self.agents:
                agent.freeze_type_head()

        # Optimizers
        self.optimizers = [
            optim.Adam(agent.parameters(), lr=self.config.learning_rate)
            for agent in self.agents
        ]

        # Metrics history
        self.epoch_metrics: list[dict] = []
        self._all_signal_samples: list[list[dict]] = []

    def run(self) -> list[dict]:
        """Run the full simulation. Returns list of epoch metrics."""
        self._all_signal_samples = []

        for epoch in range(self.config.num_epochs):
            if self._stopped:
                break

            while self._paused:
                time.sleep(0.1)
                if self._stopped:
                    break

            metrics = self._run_epoch(epoch)
            self.epoch_metrics.append(metrics)

            if self.epoch_callback:
                self.epoch_callback(metrics)

        # Post-run: fit global PCA and inject per-epoch projections
        if self._all_signal_samples:
            projections = fit_pca_and_project(self._all_signal_samples)
            for i, proj in enumerate(projections):
                if i < len(self.epoch_metrics):
                    self.epoch_metrics[i]['signal_pca'] = proj

        # Write run manifest
        self._write_manifest("manifest.json")

        return self.epoch_metrics

    def _run_epoch(self, epoch: int) -> dict:
        """Run one epoch (multiple episodes) and collect metrics."""
        epoch_rewards = {name: 0.0 for name in ["A", "B", "C"]}
        epoch_survivals = 0
        epoch_target_reached = 0
        epoch_steps = 0
        epoch_energy_spent = 0.0

        # Current temperature (Protocol 1: Gumbel-Softmax annealing; Protocol 0: unused)
        tau = self.protocol.get_tau(epoch)

        for agent in self.agents:
            agent.clear_episode()

        last_trajectory = None
        for episode in range(self.config.episodes_per_epoch):
            record_trajectory = (episode == self.config.episodes_per_epoch - 1)
            result = self._run_episode(epoch, tau=tau, record_trajectory=record_trajectory)
            for name in ["A", "B", "C"]:
                epoch_rewards[name] += result["total_rewards"][name]
            epoch_survivals += 1 if result["survived"] else 0
            epoch_target_reached += 1 if result["target_reached"] else 0
            epoch_steps += result["steps"]
            epoch_energy_spent += result["energy_spent"]
            if record_trajectory:
                last_trajectory = result.get("trajectory")

        # Training update
        losses = update_agents(self.agents, self.optimizers, self.config.gamma)

        # Compute signal metrics from comm buffer history (BEFORE reset)
        history = self.comm_buffer.history
        type_history = self.comm_buffer.type_history
        entropy = compute_per_agent_entropy(history)
        mi = compute_pairwise_mi(history)
        te = compute_all_pairs_te(history)
        zipf = compute_zipf_per_agent(history)

        avg_episodes = self.config.episodes_per_epoch
        target_rate = epoch_target_reached / avg_episodes
        avg_energy = epoch_energy_spent / avg_episodes
        roi = compute_energy_roi(target_rate, avg_energy)

        # Protocol-specific extras (inquiry metrics for P1, empty dict for P0)
        extras = self.protocol.compute_epoch_extras(
            type_history=type_history,
            signal_history=history,
            target_rate=target_rate,
            tax_rate=self.config.communication_tax_rate,
        )

        # Collect PCA signal samples before buffer reset
        pca_samples = collect_signal_samples(history, type_history)
        self._all_signal_samples.append(pca_samples)

        # Clear comm buffer history for next epoch
        self.comm_buffer.reset()

        metrics = {
            "epoch": epoch,
            "avg_reward": {k: v / avg_episodes for k, v in epoch_rewards.items()},
            "survival_rate": epoch_survivals / avg_episodes,
            "target_reached_rate": target_rate,
            "avg_steps": epoch_steps / avg_episodes,
            "avg_energy_spent": avg_energy,
            "losses": losses,
            "entropy": entropy,
            "mutual_information": mi,
            "transfer_entropy": te,
            "zipf": zipf,
            "energy_roi": roi,
            "comm_killed": self.comm_buffer.is_killed,
            "timestamp": time.time(),
            "trajectory": last_trajectory,
            "tau": tau,
        }
        metrics.update(extras)  # merges 'inquiry' dict for P1, nothing for P0

        return metrics

    def _run_episode(
        self,
        epoch_seed_offset: int,
        tau: float = 1.0,
        record_trajectory: bool = False,
    ) -> dict:
        """Run a single episode and return summary."""
        episode_seed = self.config.seed + epoch_seed_offset
        obs = self.env.reset(seed=episode_seed)

        self.agent_a.reset_hidden()

        total_rewards = {"A": 0.0, "B": 0.0, "C": 0.0}
        done = False

        trajectory = None
        if record_trajectory:
            trajectory = {
                "grid_size": self.env.grid_size,
                "target": self.env.target_pos.tolist(),
                "obstacles": [o.tolist() for o in self.env.obstacles],
                "steps": [],
            }

        while not done:
            signals = {}
            signal_types = {}
            action_logits = {}
            all_type_logits = {}

            for agent in self.agents:
                agent_obs = obs[agent.name]
                incoming = self.comm_buffer.receive_all(agent.name)

                signal, logits, type_logits = agent(agent_obs, incoming)

                # Protocol-aware type resolution:
                # P0: returns (None, 0) — no gradient, always DECLARE
                # P1: returns (soft_type, hard_type) — Gumbel-Softmax
                soft_type, hard_type = self.protocol.resolve_signal_type(
                    type_logits, tau, training=True
                )

                signals[agent.name] = signal
                signal_types[agent.name] = hard_type
                action_logits[agent.name] = logits
                all_type_logits[agent.name] = type_logits

            # Store signals and types in comm buffer
            for name, signal in signals.items():
                self.comm_buffer.send(name, signal, signal_type=signal_types[name])
            self.comm_buffer.record_history()

            # Sample actions and compute combined log probs
            actions = {}
            for agent in self.agents:
                logits = action_logits[agent.name]
                dist = Categorical(logits=logits)
                action = dist.sample()
                action_log_prob = dist.log_prob(action)

                # Protocol 1: include type_head gradient via joint log P(action, type | s)
                # Protocol 0: type_head is frozen — only action log_prob contributes
                if self.protocol.should_train_type_head():
                    type_dist = Categorical(logits=all_type_logits[agent.name])
                    type_log_prob = type_dist.log_prob(
                        torch.tensor(signal_types[agent.name])
                    )
                    combined_log_prob = action_log_prob + type_log_prob
                else:
                    combined_log_prob = action_log_prob

                agent.store_outcome(combined_log_prob, 0.0)  # reward filled below
                actions[agent.name] = action.item()

            # Environment step
            obs, env_rewards, done, info = self.env.step(actions)

            if trajectory is not None:
                trajectory["steps"].append({
                    "A": self.env.agents_pos["A"].tolist(),
                    "B": self.env.agents_pos["B"].tolist(),
                    "C": self.env.agents_pos["C"].tolist(),
                    "energy": {k: round(v, 1) for k, v in info["energy"].items()},
                })

            # Compute rewards via protocol
            for agent in self.agents:
                reward = self.protocol.compute_reward(
                    agent_name=agent.name,
                    env_reward=env_rewards[agent.name],
                    signal_sent=signals[agent.name],
                    energy_remaining=info["energy"][agent.name],
                    energy_budget=self.config.energy_budget,
                    communication_tax_rate=self.config.communication_tax_rate,
                    reached_target=info["reached_target"][agent.name],
                    survival_bonus=self.config.survival_bonus,
                    signal_type=signal_types[agent.name],
                )
                agent.rewards[-1] = reward
                total_rewards[agent.name] += reward

        result = {
            "total_rewards": total_rewards,
            "survived": info["done_reason"] != "energy_depleted",
            "target_reached": info["done_reason"] == "target_reached",
            "steps": info["step"],
            "energy_spent": self.env.total_energy_spent,
        }
        if trajectory is not None:
            result["trajectory"] = trajectory
        return result

    # --- Manifest helpers ---

    def _write_manifest(self, path: str) -> None:
        """Write a run summary manifest to disk."""
        import os
        if not self.epoch_metrics:
            return
        os.makedirs(self.config.output_dir, exist_ok=True)
        full_path = os.path.join(self.config.output_dir, path)
        manifest = {
            "protocol": self.config.protocol,
            "seed": self.config.seed,
            "declare_cost": self.config.declare_cost,
            "query_cost": self.config.query_cost,
            "respond_cost": self.config.respond_cost,
            "epochs_total": len(self.epoch_metrics),
            "final_metrics": self._extract_final_metrics(self.epoch_metrics[-1]),
            "crystallization_epoch": self._find_crystallization_epoch(self.epoch_metrics),
            "phase_transitions": self._detect_phase_transitions(self.epoch_metrics),
            "performance_stats": self._compute_performance_stats(self.epoch_metrics),
        }
        with open(full_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def _extract_final_metrics(self, last_epoch: dict) -> dict:
        inq = last_epoch.get('inquiry', {})
        if not isinstance(inq, dict):
            inq = {}
        return {
            'survival_rate': last_epoch.get('survival_rate', 0),
            'target_reached_rate': last_epoch.get('target_reached_rate', 0),
            'energy_roi': last_epoch.get('energy_roi', 0),
            'type_entropy': inq.get('type_entropy', None),
            'qrc': inq.get('query_response_coupling', None),
        }

    def _find_crystallization_epoch(self, epochs: list[dict]) -> int | None:
        """First epoch in a streak of 5 consecutive epochs with type_entropy < 0.95."""
        if self.config.protocol != 1:
            return None
        streak_start = None
        streak_count = 0
        for m in epochs:
            inq = m.get('inquiry', {})
            if not isinstance(inq, dict):
                streak_count = 0
                streak_start = None
                continue
            te = inq.get('type_entropy', None)
            if te is not None and te < 0.95:
                if streak_count == 0:
                    streak_start = m['epoch']
                streak_count += 1
                if streak_count >= 5:
                    return streak_start
            else:
                streak_count = 0
                streak_start = None
        return None

    def _detect_phase_transitions(self, epochs: list[dict]) -> list[dict]:
        """Epochs where type_entropy drops by more than 0.05 in a single step."""
        transitions = []
        prev_te = None
        for m in epochs:
            inq = m.get('inquiry', {})
            if not isinstance(inq, dict):
                continue
            te = inq.get('type_entropy', None)
            if te is not None and prev_te is not None:
                delta = prev_te - te
                if delta > 0.05:
                    transitions.append({
                        'epoch': m['epoch'],
                        'entropy_before': round(prev_te, 4),
                        'entropy_after': round(te, 4),
                        'delta': round(delta, 4),
                    })
            prev_te = te
        return transitions

    def _compute_performance_stats(self, epochs: list[dict]) -> dict:
        survival_rates = [m.get('survival_rate', 0) for m in epochs]
        target_rates = [m.get('target_reached_rate', 0) for m in epochs]
        n = max(len(survival_rates), 1)
        return {
            'avg_survival_rate': round(sum(survival_rates) / n, 4),
            'avg_target_rate': round(sum(target_rates) / n, 4),
            'max_survival_rate': round(max(survival_rates) if survival_rates else 0, 4),
            'max_target_rate': round(max(target_rates) if target_rates else 0, 4),
        }

    # --- Control methods ---

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        self._stopped = True
        self._paused = False

    def kill_communication(self) -> None:
        self.comm_buffer.kill()

    def restore_communication(self) -> None:
        self.comm_buffer.restore()

    @property
    def is_running(self) -> bool:
        return not self._stopped and not self._paused

    def get_agent_weights(self) -> dict[str, dict]:
        """Export all agent state dicts."""
        return {agent.name: agent.state_dict() for agent in self.agents}

    def save_checkpoint(self, path: str, epoch: int) -> None:
        """Save full simulation state for checkpoint/resume across epoch boundaries."""
        torch.save({
            "epoch": epoch,
            "agent_states":     {a.name: a.state_dict() for a in self.agents},
            "optimizer_states": [o.state_dict() for o in self.optimizers],
            "epoch_metrics":    self.epoch_metrics,
        }, path)

    def load_checkpoint(self, path: str) -> int:
        """Load checkpoint and return the epoch to resume from."""
        ckpt = torch.load(path, weights_only=False)
        for agent in self.agents:
            agent.load_state_dict(ckpt["agent_states"][agent.name])
        for opt, state in zip(self.optimizers, ckpt["optimizer_states"]):
            opt.load_state_dict(state)
        self.epoch_metrics = ckpt["epoch_metrics"]
        return int(ckpt["epoch"])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run MARL simulation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--protocol", type=int, default=1, choices=[0, 1],
                        help="0=Baseline (Run 10 behaviour), 1=Interrogative Emergence")
    parser.add_argument("--declare-cost", type=float, default=1.0,
                        help="DECLARE signal cost multiplier (Protocol 1)")
    parser.add_argument("--query-cost", type=float, default=1.5,
                        help="QUERY signal cost multiplier (Protocol 1)")
    parser.add_argument("--respond-cost", type=float, default=0.8,
                        help="RESPOND signal cost multiplier (Protocol 1)")
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Directory for manifest and report output")
    args = parser.parse_args()

    def print_metrics(m: dict) -> None:
        inq = m.get('inquiry', {})
        te_str = (
            f" | H: {inq['type_entropy']:.3f}"
            if isinstance(inq, dict) and 'type_entropy' in inq
            else ""
        )
        print(
            f"Epoch {m['epoch']:3d} | "
            f"Survival: {m['survival_rate']:.2f} | "
            f"Target: {m['target_reached_rate']:.2f} | "
            f"Reward A: {m['avg_reward']['A']:.3f}"
            f"{te_str}"
        )

    config = SimulationConfig(
        seed=args.seed,
        num_epochs=args.epochs,
        episodes_per_epoch=args.episodes,
        protocol=args.protocol,
        declare_cost=args.declare_cost,
        query_cost=args.query_cost,
        respond_cost=args.respond_cost,
        output_dir=args.output_dir,
    )
    engine = SimulationEngine(config=config, epoch_callback=print_metrics)
    engine.run()
    print("Simulation complete.")
