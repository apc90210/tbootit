# Stage 1.2 — Synthesis of Independent Peer Reviews and ToyWorld v1.1 Design Decision

## Status

Two independent review streams were compared:

- Agent 1: adversarial review of the actual ToyWorld v1.0/v1.0A code, metrics, results and provenance.
- Agent 2: blind design from first principles, without access to the existing ToyWorld implementation/results.

This document records the convergent principles, rejected proposals, and the selected architecture for ToyWorld v1.1.

## 1. Independent convergence

Both reviewers independently converge on the following principles:

1. **Partial observability must be real.**
   No single ordinary node may possess all information required for optimal control.

2. **Information must be distributed.**
   Different nodes must observe different components/sectors of the environment.

3. **Communication must have both benefit and cost/failure modes.**
   It must be possible for communication to help, do nothing, or hurt depending on regime.

4. **No omniscient central controller.**
   The action channel must not simply read one privileged node with complete information.

5. **Four control worlds are mandatory.**
   - positive integration;
   - integration useless;
   - integration harmful/adversarial;
   - fake coordination without task-relevant distributed causality.

6. **Task-directed regulation and internal coherence are not the same.**
   Synchrony/correlation/causal-emergence-like quantities cannot by themselves establish agency-like regulation.

7. **Exact small-N regime comes first.**
   Approximate information estimators at larger N must never be mixed with exact values before overlap calibration.

8. **A null result is valid.**
   The experiment must be capable of finding no threshold or only a smooth crossover.

## 2. Main disagreement

Agent 1 recommends:
- task-directed causal control (CDC) and performance as primary;
- EI/causal emergence only as secondary diagnostic;
- small exact N first.

Agent 2 proposes:
- a multidimensional partially observed controlled dynamical system;
- distributed local actuators with no central readout;
- but also proposes an order parameter
  `Psi = Pi_reg * Theta(Pi_CE - 1)`,
  making EI a gate for successful macro-regulation.

Decision:
**Do not use Pi_CE as a primary gate in ToyWorld v1.1.**

Reason:
- causal emergence is representation/coarse-graining dependent;
- v1.0 already demonstrated that an apparently clean ratio can be misleading;
- the research question is specifically whether distributed communication causally improves task-directed regulation.

EI may be computed later as an exploratory diagnostic only under a preregistered coarse-graining and only where the Markov state is exact.

## 3. Selected conceptual architecture

ToyWorld v1.1 will combine the strongest parts of both proposals:

- Agent 2's **two-component partially observed environment**;
- Agent 2's **distributed local actuator superposition**, avoiding a central majority readout;
- Agent 1's **contextual task-directed causal metrics**;
- Agent 1's **exact-core-first discipline**;
- both agents' positive/negative/adversarial/fake-coordination controls.

## 4. Key simplification relative to both proposals

ToyWorld v1.1 will NOT use:
- adaptive observation weights;
- learned node policies;
- JAX/GPU;
- N > 8;
- approximate EI;
- thermodynamic “phase transition” language;
- a single scalar agency score.

The first goal is smaller:

**Demonstrate or falsify a non-degenerate distributed-regulation effect in an exact/auditable small system.**

## 5. Selected environment

Hidden disturbance:
`H_t = (h1_t, h2_t)`, with `h1,h2 ∈ {-1,+1}`.

Each component evolves as an independent two-state Markov chain:
`P(hj_{t+1} = -hj_t) = p_flip`.

Controlled environmental state:
`X_t = (x1_t, x2_t)` on a bounded half-step grid.

Target:
`X* = (0,0)`.

Coupling parameter:
`c_env ∈ {0,1}` in v1.1 exact core.

Effective disturbance:
`d(H,c) = G(c) H`,
with
`G(c) = [[1,c],[c,1]]/(1+c)`.

Thus:
- at `c=0`, coordinate 1 depends only on h1 and coordinate 2 only on h2;
- at `c=1`, each controlled coordinate depends on both hidden disturbance components.

This gives a principled positive-vs-negative control without changing the basic simulator.

Environment transition:
`X_{t+1} = clip_grid(X_t + d(H_t,c_env) - U_t)`.

## 6. Nodes and local sensing

Exact core:
`N=4`.

Sensor classes:
- nodes 0 and 2 observe noisy h1;
- nodes 1 and 3 observe noisy h2.

Observation:
`y_i(t) ∈ {-1,+1}`

with:
`P(y_i = true_component) = 1-epsilon`.

No node directly observes both h1 and h2.

Primary graph:
4-node ring with alternating sensor classes.

This graph is deliberately simple:
every node's neighbors belong to the opposite sensor class, so cross-component information can flow without a privileged central node.

## 7. Node internal state and update

Node internal state:
`z_i(t) ∈ {-1,0,+1}`.

Messages are the previous internal states of neighbors.

No adaptive weights in v1.1A.

Local field:
`q_i(t) = w_obs*y_i(t) + gamma * mean_{j in N(i)} z_j(t-1)`.

Primary fixed:
`w_obs = 1`.

Primary scanned communication coupling:
`gamma >= 0`.

Probabilistic ternary update:
`P(z_i(t)=a) ∝ exp(beta * a * q_i(t) - lambda_action*a^2)`
for `a ∈ {-1,0,+1}`.

This has three important properties:
1. neighbor information can affect the probability of the next node state;
2. no term is algebraically guaranteed to determine the sign;
3. finite temperature/probabilistic updating avoids deterministic absorbing consensus.

Primary beta and lambda_action must be fixed before the registered scan and must not be tuned after results.

## 8. Distributed action without central aggregator

Nodes are also local actuators.

Actuator group for coordinate 1:
nodes {0,2}.

Actuator group for coordinate 2:
nodes {1,3}.

Environmental control:
`u1_t = (z0_t + z2_t)/2`
`u2_t = (z1_t + z3_t)/2`

Therefore:
`U_t = (u1_t,u2_t)`.

The environment receives physical superposition/averaging of local actions.
There is no extra “macro decision node”.

At c_env=1, each actuator group's optimal decision depends partly on the hidden component observed by the other sensor class; communication can therefore add task-relevant information.

At c_env=0, cross-class information is unnecessary; communication should not improve the task and can hurt.

## 9. Primary worlds

### World A — Positive Integration
- c_env = 1
- moderate p_flip
- epsilon > 0
- communication coupling gamma scanned

Prediction:
intermediate non-zero gamma may improve regulation relative to gamma=0.

### World B — Integration Useless
- c_env = 0
- same node/graph/action architecture

Each actuator group already senses the disturbance component relevant to its own coordinate.
Cross-class information provides no necessary additional task information.

Prediction:
communication gain should be near zero or negative.

### World C — Integration Harmful
- c_env = 1
- fast p_flip and/or one-step communication delay in the simulation-only timing extension

Prediction:
stale neighbor information can reduce performance as communication coupling increases.

### World D — Fake Coordination
- task-relevant communication removed or gamma=0;
- add a shared common-mode driver to node logits that is independent of H_t.

Prediction:
internal synchrony/total correlation can become high while task-directed communication gain remains near zero and J fails to improve.

This control is mandatory.

## 10. Primary metrics

### 10.1 Task performance
Loss:
`L_t = (x1_t^2 + x2_t^2)/(2*K^2)`.

Primary score:
`J = -E[L_t]`.

Always report raw loss as well.

### 10.2 Contextual Directed Control
Report BOTH:
- `CDC_uniform`
- `CDC_trajectory`

They answer different questions and neither may replace the other post hoc.

### 10.3 Causal Communication Gain — new primary integration metric

Define a paired intervention/ablation comparison under common random numbers:

`CCG = J_intact_messages - J_message_blocked`

Optionally also:
`CCG_shuffle = J_intact_messages - J_message_shuffled`

Message-blocked means the same network/environment/sensor random streams are used but neighbor messages are replaced with zero.
Message-shuffled preserves marginal message statistics but destroys their correct causal timing/source relationship.

Interpretation:
- CCG > 0: communication causally improves task regulation;
- CCG ≈ 0: communication is irrelevant;
- CCG < 0: communication harms regulation.

This directly operationalizes the central Stage 1.2 question and is more task-specific than raw total correlation or EI.

### 10.4 Resilience
Report raw loss/J under lesions.
Do not use unstable ratios with negative J.

Primary lesion protocol:
randomly disable one non-entire-actuator-class node at a time in N=4 exact core, then later random fractions for larger N.

### 10.5 Secondary diagnostics
- I_sense;
- total correlation / synchrony;
- environment actuator capacity reported once per environment, not per network row.

### 10.6 Causal emergence / EI
Exploratory only in v1.1.

Rules:
- never gates success;
- only where the exact Markov representation is valid;
- never compare exact EI with approximate EI;
- preregister at least two coarse-grainings if used;
- report undefined ratios honestly.

## 11. What counts as a v1.1 result

Do NOT call the v1.1 exact-core result a thermodynamic phase transition.

Allowed categories:
- no effect;
- harmful communication;
- smooth crossover;
- operational control threshold;
- bifurcation-like change (only if attractor structure demonstrates it).

Primary successful signal:
in World A, for a preregistered gamma range:
- J improves over gamma=0;
- CCG > 0;
- CDC_trajectory improves;
while World B does not show the same benefit and World D can show coherence without CCG.

This is evidence of non-degenerate distributed regulation, not “macroagent proven”.

## 12. Gate structure

### Gate v1.1A — exact/non-degeneracy gate
N=4 only.
No approximate estimators.
Primary ring topology.
tau_c=0 in the exact registered core.

Required before any scaling:
- prove no feedthrough theorem exists over scanned gamma;
- demonstrate neighbor intervention changes node transition probabilities for at least some reachable states;
- validate World B;
- validate fake-coordination control;
- verify CDC/CCG analytically on tiny constructed cases.

If Gate A fails:
STOP. Do not scale N.

### Gate v1.1B — small finite-size replication
Only if Gate A passes:
N=6 and N=8 using simulation/common random numbers.

Goals:
- test whether qualitative World A/B/C/D distinctions persist;
- test whether candidate gamma threshold/crossover drifts with N;
- no approximate EI required.

### Gate v1.1C — timing extension
Only after A/B:
introduce tau_c > 0.

No exact delayed EI unless the augmented Markov state is explicitly represented.

## 13. Main dimensionless candidates

Keep minimal:

1. Coupling ratio:
`Pi_gamma = gamma / w_obs`

2. Environment timescale ratio for timing extension:
`Pi_tau = tau_int / tau_env`
using empirical tau_int, not graph diameter as the primary definition.

3. Sensor noise fraction:
`Pi_noise = epsilon / 0.5`

Do not add communication cost/resource Pi groups in v1.1A.

## 14. Rejected blind-review proposals

The following Agent 2 proposals are not adopted into the registered v1.1 core:

- `Psi = Pi_reg * Theta(Pi_CE-1)`:
  rejected because EI must not gate agency-like regulation.

- `Pi_tau = d_net*tau_c/tau_env` as the primary timescale:
  retained only as a structural proxy; empirical response time remains primary.

- Total correlation as evidence of integration:
  diagnostic only; fake coordination can produce it without useful causal integration.

- N=16..128 / KSG in v1.1:
  deferred until a small-N non-degenerate effect exists.

- claimed thermodynamic phase-transition scaling:
  not part of v1.1.

## 15. Decision

Proceed to ToyWorld v1.1A implementation only.

The implementation must be preregistered and committed before any registered scan.

No Stage 1.3 work may begin until v1.1A and, if successful, v1.1B are externally reviewed.
