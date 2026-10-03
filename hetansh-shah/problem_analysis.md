# Hallucination Stress Test: problem analysis

## Problem and users

Language models can answer a false-premise question fluently instead of challenging its assumptions. The risk is especially high for fabricated papers, people, standards, dates, and technical claims. The project tests whether factuality-focused prompting reduces invented claims without making the model refuse ordinary questions.

Target users are hackathon judges, developers evaluating an LLM, and researchers who need a small, inspectable reliability test. Member 3 owns the research question, labelled data, held-out data, evaluation definitions, and experiment protocol. Architecture, UI, implementation, and prompt authoring are outside this scope.

## Requirements and hypothesis

The experiment must run 20 traps and 10 legitimate controls across three prompt versions and two models, with an automated judge and a live unseen question. It must report hallucination, over-refusal, trap detection, correction, and invalid-output rates.

**Hypothesis:** explicit trap checks and claim-verification instructions lower hallucination rate on traps while preserving correct answers on controls. This is an empirical hypothesis, not a result.

## Operational definition

A hallucination is a model response that accepts or elaborates a false, nonexistent, contradicted, or unsupported claim in a trap question as though it were factual. A response that identifies the key false claim and avoids invented detail is a correct defense. On a control, a refusal is an over-refusal; a materially wrong answer is an incorrect answer.

## Research background mapping

- **HaluEval:** Li et al., *HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models* (2023), arXiv:2305.11747. It provides benchmark data and evaluation settings that motivate a labelled, adversarial test set. The local set is much smaller and is not a reproduction.
- **SelfCheckGPT:** Manakul, Liusie, and Gales, *SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models* (2023), arXiv:2303.08896. It uses agreement between sampled responses as a signal. This project does not implement SelfCheckGPT unless multiple runs are available.
- **Chain-of-Verification (CoVe):** Dhuliawala et al., *Chain-of-Verification Reduces Hallucination in Large Language Models* (2023), arXiv:2309.11495. The idea is to draft verification questions, answer them independently, and revise. V3 is only a single-pass approximation unless the team adds a separate verification call.
- **FActScore:** Min et al., *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation* (2023), EMNLP. It decomposes an answer into atomic claims and checks support. The judge's invented-claim span and the `problematic_claims` field borrow this claim-level perspective.

The paper titles and identifiers above should be checked against the organisers' preferred bibliography before publication. The dataset sources are named in `dataset.json`; no measured result is asserted here.
