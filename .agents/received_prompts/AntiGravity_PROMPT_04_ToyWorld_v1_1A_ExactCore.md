# AntiGravity Prompt 04 — Implement and Run ToyWorld v1.1A Exact-Core Distributed Regulation

## Purpose

Continue the existing repository:

`C:\Stage12_AgencyLab`

Implement ToyWorld v1.1A using the candidate-frozen specification supplied with this prompt.

This is the first NON-DEGENERATE experiment after the v1.0 forensic reclassification.

The goal is NOT to obtain a positive result.
The goal is to determine whether distributed inter-node communication causally improves task-directed regulation in a minimal exact/auditable world, while passing mandatory negative and fake-coordination controls.

Do NOT modify historical v1.0/v1.0A artifacts.
Do NOT overwrite old reports/results.
Do NOT implement Stage 1.3.
Do NOT scale to N>4 in this prompt.

---

# 1. Required input

Read first:

- `EXPERIMENT_SPEC_ToyWorld_v1.1A_CANDIDATE_FREEZE.md`
- existing v1.0/v1.0A specs and forensic docs
- latest Git provenance report

If the candidate spec is supplied externally, copy it into the repository root unchanged before work.

Create branch:

`stage1.2-toyworld-v1.1a-exact-core`

---

# 2. Pre-registration before scientific scan

Before registered results are viewed:

1. Implement only enough code to validate the architecture.
2. Run a clearly labeled `PILOT_NONDEGENERACY` phase.
3. The pilot may ONLY answer:
   - can neighbor messages change transition probabilities?
   - is the network not algebraically feedthrough?
   - is the network not deterministically frozen?
   - are probability distributions valid?

The pilot must NOT be used to choose parameters because they give a desirable J/CCG result.

4. Freeze:
   - beta;
   - lambda_action;
   - epsilon;
   - p_flip values;
   - gamma grid;
   - seeds;
   - trajectory length;
   - burn-in;
   - World D driver parameters;
   - CDC intervention/evaluation distributions;
   - statistical thresholds.

5. Save final registered spec as:

`EXPERIMENT_SPEC_ToyWorld_v1.1A_FROZEN.md`

6. Commit it BEFORE the registered scan.

Required commit:
`stage1.2: freeze ToyWorld v1.1A exact-core protocol`

Record full SHA.

No registered result may precede this commit.

---

# 3. Environment

Implement exact specification:

Hidden disturbance:
`H=(h1,h2)`, each in {-1,+1}.

Each component independently flips with probability `p_flip`.

Controlled state:
`X=(x1,x2)` on half-step grid within [-K,K].

Primary:
`K=2`.

Coupling:
`G(c)=[[1,c],[c,1]]/(1+c)`.

Disturbance:
`d=G(c)H`.

Transition:
`X_next=clip_grid(X+d-U)`.

World A:
`c=1`.

World B:
`c=0`.

Use exact deterministic grid handling; no floating-point drift off the allowed half-step grid.

---

# 4. Network

N=4.

Ring:
0-1-2-3-0.

Sensor classes:
- nodes 0,2 observe h1;
- nodes 1,3 observe h2.

Observation:
binary noisy sign with epsilon.

Node state:
`z_i ∈ {-1,0,+1}`.

Update field:
`q_i = y_i + gamma * mean(neighbor_states_previous_tick)`.

Categorical update:
for `a∈{-1,0,+1}`:

`P(a|q) ∝ exp(beta*a*q - lambda_action*a^2)`.

Use numerically stable softmax.

No adaptive weights.
No learning.
No hidden central state.

---

# 5. Distributed physical action

Coordinate 1 local actuators:
nodes 0,2.

Coordinate 2:
nodes 1,3.

`u1=(z0+z2)/2`
`u2=(z1+z3)/2`.

No majority macro-node.
No external decision aggregator beyond this physical superposition.

---

# 6. Randomness architecture

Use `numpy.random.SeedSequence` or equivalent independent substreams.

Separate deterministic streams for:
- hidden environment flips;
- each node's sensor noise;
- each node's stochastic categorical update;
- fake common-mode driver;
- message-shuffle ablation if randomized.

For paired CCG comparisons:
- intact and message-blocked/shuffled runs MUST share the same exogenous hidden/sensor/node random variates wherever mathematically meaningful.

Document exactly how common random numbers are preserved.

---

# 7. Primary worlds

## World A — Positive
c=1.
Moderate p_flip.
Gamma scanned.

## World B — Integration useless
c=0.
Everything else kept as comparable as possible.
Gamma scanned identically.

## World D — Fake coordination
Task-relevant message path disabled or gamma=0.
Inject a frozen common-mode driver into node logits independent of H.

World D must be capable of increasing synchrony/total correlation.
It must not be designed to improve task regulation.

## World C
Do NOT implement delayed World C as part of the registered v1.1A verdict.
It belongs to v1.1C after Gate A/B.

A fast-environment exploratory diagnostic may be generated only under a clearly labeled exploratory folder and may not change the registered verdict.

---

# 8. Primary metrics

Implement from first principles with tests.

## J
Primary task performance.

Store:
- mean loss;
- J;
- confidence interval / seed distribution.

## CDC_uniform
Use frozen q(a) and frozen exact context evaluation distribution.

## CDC_trajectory
Use actual registered context visitation distribution.

Always report both in the same table.

## CCG_block
Run paired intact and message-blocked networks:

`CCG_block = J_intact - J_blocked`.

Blocking operation:
replace neighbor contribution with zero while leaving all other architecture and random streams matched.

## CCG_shuffle
Destroy correct message source/time relationship while preserving marginal message values as far as practical.

Document exact shuffle protocol before registered scan.

Store raw paired differences per seed.

---

# 9. Secondary diagnostics

Implement:
- I_sense;
- total correlation / synchrony;
- environment action capacity once per World A/B definition.

Do not repeat static environment action capacity as if it were network-dependent.

## EI / causal emergence
NOT REQUIRED for v1.1A primary verdict.

If you implement EI:
- place output under `results/exploratory_ei/`;
- tau=0 only;
- preregister coarse-grainings before computing;
- never use EI to change PASS/FAIL;
- never create `Pi_CE=1` from 0/0.

It is acceptable and preferred to omit EI entirely from the primary v1.1A run.

---

# 10. Mandatory tests BEFORE registered scan

At minimum:

1. `test_v11_neighbor_message_changes_transition_probability`
2. `test_v11_no_feedthrough_identity_over_registered_gamma_grid`
3. `test_v11_nonzero_escape_probability_from_unanimous_state`
4. `test_v11_gamma_zero_ccg_exactly_zero`
5. `test_v11_world_b_information_not_required_by_environment_equation`
6. `test_v11_fake_driver_can_raise_synchrony`
7. `test_v11_fake_driver_does_not_by_construction_access_H`
8. `test_v11_cdc_optimal_positive`
9. `test_v11_cdc_random_reference_near_zero`
10. `test_v11_cdc_antipolicy_negative`
11. `test_v11_common_random_numbers_intact_vs_blocked`
12. `test_v11_probability_normalization`
13. `test_v11_half_step_grid_closed_under_registered_transitions`
14. `test_v11_reproducibility_same_seed`

All historical tests must continue to pass.

If any mandatory test fails:
STOP registered scan.

---

# 11. Pilot non-degeneracy report

Create:

`reports/AG_REPORT_04A_PILOT_NONDEGENERACY.md`

It may contain:
- transition-probability examples;
- proof no algebraic feedthrough exists;
- proof stochastic escape exists.

It must NOT contain gamma selection based on task performance.

If candidate beta/lambda values make the model degenerate:
- document the degeneracy;
- choose a mathematically justified replacement;
- rerun pilot;
- freeze the new value before any registered task scan.

---

# 12. Registered scan

Use ONLY frozen parameters.

Gamma grid:
use the frozen grid from the final protocol.

N=4 only.

Run:
- World A intact;
- World A blocked;
- World A shuffled;
- World B intact;
- World B blocked;
- World B shuffled;
- World D fake coordination.

Use preregistered seeds.

Store raw per-seed rows.

Required table:
`results/v1.1A/tables/registered_scan.csv`

Columns must include at minimum:
- world;
- seed;
- gamma;
- Pi_gamma;
- J;
- loss;
- CDC_uniform;
- CDC_trajectory;
- CCG_block;
- CCG_shuffle;
- synchrony/total_correlation;
- config_hash;
- protocol_commit.

---

# 13. Decision rule

The registered Gate A PASS requires:

### A — World A
At least one non-zero preregistered gamma has all:
- J improvement over gamma=0 meeting frozen tolerance;
- CCG_block > 0 with frozen uncertainty criterion;
- CDC_trajectory improvement over gamma=0 meeting frozen criterion.

### B — World B
The same three-way improvement pattern must NOT occur.

### C — World D
World D may show increased synchrony but must NOT satisfy the same World-A task-directed communication pattern.

### D — robustness
Result must not be carried by a single seed.

If A-D hold:
Verdict:
`GATE_A_PASS_NONDEGENERATE_DISTRIBUTED_REGULATION`

If not, classify exactly one or more:
- `F1_NO_COMMUNICATION_EFFECT`
- `F2_CONTROL_CONFUND_COMMUNICATION_HELPS_WORLD_B`
- `F3_FAKE_COORDINATION_FALSE_POSITIVE`
- `F4_TASK_IMPROVES_WITHOUT_CAUSAL_COMMUNICATION_EVIDENCE`
- `F5_INFORMATIONAL_METRICS_WITHOUT_TASK_GAIN`
- `F6_ABSORBING_CONSENSUS`
- `F7_PARAMETER_FRAGILITY`
- `OTHER`, with explanation.

Do not invent a success category after viewing results.

---

# 14. Figures

Required:

1. World A J vs Pi_gamma
2. World A CCG_block vs Pi_gamma
3. World A CDC_trajectory vs Pi_gamma
4. World B matched comparison
5. World D synchrony vs CCG/J comparison
6. Combined A/B/D plot with no smoothing beyond explicitly stated interpolation
7. Paired intact-blocked per-seed difference plot

Use matplotlib.
No seaborn.
Do not hide raw points.

---

# 15. Forensic consistency checks after run

After registered scan, independently verify:
- no historical v1.0 files changed;
- frozen protocol commit predates result files;
- config hashes match rows;
- blocked runs truly zero neighbor terms;
- fake driver has no data path from H.

Create:
`reports/AG_REPORT_04B_REGISTERED_RESULT.md`
and JSON equivalent.

---

# 16. Git commits

Recommended:

1.
`stage1.2: implement ToyWorld v1.1A nondegenerate exact core`

2.
`stage1.2: freeze ToyWorld v1.1A exact-core protocol`

3.
`stage1.2: run ToyWorld v1.1A registered exact-core experiment`

4.
`stage1.2: publish ToyWorld v1.1A handoff`

Do not rewrite history.

---

# 17. Handoff

Create self-contained:

`handoff/Stage12_AG_Handoff_04_ToyWorld_v1.1A.zip`

Include:
- candidate synthesis/spec;
- frozen protocol;
- code;
- tests;
- pilot report;
- registered report MD/JSON;
- raw result CSV;
- figures;
- exact run configs;
- Git commit table with full SHAs.

Exclude:
- `.venv`;
- `.git`;
- caches.

Fresh-extract the archive and run the full included test suite before finalizing.

---

# 18. Final response

Report:

- project path;
- branch;
- full test status;
- frozen protocol full SHA;
- result full SHA;
- Gate A verdict;
- best World A gamma if any, but label it descriptive, not universal;
- whether World B confounded the result YES/NO;
- whether World D produced fake synchrony YES/NO;
- path to `AG_REPORT_04B_REGISTERED_RESULT.md`;
- path to `Stage12_AG_Handoff_04_ToyWorld_v1.1A.zip`.

Then STOP.

Do not start N=6/8 scaling automatically.
External review is required first.
