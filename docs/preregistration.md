# Preregistration: The Δ-Variable Theory of Interrogative Emergence
https://doi.org/10.5281/zenodo.18738379

## Study Title
Testing Substrate-Independent Emergence of Interrogative Structures Under Resource Constraints in Multi-Agent Coordination Systems

## Theoretical Framework

**Core Theory**: Coordinating systems under resource constraints will spontaneously develop internal uncertainty management (Δ-variables) that manifests as interrogative coupling, following substrate-independent optimization principles.

**Δ-Variable Definition**: A Δ-variable is an explicitly represented, unresolved dependency variable that requires external information for resolution and creates mandatory coupling between systems.

**Key Theoretical Claims**:

1. **Structural Necessity**: Interrogative states emerge as optimal solutions to uncertainty management, not as linguistic phenomena
2. **Cost-Benefit Optimization**: Systems will develop interrogative behaviors despite higher energy costs when coordination benefits exceed expenditure
3. **Forced Coupling**: Unresolved Δ-variables create dependency edges that require inter-system coordination
4. **Silent Collapse Prevention**: Systems that act without resolving acknowledged uncertainty exhibit coordination failure
5. **Substrate Independence**: Under identical constraints, different cognitive architectures converge on similar Δ-management strategies

## Primary Predictions

**P1: Interrogative Emergence**
Agents will spontaneously develop QUERY-type signals with emergence rate ≥ 10% of total communications within 100 epochs, despite higher energy costs (1.5x vs 1.0x baseline).

**P2: Cost-Sensitivity Optimization**
Mean query emergence rate per condition will be inversely correlated with query cost across the four cost conditions (r < -0.70). Significance will be tested using individual seeds as observations (n=60 across 4 conditions, p < 0.01). Optimal query budget discovery expected within 200 epochs.

**P3: Temporal Coupling**
Query-Response Coupling (QRC) will exceed 0.90 for ≥ 20 consecutive epochs, measured as P(RESPONSE within 3 timesteps | QUERY at t) across all agent pairs.

**P4: Substrate Independence**
Heterogeneous agents (RNN/CNN/GNN) will each participate in query-response coupling, with no significant architectural differences (p > 0.10) in convergence rate to stable interrogative behavior. Note: Agent C (GNN) functions as a communication broker by role; differentiated final signal type distributions across architectures are expected due to role specialization and do not constitute evidence of substrate dependence. The test compares convergence epoch and QRC participation rate, not final signal type proportions.

**P5: Coordination Advantage**
Query-enabled agents will achieve ≥ 25% higher coordination efficiency (ROI: success_rate/energy_cost) compared to query-disabled controls.

## Experimental Design

**Environment**: Multi-agent coordination with dynamic targets, 20×20 grid
**Agents**: 3 heterogeneous agents per trial (RNN-1D, CNN-3D, GNN-relational)
**Episodes**: 500 epochs × 10 episodes per epoch
**Replication**: 15 independent seeds per condition

**Cost Structure Conditions**:
- **Baseline**: DECLARE=1.0x, QUERY=1.5x, RESPOND=0.8x
- **Low Pressure**: DECLARE=1.0x, QUERY=1.2x, RESPOND=0.9x
- **High Pressure**: DECLARE=1.0x, QUERY=3.0x, RESPOND=0.5x
- **Extreme**: DECLARE=1.0x, QUERY=5.0x, RESPOND=0.3x
- **Control**: Query signals disabled, DECLARE=1.0x only

## Primary Outcome Variables

**Emergence Metrics**:
1. **Query Emergence Rate**: Percentage of signals classified as QUERY type
2. **Emergence Epoch**: First epoch where query rate exceeds 5% sustainably (20+ epochs)

**Coupling Metrics**:
3. **Query-Response Coupling (QRC)**: P(RESPONSE within 3 timesteps | QUERY at t)
4. **Coupling Latency**: Mean timesteps between QUERY and corresponding RESPONSE
5. **Coupling Persistence**: Longest streak of QRC ≥ 0.90

**Optimization Metrics**:
6. **Information ROI**: (Coordination success rate) / (Total energy expenditure)
7. **Query Efficiency**: (Coordination improvement) / (Query energy spent)
8. **Protocol Entropy**: Shannon entropy of signal type distribution

**Substrate Metrics**:
9. **Architecture Convergence**: Coefficient of variation in final strategy metrics across agent types
10. **Cross-Architecture Coupling**: QRC measured specifically between different agent architectures

## Statistical Analysis Plan

**Power Analysis**: N=15 seeds provides 80% power to detect Cohen's d ≥ 0.8 effects at α=0.05

**Primary Tests**:
- **Emergence**: One-sample t-test of query emergence rate vs. 10% threshold
- **Cost Sensitivity**: Pearson correlation of query rate vs. cost across conditions  
- **Coupling**: Run-length analysis on QRC time series confirming ≥ 20 consecutive epochs exceeding QRC = 0.90 (per P3 criterion); supplemented by one-sample t-test of mean sustained QRC vs. 0.90 threshold
- **Substrate Independence**: One-way ANOVA of convergence epoch and QRC participation rate by agent architecture, with planned contrasts excluding Agent C signal-type proportions (broker role expected to differ); significant convergence-rate differences only constitute falsification
- **Coordination Advantage**: Two-sample t-test of ROI (query-enabled vs. control)

**Multiple Comparisons**: Bonferroni correction applied to 5 primary predictions (α=0.01)

**Changepoint Detection**: PELT algorithm to identify emergence epochs in type entropy timeseries

## Success Criteria

**Minimal Success**: P1, P3, and P5 confirmed (emergence, coupling, advantage)
**Strong Success**: All 5 primary predictions confirmed with committed effect sizes
**Paradigmatic Success**: P4 confirmed + replication across all cost conditions

## Falsification Criteria

**Theory is falsified if ANY of the following occur**:
1. Query emergence rate < 5% in baseline condition (averaged across seeds)
2. Maximum QRC never exceeds 0.70 in any condition  
3. No significant ROI advantage over query-disabled control (p > 0.05)
4. Significant architectural differences in convergence rate or QRC participation (p < 0.01), excluding Agent C signal-type proportions which are expected to differ due to broker role
5. No cost-sensitivity correlation (|r| < 0.30 across conditions)

## Controls and Robustness

**Control Conditions**:
- Query-disabled agents (Protocol 0 replication)
- Random signaling baseline
- Single-architecture homogeneous groups

**Robustness Checks**:
- Grid size variation (10×10, 30×30)  
- Agent count variation (2, 4, 6 agents)
- Target dynamics variation (static, slow, fast)
- Seed independence validation across 15 replications

## Data Management

**Precommitted Metrics**: Only the 10 primary outcome variables listed above will be used for hypothesis testing
**Exploratory Analysis**: Additional metrics may be computed but will be clearly labeled as exploratory
**Pilot Data**: Run 11 (seed=42, 500 epochs, Protocol 1 baseline condition) constitutes pilot data used to develop this preregistration and calibrate threshold predictions. It will be excluded from confirmatory hypothesis testing and reported separately as exploratory.
**Analysis Blinding**: Blinding to condition is not possible in computational research. All analysis will follow the preregistered statistical plan exactly; deviations will be documented and justified.
**Data Availability**: All code, datasets, and analysis scripts publicly available upon completion
**Preregistration Hash**: SHA-256: 7edc9113e39afb2dce430eb77802d5a6c10988e269eb823ae30e5508b12a8d6a

## Timeline

- **Week 1-2**: Protocol implementation and validation
- **Week 3-6**: Experimental execution (all conditions; 75 total runs at 500 epochs each requires parallel execution)
- **Week 7**: Statistical analysis per preregistered plan
- **Week 8**: Results writeup and data release

**Compute Note**: 5 conditions × 15 seeds × 500 epochs = 75 runs. Timeline assumes parallel execution across available hardware.

---

**Registration Commitment**: This preregistration represents our complete analytical strategy. No hypothesis tests beyond those specified will be used to support theoretical claims. Any deviations from this protocol will be explicitly documented and justified.

**Falsification Commitment**: If the specified falsification criteria are met, we commit to reporting this as evidence against the Δ-variable theory, regardless of other interesting patterns that may emerge in the data.