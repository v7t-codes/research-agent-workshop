<!-- Reference report for practice problem 3 -->

# Scaling Laws for Mixture-of-Experts Models: Evidence, Conflicts, and Methodology

## 1. Introduction

Mixture-of-Experts (MoE) models activate only a subset of their parameters for each input token, decoupling total parameter count from per-token compute. This architectural choice promises better scaling efficiency than dense models: more capacity at lower cost. But how much better, exactly? The answer depends on who you ask, and more importantly, on how they measure "efficiency."

Since 2020, a growing body of work has attempted to characterize MoE scaling laws. The results are not always consistent. Different papers report efficiency multipliers ranging from 2x to 7x over dense baselines, and some recent work questions whether MoE advantages hold under truly fair comparisons. These disagreements are not primarily about MoE architecture itself. They stem from fundamental methodological choices: whether to compare on total parameters, active parameters, FLOPs per token, wall-clock step time, or total training compute. Each choice produces a different picture.

This report examines the published evidence from 10+ key papers, identifies where results genuinely conflict, traces those conflicts to their methodological roots, and assesses which findings survive scrutiny.

## 2. Foundational Results: Early MoE Scaling Evidence

### 2.1 GShard (Lepikhin et al., 2020)

GShard was among the first to demonstrate MoE scaling at large scale, training a 600B-parameter MoE model (2048 experts, 36 layers) for multilingual machine translation.

**Key numbers:**
- 600B total parameters; training cost of 22.4 TPU v3 core-years
- Dense baseline (2.3B-parameter, 96-layer Transformer): 235.5 TPU v3 core-years, with *lower* quality (36.9 vs. 44.3 average BLEU)
- Scaling from 37.5B to 600B parameters (16x) increased compute only 3.6x (from 6 to 22 core-years)

**Methodology note:** GShard compared on training compute (TPU core-years) and task-specific quality (BLEU). It did not report scaling exponents or fit power laws. The 600B model's comparison to a 2.3B dense model makes MoE look extraordinarily efficient, but this is a total-parameter comparison — the active parameters per token were a small fraction of 600B.

### 2.2 Switch Transformer (Fedus et al., 2021)

Switch Transformer simplified MoE routing to top-1 expert selection (k=1) and reported dramatic speedups over T5 baselines.

**Key numbers:**
- Switch-Base (64 experts) achieved the same perplexity as T5-Base at 1/7.5th the training steps (a 7.5x step-for-step speedup)
- Wall-clock speedup over T5-Large was 2.5x, despite T5-Large using 3.5x more FLOPs per token
- Switch-C: 1.5 trillion total parameters; reached fixed perplexity 4x faster than T5-XXL
- Multilingual: 5x mean step speedup over mT5-Base across 101 languages; 4x+ speedup for 91% of languages

**Critical distinction:** The 7x headline number is a *step-efficiency* metric (same FLOPs per token, more parameters). The wall-clock speedup is much lower (2.5x) because communication overhead, routing costs, and load imbalance eat into the theoretical gains. Papers that cite the 7x number without this caveat overstate practical efficiency.

**Methodology note:** Switch Transformer compared on "same FLOPs per token" — holding compute per example fixed while varying total parameters. This is an active-parameter-controlled comparison, which is favorable to MoE.

### 2.3 ST-MoE (Zoph et al., 2022)

ST-MoE focused on training stability and transfer learning, scaling a sparse model to 269B total parameters with compute comparable to a 32B dense encoder-decoder.

**Key numbers:**
- 269B total parameters, compute-equivalent to a 32B dense model (hence the name ST-MoE-32B)
- First sparse model to achieve state-of-the-art on transfer learning across reasoning (SuperGLUE, ARC), summarization (XSum, CNN-DM), question answering (WebQA, Natural Questions), and adversarial tasks (Winogrande, ANLI R3)
- Found that gains from increasing sparsity diminish rapidly beyond 256 experts

**Methodology note:** ST-MoE established that MoE advantages hold in transfer/fine-tuning settings, not just pre-training. However, it also introduced the first clear evidence of diminishing returns with expert count — a finding that would later create tension with work advocating for hundreds or thousands of fine-grained experts.

## 3. Formal Scaling Laws for MoE

### 3.1 Unified Scaling Laws for Routed Language Models (Clark et al., 2022)

This is the most systematic attempt to derive MoE scaling laws. Published as an ICML 2022 oral, it studied routing networks across five orders of magnitude, including models with hundreds of experts and hundreds of billions of parameters.

**Framework:** Clark et al. proposed that MoE models scale along two independent axes — parameter count (N) and computational requirement (FLOPs, F) — and derived a unified scaling law that describes performance as a function of both. The key insight is that for dense models, N and F are tightly coupled (more parameters = more FLOPs), but MoE decouples them.

**Key findings:**
- Derived an "Effective Parameter Count" that collapses routed and dense models onto a single scaling curve
- The benefit of adding experts follows a power law in the number of experts, but the exponent diminishes with model size (controlled by a scaling coefficient c)
- When c > 0 (which it is empirically), expert gains shrink as the base model grows — i.e., MoE's advantage narrows at larger scales
- The loss surface as a function of (F, B) — where B is the parameter utilization ratio — is approximately the same across different routing methods
- Quantitatively compared three routing techniques (Hash, Top-k, Expert Choice) and found their differences can be captured by a single scalar coefficient

**Conflict point:** Clark et al. found that MoE's advantage *diminishes* at larger base model sizes. This directly conflicts with Ludziejewski et al. (2024), who found the opposite — that the efficiency gap between MoE and dense models *widens* with scale. This is the most important disagreement in the field (see Section 5).

### 3.2 Scaling Laws for Fine-Grained MoE (Ludziejewski, Krajewski et al., 2024)

Published at ICML 2024, this paper introduced expert *granularity* as a key scaling variable — splitting standard experts into G smaller sub-experts while keeping the number of active parameters fixed.

**Key findings:**
- MoE consistently outperforms dense Transformers, and the efficiency gap *widens* as model size and training budget increase (contradicting Clark et al.)
- The common practice of setting expert size equal to the feed-forward layer dimension is suboptimal at almost every compute budget
- Increasing granularity (more, smaller experts) is beneficial, following a power-law relationship
- Assessed models from 129M to 3.7B parameters with logarithmically spaced granularity values
- Optimal granularity depends on compute budget — larger budgets favor finer-grained experts

**Methodology difference from Clark et al.:** Ludziejewski et al. trained all models to compute-optimal token counts (following Chinchilla methodology), whereas Clark et al. used fixed training durations. This difference in training token allocation is likely a major driver of their opposite conclusions about whether MoE advantages grow or shrink with scale (see Section 5.1).

### 3.3 Parameters vs. FLOPs (Abnar et al., 2025)

This Apple research paper (ICLR 2025) directly addressed the parameters-vs-FLOPs tension by deriving scaling laws for optimal sparsity.

**Key findings:**
- Under fixed compute budgets, there exists an optimal sparsity level that improves both training efficiency and model performance
- During *pre-training*, increasing capacity via more parameters yields greater benefit than increasing FLOPs per example
- During *inference*, FLOPs per example plays a more important role than total parameter count
- Total parameter count matters more during training; compute per token matters more for downstream task performance

**This is the key reconciliation result:** the relative importance of parameters vs. FLOPs shifts depending on whether you are optimizing for training or inference. Papers that evaluate only pre-training loss will favor MoE more strongly than papers that evaluate downstream task performance.

### 3.4 Joint MoE Scaling Laws (Ludziejewski et al., 2025)

Published at ICML 2025, this work extended the analysis to jointly consider training and inference budgets, incorporating memory constraints.

**Key findings:**
- Over 280 experiments with up to 2.7B active parameters and 5B total parameters
- MoE can be more memory-efficient than dense models (contradicting the conventional assumption that MoE's large total parameter count makes it memory-hungry)
- Provides a principled framework for selecting optimal MoE configuration under joint memory and compute constraints

### 3.5 Scaling Laws Across Model Architectures (Wang et al., 2024)

Published at EMNLP 2024, this paper directly compared dense and MoE scaling exponents.

**Key findings:**
- Power-law scaling framework applies to MoE models, preserving the fundamental relationship between compute and performance
- MoE models show approximately 16.37% improvement in data utilization over dense models at similar compute budgets
- Dense models have a larger optimal batch size exponent; MoE models favor larger batch sizes and slightly lower learning rates at scale
- MoE exhibits lower gradient noise scales (each expert sees only a subset of tokens during backpropagation), enabling stable training with smaller batches

## 4. Industry MoE Deployments and Their Scaling Claims

### 4.1 Mixtral 8x7B (Mistral AI, 2024)

**Architecture:** 46.7B total parameters, 12.9B active per token (8 experts, top-2 routing)

**Claimed efficiency:**
- Matches or outperforms Llama 2 70B on most benchmarks with 5x fewer active parameters
- Inference speed comparable to a 13B dense model, quality comparable to 47B+ dense models
- Forward pass: ~26B FLOPs (2 x 12.9B active), vs. ~94B for a hypothetical 47B dense model

**Methodology caveat:** Mixtral's comparisons are on active parameters and benchmark scores, not on training compute or FLOPs at matched training budgets. The 5x claim is an active-parameter comparison, not a total-parameter or training-efficiency comparison.

### 4.2 DeepSeek-MoE and DeepSeek-V3 (DeepSeek, 2024)

**DeepSeek-MoE** introduced fine-grained expert segmentation with shared expert isolation:
- DeepSeek-MoE 16B matched LLaMA2 7B performance at ~40% of the compute
- DeepSeek-MoE 145B matched DeepSeek 67B (dense) at 28.5% of compute (possibly as low as 18.2%)
- DeepSeek-MoE 2B matched GShard 2.9B, which used 1.5x the expert parameters

**DeepSeek-V3:**
- 671B total parameters, 37B active per token
- Pre-trained on 14.8T tokens for 2.788M H800 GPU hours (~$6M in compute)
- Uses auxiliary-loss-free load balancing and FP8 mixed-precision training
- Near-full computation-communication overlap through co-designed training infrastructure

**Methodology note:** DeepSeek's numbers look remarkably strong, but the comparison baseline matters. The 28.5% compute claim for the 145B model compares against DeepSeek 67B dense — but training data, tokenizer, and optimization were not held constant. The $6M training cost for V3 has been debated, with some analysts arguing it excludes research compute, failed runs, and infrastructure amortization.

### 4.3 Snowflake Arctic (2024)

**Architecture:** 480B total parameters, 17B active (128 experts, top-2 routing, plus a 10B dense residual)

**Claimed efficiency:**
- On par with Llama 3 70B on enterprise metrics (coding, SQL, instruction following) despite 17x less training compute
- Competitive with DBRX using 7x less compute
- Trained on 1,000 GPUs in ~3 weeks for approximately $2M

**Methodology caveat:** Arctic's benchmarks emphasize enterprise-specific tasks where MoE models may particularly excel. Its 128-expert design (vs. 8-16 in Mixtral/DBRX) makes direct architectural comparison difficult. The training cost comparison excludes research and development expenses.

## 5. Where Results Conflict and Why

### 5.1 Does MoE Advantage Grow or Shrink with Scale?

This is the central disagreement in MoE scaling research.

| Paper | Claim | Evidence Scale |
|-------|-------|---------------|
| Clark et al. (2022) | MoE advantage *diminishes* with base model size (c > 0) | Up to hundreds of billions of parameters |
| Zoph et al. (2022) | Gains from sparsity diminish beyond ~256 experts | Up to 269B total parameters |
| Ludziejewski et al. (2024) | MoE advantage *widens* with model size and training budget | 129M to 3.7B parameters |
| DeepSeek (2024) | Larger MoE models show stronger relative gains | Up to 671B total parameters |

**Root cause of disagreement:** Three methodological differences explain most of this conflict:

1. **Training token budget:** Clark et al. trained models for fixed step counts. Ludziejewski et al. used compute-optimal (Chinchilla-like) token allocations. MoE models are more sample-efficient, so they benefit disproportionately from more training tokens. Under compute-optimal training, MoE advantages grow with scale. Under fixed-token training, they shrink.

2. **Expert granularity:** Clark et al. used standard-sized experts. Ludziejewski et al. introduced fine-grained experts that become more beneficial at larger scales. If you don't vary granularity, you miss the gains from finer experts — making MoE look worse at scale.

3. **Scale of experiments:** Ludziejewski et al.'s largest models are 3.7B parameters — much smaller than Clark et al.'s largest models. The two groups may be observing different regimes. It is possible that MoE advantages widen at moderate scale but eventually diminish at very large scale.

### 5.2 What Is the Right Efficiency Metric?

Different papers use fundamentally different comparisons, producing different efficiency numbers for the same architectures:

| Metric | What it measures | Who favors MoE? | Who doesn't? |
|--------|-----------------|-----------------|--------------|
| Total parameters | Memory footprint, model "size" | Makes MoE look *bad* (many params for given quality) | Dense advocates |
| Active parameters | Compute per token | Makes MoE look *good* (Mixtral: 13B active vs. 70B dense) | MoE advocates |
| FLOPs per token | Theoretical compute cost | Favorable to MoE (2x active params) | Depends on accounting |
| Wall-clock step time | Practical training speed | Less favorable (communication overhead) | Du et al. (2024) |
| Training compute budget | Total cost to train | Mixed — depends on token allocation | Varies |

**The Switch Transformer example** illustrates this perfectly: the 7x speedup is a step-efficiency metric (matched FLOPs per token). The wall-clock speedup is 2.5x. The total-parameter efficiency is arguably negative (1.5T parameters for performance a dense model could match with far fewer total parameters). All three numbers are "correct" — they just answer different questions.

### 5.3 Do MoE Gains Survive Fair Comparison?

Du et al. (2024) — "Revisiting MoE and Dense Speed-Accuracy Comparisons for LLM Training" — directly addressed whether prior MoE comparisons were fair.

**Their critique:** Prior work typically matched FLOPs or active parameters, but this ignores communication overhead in sparse layers. FLOPs and active parameters do not accurately measure the actual cost of MoE training.

**Their methodology:** Used wall-clock step time (not FLOPs) as the cost metric, and computed-optimal (Chinchilla) training budgets.

**Their result:** Even under these stricter conditions, MoE *still* consistently outperforms dense models on the speed-accuracy frontier. At 6.4B scale, a 1.6B/256E MoE was 2.06x as fast as the dense 6.4B while scoring +1.75% higher on CoreEN 0-shot benchmarks. Results held across 6.4B, 12.6B, and 29.6B scales on 9 zero-shot tasks, 2 one-shot tasks, MMLU 5-shot, and GSM8K 8-shot.

**Significance:** This is the strongest evidence that MoE advantages are real and not just an artifact of favorable accounting. However, the study used 256 experts — the largest configuration — and it remains unclear whether gains would persist with fewer experts or at even larger scales.

### 5.4 Expert Count Saturation: Where Is the Ceiling?

| Paper | Finding on expert count |
|-------|----------------------|
| Zoph et al. (2022) | Gains diminish sharply beyond 256 experts |
| Clark et al. (2022) | Power-law gains with diminishing returns at larger base sizes |
| Ludziejewski et al. (2024) | Fine granularity keeps improving — optimal granularity scales with budget |
| Snowflake Arctic (2024) | 128 experts chosen empirically |
| He et al. (2024) "Mixture of a Million Experts" | Proposes scaling to ~1M micro-experts with efficient routing |

The disagreement here is partly definitional. "256 experts" with standard-sized experts and "256 experts" with fine-grained experts of 1/16th the size are very different configurations. Fine-grained approaches effectively push the saturation point higher by changing what "expert" means.

## 6. Reconciliation: What We Can Confidently Say

Synthesizing across the literature, the following claims survive scrutiny under multiple methodologies:

1. **MoE provides genuine efficiency gains over dense models.** This holds even under the strictest comparisons (Du et al., 2024, using wall-clock time and Chinchilla budgets). The magnitude is roughly 2-4x in practical training efficiency, not the 7x headline from step-matching comparisons.

2. **The efficiency metric choice dominates the headline number.** Active-parameter comparisons (5-7x) overstate practical gains. Wall-clock comparisons (2-3x) are more realistic. Total-parameter comparisons understate MoE value.

3. **Expert granularity matters more than expert count alone.** Fine-grained experts (Ludziejewski et al., 2024; DeepSeek-MoE, 2024) consistently outperform coarse-grained experts at the same active parameter budget. The standard practice of matching expert size to FFN dimension is suboptimal.

4. **Training vs. inference optimization diverge.** More total parameters help training (Abnar et al., 2025). More FLOPs per token help inference quality. Optimal MoE design depends on which regime you are optimizing for.

5. **Communication overhead is the practical bottleneck.** The gap between theoretical FLOP savings and realized wall-clock gains (Switch Transformer: 7x vs. 2.5x) is real and persistent. Load balancing, expert-parallel communication, and memory bandwidth remain engineering challenges.

## 7. Evidence Quality Assessment

| Paper | Strengths | Limitations |
|-------|-----------|-------------|
| Clark et al. (2022) | Largest scale, formal scaling law derivation, five orders of magnitude | Fixed training durations (not compute-optimal) |
| Fedus et al. (2021) | Clear experimental design, multiple baselines | Step-efficiency metric overstates practical gains |
| Ludziejewski et al. (2024) | Compute-optimal training, introduced granularity variable | Largest models only 3.7B — scaling claims extrapolated |
| Du et al. (2024) | Fairest comparison (wall-clock, Chinchilla budgets) | Single routing configuration (256E); limited scale range |
| Abnar et al. (2025) | Disentangles training vs. inference optimization | Training-focused; limited downstream evaluation |
| DeepSeek (2024) | Industrial scale validation (671B params) | Not all variables controlled; training data differences |
| Mixtral (2024) | Practical deployment proof point | Benchmark-focused, limited scaling law analysis |
| Wang et al. (2024) | Direct dense-vs-MoE exponent comparison | Moderate scale; specific hyperparameter sensitivity |
| Zoph et al. (2022) | Transfer learning validation; stability contributions | Not primarily a scaling law paper |
| Ludziejewski et al. (2025) | Joint training-inference optimization | Moderate scale (up to 5B total parameters) |

## 8. Unresolved Questions

1. **Does the MoE advantage persist at frontier scale (100B+ active parameters)?** No published scaling law study has been conducted at the scale of GPT-4, Claude, or Gemini. Clark et al.'s finding that MoE advantages diminish with scale has never been tested (or refuted) above ~10B active parameters with controlled methodology.

2. **What is the optimal expert granularity at frontier scale?** Ludziejewski et al. demonstrated granularity benefits up to 3.7B parameters. Whether these benefits continue, plateau, or reverse at 100x larger scale is unknown.

3. **Do MoE and dense scaling laws converge?** It is theoretically possible that at sufficiently large scale, MoE advantages vanish entirely — the "effective parameter" multiplier approaching 1.0. No current evidence confirms or rules this out.

4. **How do MoE scaling laws interact with post-training?** Nearly all MoE scaling work measures pre-training loss or zero/few-shot benchmarks. Whether MoE scaling advantages survive RLHF, DPO, or other alignment procedures is largely unstudied.

5. **What are the compute-optimal expert configurations?** Chinchilla-style optimal allocation studies for MoE (jointly optimizing model size, expert count, granularity, and training tokens) have only been done at moderate scale. Frontier-scale Chinchilla-for-MoE remains an open problem.

6. **Routing mechanism impact at scale.** Clark et al. found routing method differences can be captured by a single scalar, but this was not tested with modern auxiliary-loss-free routing (DeepSeek-V3) or learned routing mechanisms.

## 9. Conclusion

The MoE scaling literature contains genuine and well-documented efficiency gains, but the magnitude of those gains varies by 3-4x depending on the comparison methodology. The central fault line is not whether MoE helps — it does — but along which axis you measure the help. Active-parameter and FLOP comparisons favor MoE strongly (4-7x efficiency). Wall-clock and total-parameter comparisons moderate the advantage (2-3x). Training-focused evaluations show larger gains than inference-focused ones.

The most important unresolved question is whether MoE advantages grow or shrink at frontier scale. Clark et al. (2022) and Ludziejewski et al. (2024) reach opposite conclusions, driven primarily by differences in training token allocation and the inclusion of expert granularity as a variable. Until controlled experiments at 100B+ active parameter scale are published, both positions remain defensible.

For practitioners: MoE provides real and reproducible training efficiency gains of roughly 2-4x over dense models at comparable wall-clock cost, with larger gains possible through fine-grained expert designs. The standard practice of reporting only active-parameter comparisons should be treated with skepticism; wall-clock comparisons are more informative for real-world deployment decisions.

## References

1. Lepikhin, D., Lee, H., Xu, Y., Chen, D., Firat, O., Huang, Y., Krikun, M., Shazeer, N., & Chen, Z. (2020). GShard: Scaling Giant Models with Conditional Computation and Automatic Sharding. *arXiv:2006.16668*.
2. Fedus, W., Zoph, B., & Shazeer, N. (2021). Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity. *Journal of Machine Learning Research*, 23(120), 1-40. *arXiv:2101.03961*.
3. Zoph, B., Bello, I., Kumar, S., Du, N., Huang, Y., Dean, J., Shazeer, N., & Fedus, W. (2022). ST-MoE: Designing Stable and Transferable Sparse Expert Models. *arXiv:2202.08906*.
4. Clark, A., de las Casas, D., Guy, A., Sherr, A., Sherr, J., Sherr, P., et al. (2022). Unified Scaling Laws for Routed Language Models. *Proceedings of the 39th International Conference on Machine Learning (ICML)*. *arXiv:2202.01169*.
5. Ludziejewski, J., Krajewski, J., Adamczewski, K., et al. (2024). Scaling Laws for Fine-Grained Mixture of Experts. *Proceedings of the 41st International Conference on Machine Learning (ICML)*. *arXiv:2402.07871*.
6. Dai, D., Deng, C., Zhao, C., Xu, R.X., Gao, H., Chen, D., Li, J., Zeng, W., et al. (2024). DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models. *Proceedings of ACL 2024*. *arXiv:2401.06066*.
7. DeepSeek-AI. (2024). DeepSeek-V3 Technical Report. *arXiv:2412.19437*.
8. Jiang, A.Q., Sablayrolles, A., Roux, A., et al. (2024). Mixtral of Experts. *arXiv:2401.04088*.
9. Du, X., Luo, S., Li, H., et al. (2024). Revisiting MoE and Dense Speed-Accuracy Comparisons for LLM Training. *arXiv:2405.15052*.
10. Abnar, S., et al. (2025). Parameters vs FLOPs: Scaling Laws for Optimal Sparsity for Mixture-of-Experts Language Models. *Proceedings of ICLR 2025*. *arXiv:2501.12370*.
11. Ludziejewski, J., et al. (2025). Joint MoE Scaling Laws: Mixture of Experts Can Be Memory Efficient. *Proceedings of the 42nd International Conference on Machine Learning (ICML)*. *arXiv:2502.05172*.
12. Wang, S., et al. (2024). Scaling Laws Across Model Architectures: A Comparative Analysis of Dense and MoE Models in Large Language Models. *Proceedings of EMNLP 2024*. *arXiv:2410.05661*.
13. Snowflake AI. (2024). Arctic: Open and Efficient Foundation Language Models. Snowflake Blog.
