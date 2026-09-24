# EXPERIMENT_SPEC_ToyWorld_v1.1A_CANDIDATE_FREEZE

Status: CANDIDATE FREEZE FOR IMPLEMENTATION
Stage: 1.2
Experiment: ToyWorld v1.1A — Non-degenerate Distributed Regulation Exact Core

## 1. Scientific objective

Test whether a minimal finite network can show genuinely communication-dependent, task-directed distributed regulation in a world where task-relevant information is split across local nodes.

The experiment does NOT test:
- consciousness;
- subjective experience;
- universal intelligence;
- thermodynamic phase transitions;
- human/organizational/civilizational agency.

## 2. Primary hypothesis

In World A, there exists a non-zero communication coupling range in which inter-node messages causally improve task regulation relative to message-blocked/no-communication controls.

Operationally, at least:
- J must improve;
- CCG must be > 0;
- CDC_trajectory must improve.

This same pattern must NOT appear in the integration-useless World B.

## 3. Exact-core architecture

### Hidden disturbance
H_t = (h1_t,h2_t), hj ∈ {-1,+1}.

Each hj flips independently with probability p_flip per tick.

### Controlled state
X_t = (x1_t,x2_t).

Each coordinate belongs to a bounded half-step grid:
{-K, -K+0.5, ..., K-0.5, K}.

Primary K = 2.

Target X*=(0,0).

### Coupled disturbance
G(c) = [[1,c],[c,1]]/(1+c), c ∈ {0,1}.

d_t = G(c) H_t.

World A uses c=1.
World B uses c=0.

### Environment transition
X_{t+1} = clip_grid(X_t + d_t - U_t).

### Nodes
N=4.

Ring:
0—1—2—3—0.

Sensor classes:
- nodes 0,2 observe h1;
- nodes 1,3 observe h2.

Observation noise:
P(y_i = true hidden component) = 1-epsilon.

### Node state
z_i ∈ {-1,0,+1}.

### Node update
q_i = y_i + gamma * mean(neighbor z from previous tick).

For a ∈ {-1,0,+1}:

P(z_i(t)=a | q_i)
=
exp(beta*a*q_i - lambda_action*a^2) / Z(q_i).

No adaptive weights.

### Distributed action
u1 = (z0+z2)/2
u2 = (z1+z3)/2.

No central readout.

## 4. Primary fixed parameters

Must be frozen by implementation-validation commit before registered scan:
- K
- beta
- lambda_action
- epsilon
- p_flip World A
- p_flip World B/D
- initial-state distribution
- burn-in
- trajectory length
- seed list
- intervention distributions
- gamma grid

A pilot may be used only to reject degenerate parameterizations.
Pilot results must be stored separately and must not be merged with registered results.

## 5. Primary scan

N=4 only.

tau_c=0 registered exact core.

Primary gamma ratio:
Pi_gamma = gamma / w_obs = gamma because w_obs=1.

Recommended pre-freeze candidate grid:
gamma ∈ {0,0.25,0.5,0.75,1.0,1.5,2.0}.

The exact final grid must be frozen before registered results.

## 6. Worlds

### World A — Positive
c=1.
Moderate p_flip.
Distributed information should be useful.

### World B — Integration useless
c=0.
Same network, sensors and actuator mapping.
Cross-class information is not required for optimal local control.

### World C — Adversarial
Deferred from registered exact core if tau_c>0 is needed.
A zero-delay fast-environment variant may be exploratory only.
The registered delayed World C belongs to v1.1C.

### World D — Fake coordination
Task-relevant communication disabled.
Inject a shared common-mode stochastic/periodic driver into node logits independent of H.
The driver distribution and amplitude must be frozen.

Expected:
high synchrony/total correlation is possible without positive CCG or J improvement.

## 7. Primary metrics

### J
L = (x1^2+x2^2)/(2K^2).
J=-E[L].

### CDC_uniform
Contextual Directed Control using a frozen uniform evaluation distribution over exact contexts.

### CDC_trajectory
Contextual Directed Control weighted by the actual registered trajectory distribution.

### CCG
Paired causal communication gain:

CCG_block =
J_intact - J_message_blocked.

Also compute:
CCG_shuffle =
J_intact - J_message_shuffled.

All paired comparisons use common random numbers.

### Resilience
Raw J/L under preregistered node lesions.
Normalized scores are secondary.

## 8. Secondary diagnostics

- I_sense;
- total correlation/synchrony;
- environment action-channel capacity, once per world.

EI/causal emergence is NOT a required v1.1A metric.

If implemented, it is exploratory and may not alter the primary verdict.

## 9. Mandatory validation before registered scan

1. No algebraic feedthrough:
   demonstrate reachable states where changing a neighbor message changes P(z_i next).

2. No deterministic absorbing lock over the registered gamma range:
   demonstrate non-zero transition probability away from unanimous states under at least one ordinary observation context.

3. At gamma=0:
   message blocking produces exactly zero CCG by construction.

4. World B:
   message communication does not produce a preregistered positive-control-like benefit.

5. Fake coordination:
   a common driver can increase synchrony without forcing CCG positive.

6. CDC:
   exact tiny cases:
   - optimal contextual policy > 0;
   - random reference ≈0;
   - anti-policy <0.

7. Independent RNG substreams / common random numbers:
   paired intact-vs-ablation runs share environment/sensor randomness.

8. Probability normalization and reproducibility tests.

## 10. Primary decision rule

ToyWorld v1.1A passes the non-degeneracy gate if all are true:

A. In World A, at least one non-zero preregistered gamma has:
- J_intact > J_gamma0 by preregistered statistical tolerance;
- CCG_block > 0 with uncertainty excluding zero;
- CDC_trajectory > gamma0 baseline.

B. World B does NOT show the same three-way improvement.

C. World D may show synchrony but does NOT show positive task-directed CCG comparable to World A.

D. Results are robust across the preregistered seed set.

Passing Gate A means:
“evidence for communication-dependent distributed regulation in ToyWorld v1.1A.”

It does NOT mean:
“macroagent proven” or “universal law found”.

## 11. Failure categories

F1 — no communication effect:
CCG≈0 everywhere in World A.

F2 — communication universally helps:
World B improves similarly; design confounded.

F3 — synchrony false positive:
World D satisfies the primary World-A-like criteria.

F4 — only J improves:
CDC/CCG fail; task effect is not shown to be causally due to distributed communication.

F5 — only metrics improve:
J does not; informational structure is task-irrelevant.

F6 — absorbing consensus:
network freezes and apparent regulation is an attractor artifact.

F7 — parameter fragility:
result exists only at one isolated hand-picked parameter point.

## 12. Vocabulary

Allowed:
- non-degenerate distributed-regulation effect;
- communication gain;
- control threshold;
- smooth crossover;
- bifurcation-like regime change, if demonstrated.

Forbidden for v1.1A:
- true thermodynamic phase transition;
- emergence of consciousness;
- universal agent law;
- proof of macroagency.
