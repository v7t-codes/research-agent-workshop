<!-- Reference report for practice problem 1 -->

# Neural Architecture Search: Weight-Sharing, Evolutionary, and Differentiable Approaches

## 1. Introduction

Neural Architecture Search (NAS) automates the design of neural network architectures, replacing human intuition with algorithmic exploration of a structured search space. The field was catalyzed by Zoph and Le (2017), who used reinforcement learning to discover competitive architectures on CIFAR-10 and Penn Treebank -- but at a cost of 22,400 GPU-hours (800 GPUs for 28 days). This prohibitive expense motivated three distinct paradigms for making NAS practical: **weight-sharing**, **evolutionary**, and **differentiable** methods. Each embodies a fundamentally different strategy for navigating the architecture-performance landscape, and each carries distinct trade-offs in search cost, result quality, and reliability.

This report compares the three approaches on their core mechanisms, landmark results, known failure modes, and current standing. A critical theme throughout: reported results across NAS papers are notoriously difficult to compare fairly due to differences in search spaces, training protocols, data augmentation, and evaluation budgets -- a confound that has itself become a subject of study (Li and Talwalkar, 2020; Yu et al., 2020).

## 2. Weight-Sharing Methods

### 2.1 Core Mechanism

Weight-sharing methods construct a single **supernet** (also called a one-shot model) that subsumes all candidate architectures in the search space as subnetworks. The supernet is a directed acyclic graph where each edge contains all candidate operations (convolutions of various kernel sizes, pooling, skip connections, etc.), and each candidate architecture corresponds to a specific selection of one operation per edge -- a *path* through the supernet.

Instead of training each candidate from scratch, all architectures share a common set of weights within this supernet. The search procedure involves two phases:

1. **Supernet training.** The supernet is trained by iteratively sampling subnetworks (paths) and performing gradient updates on the shared weights of the sampled operations. Different methods vary in their sampling strategy: ENAS uses a learned controller (trained with REINFORCE) to sample promising paths; SPOS uses uniform random sampling to ensure equal training across all subnetworks; and OFA uses progressive shrinking, starting with the largest subnetwork and gradually introducing smaller ones.

2. **Architecture evaluation and selection.** After training, candidate architectures are evaluated using their inherited supernet weights -- without any fine-tuning or retraining. This evaluation is cheap (a single forward pass on validation data), enabling rapid screening of thousands of candidates. The top-ranked architectures are then retrained from scratch to obtain final performance numbers.

The key insight is that the shared weights provide a proxy for how well each architecture would perform if trained independently, reducing search cost from thousands of GPU-hours to single-digit GPU-days. The quality of this proxy -- the correlation between supernet-inherited performance and stand-alone trained performance -- is the central question for weight-sharing methods.

### 2.2 Key Papers and Results

**ENAS (Pham et al., 2018).** Efficient Neural Architecture Search via Parameter Sharing introduced the weight-sharing paradigm. ENAS trains a single set of shared parameters across all child models, using a controller (trained with REINFORCE) to sample architectures. On CIFAR-10, ENAS achieved **2.89% test error**, comparable to NASNet's 2.65%, while reducing search cost from ~20,000 GPU-hours to just **0.5 GPU-days** (~12 GPU-hours on a single GPU) -- a ~1000x reduction. This result established that competitive architectures could be found without training each candidate independently.

**Single Path One-Shot (SPOS) (Guo et al., 2020).** SPOS simplified the supernet by activating only a single path per training step, using uniform random sampling to ensure all subnetworks receive equal training. After supernet training (120 epochs on 8 GPUs), an evolutionary algorithm searches for the best architecture by evaluating candidates via inherited supernet weights -- no fine-tuning required. SPOS achieved **74.3% top-1 accuracy on ImageNet** in the MobileNet search space. The method demonstrated that decoupling supernet training from architecture search (using uniform sampling rather than a learned controller) improved both simplicity and reliability.

**Once-for-All (OFA) (Cai et al., 2020).** OFA extended weight-sharing to the deployment setting: train a single elastic network once, then extract specialized subnetworks for diverse hardware targets without retraining. Using progressive shrinking to train a supernet supporting >10^19 subnetworks, OFA achieved **80.0% ImageNet top-1 accuracy** under mobile constraints (<600M MACs) -- the first time 80% was reached in this regime. OFA was 2.6x faster than EfficientNet-B2 at comparable accuracy, and up to 4.0% more accurate than MobileNetV3 at comparable latency.

### 2.3 Limitations

The central weakness of weight-sharing is the **ranking correlation problem**: the performance of a subnetwork using inherited supernet weights may not reliably predict its performance when trained from scratch. Studies have shown that commonly used supernet training heuristics can actually *worsen* this correlation (Yu et al., 2021), and that simple factors like hyperparameter tuning matter more than sophisticated sampling strategies. K-shot NAS (Su et al., 2021) proposed using multiple supernets to reduce weight interference, acknowledging that a single shared weight set is a fundamentally lossy proxy. Despite these concerns, weight-sharing remains practical because even imperfect ranking is sufficient to filter the search space down to a shortlist of strong candidates.

## 3. Evolutionary Methods

### 3.1 Core Mechanism

Evolutionary NAS applies principles from biological evolution to explore the architecture space. A **population** of candidate architectures is maintained, with each individual representing a complete architecture encoded as a genome (genotype). Common encodings include fixed-length vectors specifying the operation type and connectivity at each position in a cell template, or variable-length graphs representing full network topologies.

The search proceeds through iterative cycles:

1. **Fitness evaluation.** Each candidate architecture in the population is trained (fully or partially) on the target task, and its validation performance serves as its fitness score. This is the computational bottleneck -- each evaluation requires training a neural network, typically for tens to hundreds of epochs.

2. **Selection.** High-fitness individuals are chosen as parents for the next generation. Tournament selection is common: a random subset of the population is sampled, and the fittest individual is selected. Real et al. (2019) introduced *regularized evolution*, adding an age mechanism that removes the oldest individual regardless of fitness, preventing population stagnation.

3. **Mutation.** Parent architectures are modified by randomly changing operation types (e.g., replacing a 3x3 convolution with a 5x5 convolution), altering connectivity (adding or removing skip connections), or adjusting structural parameters (number of channels, number of layers). Mutation is the primary source of architectural novelty.

4. **Crossover** (optional). Elements from two parent architectures are combined to produce offspring. Designing effective crossover operators for neural architectures is non-trivial, as naively splicing subgraphs often produces dysfunctional networks. Some methods (e.g., AmoebaNet) rely primarily on mutation and omit crossover entirely.

Low-fitness or old individuals are removed, and the cycle repeats over hundreds to thousands of generations. The population-based approach naturally explores diverse regions of the search space and can optimize multiple objectives simultaneously (e.g., accuracy and FLOPs), since the population can maintain individuals spread across the Pareto front.

### 3.2 Key Papers and Results

**AmoebaNet / Regularized Evolution (Real et al., 2019).** Real et al. introduced *regularized evolution*, which modifies standard tournament selection by adding an age mechanism: the oldest individual in the population is removed regardless of fitness, preventing stagnation. Applied to the NASNet search space, AmoebaNet-A achieved **83.9% top-1 / 96.6% top-5 accuracy on ImageNet** when scaled up -- a new state-of-the-art at the time. The paper also demonstrated that evolutionary methods matched RL-based search in final accuracy while exhibiting better *anytime performance* (finding good architectures earlier in the search). The search cost was substantial: **3,150 GPU-days** (450 GPUs for 7 days). AmoebaNet-D subsequently won the Stanford DAWNBench competition for lowest ImageNet training cost, demonstrating that evolved architectures could be both accurate and efficient.

**NSGA-Net (Lu et al., 2019).** NSGA-Net applied the NSGA-II multi-objective genetic algorithm to NAS, simultaneously optimizing classification error and computational complexity (FLOPs). On CIFAR-10, it achieved **3.72% test error at 4.5M FLOPs** and **8.64% error on CMU-Car alignment at 26.6M FLOPs**, producing a Pareto front of architectures spanning the accuracy-efficiency trade-off in a single run. This multi-objective capability is a natural strength of evolutionary methods -- the population inherently maintains diverse solutions along the trade-off frontier, unlike single-objective methods that require separate runs per constraint.

**Large-Scale Evolution (Real et al., 2017).** An earlier landmark, this work evolved architectures from minimal starting points (single-layer networks) using only mutation operators. Starting from trivial architectures and evolving over 250 GPU-years of computation, the method discovered architectures achieving **94.6% test accuracy on CIFAR-10** and **77.0% on CIFAR-100**. While the search cost was impractical, the work demonstrated that evolution could discover competitive architectures without human-designed building blocks.

### 3.3 Limitations

The primary limitation of evolutionary NAS is **sample inefficiency**: each fitness evaluation requires training a candidate architecture to convergence (or near-convergence), making the total search cost proportional to `population_size x generations x per_candidate_training_cost`. Even with massive parallelization (450 GPUs for AmoebaNet), this produces costs measured in thousands of GPU-days -- orders of magnitude more expensive than weight-sharing or differentiable methods.

Additional weaknesses include:

- **Mutation operator sensitivity.** Poorly designed genotype representations can create rugged fitness landscapes where small mutations cause large performance swings, making the search erratic. The choice of which architectural elements to mutate and the granularity of mutations significantly affects search quality.
- **Crossover difficulty.** Designing effective crossover operators for neural architectures remains an open problem. Neural networks are not modular in the way biological genomes are -- splicing half a network from one parent with half from another rarely produces a functional offspring.
- **Stochasticity.** The same evolutionary algorithm run with different random seeds can produce architectures with meaningfully different performance, making results difficult to reproduce. This is compounded by the high cost per run, which limits the number of independent trials that are feasible.
- **Scalability to large search spaces.** As the architecture search space grows (e.g., full network topology search rather than cell-based search), the number of generations required for convergence increases, further amplifying the cost disadvantage.

## 4. Differentiable Methods

### 4.1 Core Mechanism

Differentiable NAS reformulates the discrete architecture search problem as a **continuous optimization** problem amenable to gradient descent. The architecture is represented as a directed acyclic graph (DAG) where each edge connects two nodes (feature maps). At each edge, instead of selecting a single operation from the candidate set {3x3 conv, 5x5 conv, max pool, skip connection, zero/none, ...}, a **continuous relaxation** computes a weighted mixture of all operations:

```
output(i,j) = sum_o [ alpha_o * op_o(input_i) ]
```

where `alpha_o` are architecture parameters (one per operation per edge), normalized via softmax so they sum to one. These architecture parameters define a probability distribution over operations and are treated as continuous variables optimized jointly with the network weights via backpropagation.

The architecture search becomes a **bilevel optimization**:

- **Inner loop (network weights):** Given current architecture parameters alpha, train the network weights `w` by minimizing the training loss: `w* = argmin_w L_train(w, alpha)`.
- **Outer loop (architecture parameters):** Given the trained weights, update alpha by minimizing the validation loss: `alpha* = argmin_alpha L_val(w*(alpha), alpha)`.

In practice, DARTS approximates this bilevel optimization by alternating single gradient steps on `w` and `alpha`, using either a first-order approximation (treating `w` as independent of `alpha`) or a second-order approximation (accounting for how `alpha` affects the optimal `w` via the Hessian). The first-order variant is cheaper but less accurate.

After search, the final discrete architecture is derived by selecting the operation with the highest architecture weight at each edge (**argmax discretization**). This discretization step introduces a gap between the continuous relaxation (where all operations contribute proportionally) and the derived architecture (where only one operation is active per edge).

### 4.2 Key Papers and Results

**DARTS (Liu et al., 2019).** The foundational differentiable NAS paper, DARTS achieved **2.76 +/- 0.09% test error on CIFAR-10** with 3.3M parameters and transferred to ImageNet at **26.7% top-1 error** (73.3% top-1 accuracy). The search cost was **1.5 GPU-days** on a single GPU (4 GPU-days for the second-order approximation variant) -- three orders of magnitude cheaper than RL-based NAS (1,800 GPU-days for NASNet) and evolutionary NAS (3,150 GPU-days for AmoebaNet). DARTS demonstrated that gradient-based optimization could navigate architecture spaces as effectively as RL or evolution, at a fraction of the cost. However, the method's simplicity concealed instabilities that would become apparent in subsequent work.

**ProxylessNAS (Cai et al., 2019).** ProxylessNAS extended differentiable search to operate directly on the target task and hardware, eliminating the need for proxy tasks (e.g., searching on CIFAR-10 and transferring to ImageNet). It introduced **latency regularization** as a differentiable loss term, enabling hardware-aware architecture optimization. On ImageNet, ProxylessNAS improved top-1 accuracy by **2.6% over MobileNetV2** at comparable mobile latency (78ms vs. 143ms for equivalent accuracy), and by **3.1% over MobileNetV2 on GPU** while being 1.2x faster. Search cost was **~200 GPU-hours** -- 200x less than competing methods. ProxylessNAS also demonstrated that architectures optimized for different hardware (GPU, CPU, mobile) have fundamentally different structures, making hardware-aware search essential.

**FairDARTS (Chu et al., 2020) and DARTS- (Chu et al., 2021).** These papers diagnosed and addressed DARTS' **performance collapse** problem: during search, skip connections accumulate unfairly high architecture weights because their parameter-free nature provides a gradient shortcut, causing the searched architecture to degenerate into a chain of skip connections with minimal learned computation. FairDARTS replaced the exclusive softmax competition with independent sigmoid activations per operation, pushing weights toward binary (zero-one) values and eliminating the unfair advantage. DARTS- instead added auxiliary skip connections to factor out the shortcut benefit, ensuring fairer competition among operations. Both achieved improved CIFAR-10 and ImageNet results over vanilla DARTS while producing architectures with meaningful learned operations rather than skip-connection-dominated designs.

### 4.3 Limitations

Differentiable NAS has several well-documented failure modes:

- **Skip-connection collapse** (discussed above). The most prominent failure mode, where parameter-free skip connections dominate the architecture weights because they provide easy gradient flow without competing for capacity. This has spawned an entire sub-literature of fixes (FairDARTS, DARTS-, P-DARTS, Lambda-DARTS), each addressing different aspects of the unfair competition.

- **Discretization gap.** The architecture that performs best in the continuous relaxation (mixed operations weighted by softmax) may not be the best after discretization (argmax selection of one operation per edge). During search, all operations contribute proportionally, creating a smooth loss landscape. After discretization, only one operation is active, and the actual discrete architecture may behave very differently from its continuous surrogate. This gap is fundamental and has no clean solution within the DARTS framework.

- **Memory intensity.** The entire supernet with all candidate operations must fit in GPU memory during search, because the continuous relaxation requires forward and backward passes through every operation at every edge simultaneously. This limits the size of the search space and the resolution of the proxy task (e.g., requiring smaller input images or fewer channels during search).

- **Bilevel optimization instability.** The first-order DARTS approximation ignores the dependency of optimal weights on architecture parameters, which can lead to convergence to poor local optima. The second-order approximation is more accurate but 2-3x more expensive and can exhibit its own instabilities, including oscillating architecture parameters.

- **Seed sensitivity.** DARTS results vary significantly across random seeds. Zela et al. (2020) showed that the same DARTS configuration can produce architectures ranging from near-state-of-the-art to degenerate, depending on the random initialization -- a level of variance that undermines confidence in any single reported result.

## 5. Comparative Analysis

### 5.1 Summary Table

| Dimension | Weight-Sharing | Evolutionary | Differentiable |
|---|---|---|---|
| **Search cost** | 0.5-4 GPU-days | 1,000-3,150 GPU-days | 1.5-4 GPU-days |
| **CIFAR-10 error** | 2.89% (ENAS) | 2.13% (AmoebaNet-A) | 2.76% (DARTS) |
| **ImageNet top-1** | 74.3-80.0% (SPOS/OFA) | 83.9% (AmoebaNet-A, scaled) | 73.3% (DARTS); 75.1%+ (ProxylessNAS) |
| **Multi-objective** | Limited (post-hoc filtering) | Native (NSGA-Net, Pareto fronts) | Via differentiable regularization |
| **Hardware-awareness** | Supernet + constraint filtering | Fitness function includes latency | Latency as differentiable loss |
| **Search space flexibility** | High (any supernet-encodable space) | High (any encodable genotype) | Moderate (must be differentiable-relaxable) |
| **Reproducibility** | Moderate (supernet training variance) | Low-moderate (stochastic population dynamics) | Low (collapse sensitivity, seed dependence) |
| **Key failure mode** | Ranking correlation breakdown | Sample inefficiency | Skip-connection collapse, discretization gap |

### 5.2 Methodological Confounds in Cross-Paper Comparisons

A recurring problem in NAS literature is that reported results are not directly comparable across papers. This issue is severe enough that some researchers have questioned whether NAS papers demonstrate genuine algorithmic advances or merely better engineering of confounding factors. Key confounds include:

- **Search space design matters more than search algorithm.** Li and Talwalkar (2020) showed that random search within well-designed search spaces can match or exceed sophisticated NAS methods, suggesting that much of the reported performance comes from the search space itself rather than the search strategy. This finding implies that the "best" NAS method may simply be the one evaluated in the best search space.

- **Training protocol differences.** Architectures found by different methods are often retrained with different augmentation strategies (e.g., Cutout, AutoAugment, MixUp), learning rate schedules, regularization (dropout rates, weight decay), and epoch budgets. These training details can account for >1% accuracy difference on CIFAR-10, which often exceeds the difference between architectures found by different NAS methods.

- **Transfer vs. direct search.** Methods that search on CIFAR-10 and transfer to ImageNet (DARTS, AmoebaNet) operate in a fundamentally different regime than methods that search directly on ImageNet (ProxylessNAS, OFA). The assumption that architecture rankings transfer across datasets is itself unverified, making cost comparisons between proxy-based and direct methods misleading.

- **Scaled vs. unscaled results.** AmoebaNet-A's headline 83.9% ImageNet result uses a model scaled far beyond the original searched architecture (more channels, more cells). This conflates architecture quality with scaling strategy -- any reasonably good architecture may reach similar accuracy at sufficient scale.

- **Reporting bias.** NAS papers typically report the best result across multiple runs, seeds, or search configurations. With enough trials, even random search will find strong architectures in a well-designed search space. Few papers report mean performance across runs with confidence intervals.

### 5.3 The Role of Search Space Design

A meta-observation across all three approaches: the design of the search space itself is arguably more important than the choice of search algorithm. The progression from early NAS (unconstrained topology search) to cell-based NAS (searching within a fixed macro-architecture) to hardware-aware search spaces (constrained by latency budgets) has driven more practical improvement than algorithmic innovations within any single paradigm. This suggests that human expertise in defining *what to search over* remains essential, even when the search itself is automated.

## 6. Current Dominance: Weight-Sharing Leads in Practice

### 6.1 Evidence for Weight-Sharing Dominance

Weight-sharing methods are the **dominant paradigm in applied NAS** as of 2025, for several reinforcing reasons:

1. **Cost efficiency.** Search costs of 0.5-4 GPU-days make weight-sharing practical for industrial deployment, where NAS must be rerun for each new task, dataset, or hardware target. Evolutionary methods' ~1000x higher cost is prohibitive for iterative deployment.

2. **Industry adoption.** The most widely deployed NAS systems use weight-sharing: Google's MnasNet and EfficientNet families used weight-sharing-based search; MIT HAN Lab's OFA/ProxylessNAS are weight-sharing methods deployed across edge devices; and platforms like Microsoft NNI and AutoGluon default to weight-sharing-based one-shot methods.

3. **Hardware-aware deployment.** OFA demonstrated that a single supernet training run can produce specialized architectures for >10^19 deployment scenarios, making the amortized per-deployment cost nearly zero. No evolutionary or differentiable method achieves comparable deployment efficiency.

4. **Practical sufficiency.** While the ranking correlation of supernet evaluation is imperfect, it is sufficient for practical use: the top-k architectures ranked by supernet performance consistently include strong candidates, even if the exact ranking is noisy.

### 6.2 Where Other Approaches Excel

Evolutionary methods retain advantages in **multi-objective optimization** (producing full Pareto fronts in a single run), **search space flexibility** (no differentiability or supernet-encodability requirements), and settings where the search budget is not the bottleneck. They are also seeing renewed relevance through integration with zero-cost proxies (see Section 7).

Differentiable methods excel in **speed of iteration** and **search space analysis** -- the continuous relaxation provides gradient-based insights into which operations and connectivity patterns matter, useful for search space design even when the final architecture is selected by other means.

## 7. Hybrid Approaches and Emerging Trends

### 7.1 Convergence of Paradigms

The boundaries between the three approaches have blurred significantly:

- **SPOS** combines weight-sharing (supernet training) with evolutionary search (architecture selection) -- arguably the most successful hybrid.
- **OFA** uses weight-sharing with progressive shrinking, a training strategy inspired by evolutionary curriculum concepts.
- **ProxylessNAS** blends differentiable relaxation (for architecture parameters) with weight-sharing (supernet training), while also supporting RL-based path selection.
- **NSGA-Net II** and follow-up work combine evolutionary multi-objective search with supernet-based fitness evaluation, reducing the per-candidate evaluation cost that historically limited evolutionary methods.

This convergence suggests that the three "approaches" are better understood as **complementary components** (supernet training, population-based exploration, gradient-based refinement) that can be mixed rather than as competing paradigms.

### 7.2 Zero-Cost Proxies

A major emerging direction is **zero-cost NAS**, which evaluates architectures using metrics computed at initialization -- no training required. These proxies analyze properties of randomly initialized networks to predict their trained performance:

- **SynFlow** measures the sum of synaptic flow (product of absolute parameter values along paths), correlating with network trainability. It demonstrates the most consistent performance across search spaces.
- **Jacob Covariance** computes the covariance of the Jacobian of the network's outputs with respect to inputs, capturing the diversity of learned representations.
- **NASWOT** (NAS Without Training) scores architectures based on the overlap of activation patterns across different inputs, correlating with network expressivity.

Zero-cost proxies reduce per-architecture evaluation from hours (training) or seconds (supernet inference) to **milliseconds**, making them natural complements to evolutionary search where the bottleneck is per-candidate evaluation cost. Recent work (2025) integrates zero-cost proxies directly into evolutionary operators: proxy-guided crossover favors combining components with high proxy scores, and proxy-regularized fitness functions combine trained accuracy with zero-cost metrics to improve search direction.

The limitation is reliability: no single zero-cost proxy correlates consistently with trained performance across all search spaces and tasks. Ensemble approaches (combining multiple proxies) partially address this but introduce their own calibration challenges.

### 7.3 LLM-Guided Architecture Search

An emerging 2025-2026 trend is using large language models to guide architecture search. Frameworks like LLM-NAS and RZ-NAS leverage LLMs' code-level understanding to propose and refine architectures, using zero-cost proxies for evaluation feedback. This represents a qualitative shift from numeric optimization to knowledge-driven search, though the approach remains nascent -- no LLM-guided method has yet displaced established NAS pipelines on standard benchmarks.

### 7.4 NAS in the Foundation Model Era

The relevance of traditional NAS has narrowed as foundation model scaling (increasing parameters, data, and compute along known scaling laws) has emerged as the dominant strategy for achieving state-of-the-art performance on most tasks. When the architecture is a standard Transformer and the primary lever is scale, there is less room for architecture search to add value. The irony is that NAS was born from the desire to automate architecture design, but the field has converged on a single architecture family (Transformers) where manual design -- or simply scaling up -- often suffices.

However, NAS remains critical in several domains where scaling alone is insufficient:

- **Edge and mobile deployment**, where compute constraints make architecture efficiency essential. This is where weight-sharing methods (OFA, ProxylessNAS) have had the most practical impact, and where the search problem is most clearly defined: maximize accuracy under hard latency/memory/power constraints.
- **Hybrid LLM architectures**, where the design space (attention variants, MLP configurations, Mamba-style state-space layers, mixture-of-experts routing) is too large for manual exploration. Despite promising advances in hybrid architectures, the design process remains manual and intuition-driven as of 2025 -- no systematic NAS framework for hybrid LLMs has been established.
- **Efficient inference**, where architecture choices interact with hardware-specific optimizations (quantization, sparsity, operator fusion) in ways that scaling alone cannot address. The growing diversity of inference hardware makes this a structurally expanding search problem.
- **Specialized scientific models**, where domain-specific architectural priors (symmetry, conservation laws, multi-scale structure) interact with standard neural network components in ways that resist simple scaling.

## 8. Open Questions and Future Directions

1. **Benchmark reliability.** NAS-Bench-101/201/301 standardized evaluation but cover narrow, CNN-centric search spaces. Can benchmark suites scale to the architecture spaces relevant to modern models (Transformers, hybrid attention-SSM architectures, mixture-of-experts) without becoming stale? The tabular benchmark approach (precomputing all architectures' performance) does not scale to the combinatorial spaces of interest.

2. **Supernet training theory.** Weight-sharing works empirically but lacks theoretical grounding for *when* and *why* supernet-derived rankings correlate with standalone performance. Under what conditions does the approximation break down? What properties of the search space or training procedure guarantee (or destroy) ranking fidelity? Closing this gap would move weight-sharing from heuristic to principled method.

3. **NAS for non-vision tasks.** The overwhelming majority of NAS research uses CIFAR-10 and ImageNet image classification benchmarks. Application to NLP (beyond simple RNN cell search), speech recognition, scientific computing, graph neural networks, and multimodal models remains underexplored relative to the potential impact. Each domain introduces unique architectural constraints and evaluation challenges.

4. **NAS + scaling laws.** Can NAS methods discover architectures that scale more efficiently than standard Transformers -- i.e., achieve better loss at a given compute budget? The intersection of architecture search and neural scaling laws is largely unexplored. If architecture choices affect the scaling exponent (not just the constant), NAS could yield compounding returns at scale. Early evidence from hybrid Transformer-Mamba architectures suggests that architectural innovations can indeed shift scaling curves, but no systematic NAS-driven exploration exists.

5. **Reproducibility crisis.** Many NAS papers report results within noise margins of each other, and the field has struggled with reproducibility. The NAS community needs standardized evaluation protocols -- fixed search spaces, identical training pipelines, mandatory reporting of mean and variance across seeds, and transparent computational budget accounting -- to distinguish genuine algorithmic advances from engineering artifacts.

6. **NAS under deployment constraints.** Real-world deployment involves constraints beyond latency and FLOPs: memory footprint, power consumption, quantization compatibility, compiler optimizability, and batch inference throughput. Multi-constraint NAS that accounts for the full deployment stack remains an open challenge, particularly as hardware diversity (GPUs, NPUs, edge TPUs, custom accelerators) continues to grow.

7. **Can NAS discover genuinely novel architectures?** Most NAS methods search within human-designed search spaces that encode strong inductive biases (e.g., cell-based structures, predefined operation sets). Whether NAS can discover architectures that are qualitatively different from human designs -- rather than optimizing within the space of human-conceived possibilities -- remains an open and arguably fundamental question for the field.

## 9. Conclusion

Weight-sharing methods dominate applied NAS in 2025 due to their favorable cost-quality trade-off: search costs of 0.5-4 GPU-days, sufficient ranking accuracy for practical use, and natural integration with hardware-aware deployment pipelines. Evolutionary methods retain advantages in multi-objective optimization and search space flexibility but are constrained by per-candidate training costs that run 100-1000x higher. Differentiable methods introduced the field's most elegant formulation but have been plagued by instabilities (collapse, discretization gap, seed sensitivity) that limit their reliability.

The most important meta-insight from the NAS literature is that the three "competing" paradigms are converging into complementary components of unified systems: supernet training (from weight-sharing), population-based exploration (from evolution), and gradient-based refinement (from differentiable methods) are increasingly combined in hybrid approaches like SPOS, OFA, and ProxylessNAS. The future of NAS likely lies not in any single paradigm winning, but in their principled integration -- alongside emerging tools like zero-cost proxies and LLM-guided search -- applied to the architecture design problems that pure scaling cannot solve.

## References

1. Zoph, B., & Le, Q. V. (2017). Neural Architecture Search with Reinforcement Learning. *ICLR 2017*. [arXiv:1611.01578]
2. Pham, H., Guan, M. Y., Zoph, B., Le, Q. V., & Dean, J. (2018). Efficient Neural Architecture Search via Parameter Sharing. *ICML 2018*. [arXiv:1802.03268]
3. Guo, Z., Zhang, X., Mu, H., et al. (2020). Single Path One-Shot Neural Architecture Search with Uniform Sampling. *ECCV 2020*. [arXiv:1904.00420]
4. Cai, H., Gan, C., Wang, T., Zhang, Z., & Han, S. (2020). Once-for-All: Train One Network and Specialize it for Efficient Deployment. *ICLR 2020*. [arXiv:1908.09791]
5. Real, E., Aggarwal, A., Huang, Y., & Le, Q. V. (2019). Regularized Evolution for Image Classifier Architecture Search. *AAAI 2019*. [arXiv:1802.01548]
6. Lu, Z., Whalen, I., Boddeti, V., et al. (2019). NSGA-Net: Neural Architecture Search using Multi-Objective Genetic Algorithm. *GECCO 2019*. [arXiv:1810.03522]
7. Real, E., Moore, S., Selle, A., et al. (2017). Large-Scale Evolution of Image Classifiers. *ICML 2017*. [arXiv:1703.01041]
8. Liu, H., Simonyan, K., & Yang, Y. (2019). DARTS: Differentiable Architecture Search. *ICLR 2019*. [arXiv:1806.09055]
9. Cai, H., Zhu, L., & Han, S. (2019). ProxylessNAS: Direct Neural Architecture Search on Target Task and Hardware. *ICLR 2019*. [arXiv:1812.00332]
10. Chu, X., Zhou, T., Zhang, B., & Li, J. (2020). Fair DARTS: Eliminating Unfair Advantages in Differentiable Architecture Search. *ECCV 2020*. [arXiv:1911.12126]
11. Chu, X., Wang, X., Zhang, B., et al. (2021). DARTS-: Robustly Stepping out of Performance Collapse Without Indicators. *ICLR 2021*. [arXiv:2009.01027]
12. Li, L., & Talwalkar, A. (2020). Random Search and Reproducibility for Neural Architecture Search. *UAI 2020*. [arXiv:1902.07638]
13. Yu, K., Sciuto, C., Jaggi, M., Muber, C., & Salzmann, M. (2020). Evaluating the Search Phase of Neural Architecture Search. *ICLR 2020*. [arXiv:1902.08142]
14. Yu, K., Ranftl, R., & Salzmann, M. (2021). How to Train Your Super-Net: An Analysis of Training Heuristics in Weight-Sharing NAS. *arXiv:2110.01154*.
15. Su, X., You, S., Zheng, F., et al. (2021). K-shot NAS: Learnable Weight-Sharing for NAS with K-shot Supernets. *ICML 2021*.
16. Abdelfattah, M. S., Mehrotra, A., Dudziak, L., & Lane, N. D. (2021). Zero-Cost Proxies for Lightweight NAS. *ICLR 2021*. [arXiv:2101.08134]
17. Zela, A., Elsken, T., Saikia, T., Marber, Y., Brox, T., & Hutter, F. (2020). Understanding and Robustifying Differentiable Architecture Search. *ICLR 2020*. [arXiv:1909.09656]
18. Tan, M., Chen, B., Pang, R., et al. (2019). MnasNet: Platform-Aware Neural Architecture Search for Mobile. *CVPR 2019*. [arXiv:1807.11626]
