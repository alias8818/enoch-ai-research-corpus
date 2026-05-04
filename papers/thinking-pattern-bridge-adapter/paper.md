# Thinking-Pattern Bridge Adapter: Recovering Failed Cross-Family On-Policy Distillation via Mode-Conditioned Prompt and Latent Adapters

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, benchmark logs, and experiment scripts). The operator who released this artifact claims no personal authorship credit for the writing or the results. Readers should treat this document as an unreviewed AI-generated research artifact. No human reviewer has endorsed its claims.

---

## Abstract

On-policy distillation (OPD) of large language models can fail when teacher and student exhibit incompatible thinking patterns, even when the student has sufficient capacity. We investigate whether small bridge adapters—operating either in prompt space or latent space—can recover failed cross-family OPD by mapping student rollouts into teacher-compatible reasoning modes before distillation proceeds. In a controlled synthetic OPD analogue where a teacher reasons in a canonical basis and a cross-family student exposes mode-mixed representations, plain cross-family OPD collapses (accuracy 0.383, log loss 1.629). A prompt bridge that predicts the active mode from rollout diagnostics and injects mode-tagged prompt features restores accuracy to 0.970 (97.2% gap recovery). A latent bridge that learns a mode-conditioned linear inverse to recover the teacher's hidden basis restores accuracy to 0.987 (99.97% gap recovery), with teacher top-3 probability mass overlap rising from 0.741 to 0.996. These results are from a synthetic feasibility test only; they do not demonstrate transfer in real language models. We report the experiment, its limitations, and the conditions under which a real-model pilot would be warranted.

## 1. Introduction

On-policy distillation (OPD) is a mechanism by which a student language model learns from rollouts generated under its own policy, with the teacher providing supervision at those student-chosen tokens. Recent work has shown that OPD success depends critically on compatible thinking patterns between teacher and student: when the teacher and student concentrate probability mass on different token sets, progressive alignment fails and distillation collapses, regardless of student capacity. The OPD phenomenology study (arXiv:2604.13016) reports that in successful OPD, a small shared token set carries 97–99% of probability mass, and proposes off-policy cold start combined with teacher-aligned prompt selection as a recovery strategy for failing pairs.

This work tests a stricter extension of that idea: rather than merely selecting better prompts or warming up off-policy, can we build explicit bridge adapters that re-map student reasoning modes into the teacher's representational basis before OPD begins? We consider two adapter designs:

1. **Prompt bridge**: Predict the active thinking mode from cheap rollout diagnostics and inject mode-tagged features into the prompt, allowing the teacher to condition on the student's mode during distillation.
2. **Latent bridge**: Learn a small mode-conditioned linear inverse that maps student rollout hidden states back into the teacher's canonical basis, then run OPD in the recovered representation.

We evaluate these adapters in a controlled synthetic OPD analogue—not in real language models—to determine whether the mechanism is coherent and whether the adapter interface can plausibly close the gap between failed and successful distillation.

## 2. Method

### 2.1 Synthetic OPD Analogue

We construct a controlled environment that isolates the thinking-pattern compatibility mechanism:

- A **teacher policy** is defined as accurate in a canonical reasoning basis $\mathbf{u}$.
- A **cross-family student** produces rollouts exposing $\mathbf{s} = T_m \mathbf{u}$, where $m$ indexes a latent thinking pattern (mode) and $T_m$ is a mode-dependent linear transformation.
- **Plain cross-family OPD** receives only the mixed-basis student rollouts $\mathbf{s}$ and must align to the teacher in basis $\mathbf{u}$. Because incompatible modes collide in the mixed representation, plain OPD is expected to fail.

This design deliberately abstracts away the complexity of real language model internals while preserving the core failure mode: representational mismatch between teacher and student thinking patterns.

### 2.2 Prompt Bridge Adapter

The prompt bridge operates in prompt/feature space:

1. From a student rollout, extract cheap diagnostic features (e.g., activation statistics, trajectory shape indicators).
2. Predict the active mode $m$ from these diagnostics using a lightweight classifier.
3. Inject mode-tagged prompt features so that the distillation process can condition on the student's current reasoning mode.

The prompt bridge does not modify hidden states; it provides the distillation procedure with information about which mode the student is operating in.

### 2.3 Latent Bridge Adapter

The latent bridge operates in representation space:

1. Collect paired (student rollout state, teacher hidden state) examples across modes.
2. Learn a mode-conditioned linear inverse $W_m$ such that $\hat{\mathbf{u}} = W_m \mathbf{s}$ recovers the teacher's canonical basis from the student's mode-mixed representation.
3. Run OPD using the recovered representation $\hat{\mathbf{u}}$ rather than the raw student rollout $\mathbf{s}$.

The latent bridge directly addresses the representational mismatch by inverting the mode-specific transformation.

### 2.4 Experimental Protocol

All experiments use the script `scripts/bridge_adapter_experiment.py` with the following configuration:

- **Training set**: 12,000 examples per seed
- **Test set**: 4,000 examples per seed
- **Seeds**: 10 (all reported metrics are means over seeds)
- **Smoke test**: 300 train / 150 test, 2 seeds (completed first to verify no memory or throughput blockers)
- **Hardware**: Linux aarch64 host with NVIDIA GB10 present; GPU not used (NumPy/sklearn experiment); swap disabled; peak RSS 237,848 KiB against ~121 GiB available memory
- **Wall time**: Full calibrated run completed in approximately 3.96 seconds

Four conditions are compared:

1. **Same-family OPD ceiling**: Teacher and student share the same reasoning basis (upper bound).
2. **Plain cross-family OPD**: Student rollouts in mixed basis with no adapter (expected failure).
3. **Prompt bridge OPD**: Cross-family with prompt bridge adapter.
4. **Latent bridge OPD**: Cross-family with latent bridge adapter.

## 3. Results

### 3.1 Main Metrics

Mean results over 10 seeds (12k train / 4k test per seed):

| Condition | Accuracy | Log Loss | Teacher Top-3 Mass Overlap |
|---|---:|---:|---:|
| Same-family OPD ceiling | 0.9871 | 0.0804 | — |
| Plain cross-family OPD | 0.3834 | 1.6287 | 0.7412 |
| Prompt bridge OPD | 0.9703 | 0.1243 | 0.9963 |
| Latent bridge OPD | 0.9870 | 0.0828 | 0.9964 |

### 3.2 Gap Recovery

The accuracy gap between plain cross-family OPD (0.3834) and the same-family ceiling (0.9871) is 0.6037. Bridge adapters recover most of this gap:

- **Prompt bridge**: recovers 97.2% of the gap (accuracy 0.9703).
- **Latent bridge**: recovers 99.97% of the gap (accuracy 0.9870).

### 3.3 Probability Mass Alignment

The teacher top-3 probability mass overlap—a mechanistic indicator emphasized in the OPD literature as critical for progressive alignment—improves dramatically:

- Plain cross-family: 0.7412 overlap.
- Prompt bridge: 0.9963 overlap.
- Latent bridge: 0.9964 overlap.

This shift from ~0.74 to ~0.996 mass overlap is the strongest mechanistic evidence in this experiment: it demonstrates that the bridge adapters restore the high-probability token alignment that the OPD literature identifies as necessary for successful distillation.

### 3.4 Resource Profile

The experiment was computationally lightweight: peak RSS of 237,848 KiB, wall time under 4 seconds, zero swap activity, no GPU utilization. This is expected for a NumPy/sklearn synthetic experiment and does not characterize the cost of bridge adapters in real model settings.

## 4. Limitations

This section is critical: the results above do **not** constitute a publishable scientific result for real language model distillation. The limitations are substantial and structural.

### 4.1 Synthetic Environment Only

The experiment operates in a controlled linear analogue where the teacher basis, student transformation, and mode structure are known and well-conditioned. Real language models have nonlinear, high-dimensional, and poorly characterized internal representations. The mode-conditioned linear inverse that works here may not be learnable or even well-defined for real transformer hidden states.

### 4.2 No Real LLM Validation

No real teacher–student language model pairs were tested. The experiment does not demonstrate that:

- Real cross-family OPD failures are caused by the same representational mismatch mechanism.
- Mode diagnostics can be extracted cheaply from real model rollouts.
- A linear or low-rank latent bridge can invert real model representational differences.
- Bridge adapters survive long-horizon reasoning tasks (math, code, multi-step inference) where error accumulation may dominate.

### 4.3 Optimistic Mode Structure

The synthetic experiment assumes a discrete, identifiable mode variable $m$ with a known number of modes. Real thinking patterns may be continuous, overlapping, or unidentifiable from rollout diagnostics alone.

### 4.4 No Comparison to Existing Recovery Strategies

The experiment does not compare bridge adapters against the cold-start and prompt-selection recovery strategies proposed in the OPD literature. It is possible that simpler interventions achieve comparable recovery in practice.

### 4.5 Generalization Unknown

The synthetic experiment uses i.i.d. train/test splits. Whether bridge adapters generalize across distribution shift, task families, or student capacity regimes is untested.

## 5. Reproducibility Checklist

- **Code**: `scripts/bridge_adapter_experiment.py` (included in project artifacts).
- **Full metrics**: `artifacts/metrics/bridge_adapter_metrics.json` (10-seed calibrated run).
- **Key findings summary**: `artifacts/metrics/key_findings.json`.
- **Smoke test metrics**: `artifacts/metrics/smoke_bridge_adapter_metrics.json`.
- **Full run stdout**: `artifacts/logs/bridge_adapter_full.stdout.log`.
- **Full run stderr (includes `/usr/bin/time -v` output)**: `artifacts/logs/bridge_adapter_full.stderr.log`.
- **Smoke test log**: `artifacts/logs/smoke_bridge_adapter.log`.
- **Environment probe**: `artifacts/logs/environment_probe.log`.
- **Run notes**: `run_notes.md`.
- **Decision record**: `.omx/project_decision.json`.
- **Hardware**: Linux aarch64, NVIDIA GB10 present (GPU unused), ~121 GiB RAM, swap disabled.
- **Software**: Python 3, NumPy, scikit-learn (versions recorded in environment probe log).
- **Random seeds**: 10 seeds for the full run; 2 seeds for smoke test. Seed values and per-seed variance are available in the full metrics JSON.
- **Wall time**: ~3.96 seconds for the full calibrated run.
- **Peak RSS**: 237,848 KiB.

## 6. Conclusion

In a controlled synthetic OPD analogue, bridge adapters that map student rollouts into teacher-compatible reasoning modes recover nearly all of the accuracy lost when cross-family OPD fails. The prompt bridge recovers 97.2% of the gap; the latent bridge recovers 99.97%. Teacher top-3 probability mass overlap rises from 0.74 (failed plain OPD) to 0.996 (both bridges), consistent with the mechanistic account in the OPD literature that high-probability token alignment is necessary for progressive distillation.

However, these results are from a synthetic feasibility test with known, well-conditioned linear structure. They do not demonstrate transfer in real language models, and the gap between this controlled setting and real transformer distillation is large. The appropriate interpretation is: the bridge-adapter mechanism is coherent and viable under controlled conditions, warranting—but not substituting for—a real-model pilot.

The next stage requires at least two cross-family teacher/student pairs where vanilla OPD fails, same-family OPD ceilings for each task family, prompt-bridge and latent-bridge comparisons on real model logits and rollouts, and evaluation on long-horizon reasoning tasks. Until such evidence is collected, the bridge-adapter hypothesis remains a promising but unvalidated mechanism.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Experiment script | `scripts/bridge_adapter_experiment.py` |
| Full calibrated metrics (10 seeds) | `artifacts/metrics/bridge_adapter_metrics.json` |
| Key findings summary | `artifacts/metrics/key_findings.json` |
| Smoke test metrics | `artifacts/metrics/smoke_bridge_adapter_metrics.json` |
| Full run stdout | `artifacts/logs/bridge_adapter_full.stdout.log` |
| Full run stderr (with `/usr/bin/time -v`) | `artifacts/logs/bridge_adapter_full.stderr.log` |
| Smoke test log | `artifacts/logs/smoke_bridge_adapter.log` |
| Environment probe log | `artifacts/logs/environment_probe.log` |
| Run notes | `run_notes.md` |
| Project decision JSON | `.omx/project_decision.json` |
| Project metadata | `.omx/project.json` |
| Notion source page | `https://www.notion.so/Thinking-Pattern-Bridge-Adapter-source-record-redacted` |
| External literature anchor | arXiv:2604.13016, *Rethinking On-Policy Distillation of Large Language Models: Phenomenology, Mechanism, and Recipe* |
