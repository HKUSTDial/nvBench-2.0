# nvBench 2.0: A Benchmark for Natural Language to Visualization under Ambiguity

This repository contains the source code and data for the nvBench 2.0 benchmark, designed to evaluate Natural Language to Visualization (nl2vis) systems in scenarios involving ambiguous queries.

## Introduction

Natural Language to Visualization (nl2vis) enables users to create visualizations from natural language queries, making data insights more accessible. However, nl2vis faces challenges in interpreting ambiguous queries, as users often express their visualization needs in imprecise language.

## Example of Reasoning through Ambiguity

![Figure 1: Example of reasoning appropriate visualizations from an ambiguous natural language query](https://claude.ai/chat/figures/fig1.png)

As shown in Figure 1, a seemingly straightforward query like "Show the gross trend of comedy and action movies by year" contains multiple ambiguities:

* At the data layer, "gross" could refer to either World_Gross or Local_Gross columns
* "Comedy and action" implicitly requires filtering by Genre
* At the visualization layer, "trend" may suggest a bar chart or line chart
* "By year" implies temporal binning that isn't explicitly defined

To address this ambiguous nl2vis task, we resolve ambiguity via a human-like reasoning workflow that breaks the process into five steps:

1. **Data Selection Reasoning** - Identifying candidate columns for "gross"
2. **Chart Type Reasoning** - Evaluating appropriate chart types for trend analysis
3. **Channel Mapping Reasoning** - Mapping data fields to visual channels
4. **Data Transformation Reasoning** - Applying temporal binning and aggregation
5. **Visualization Synthesis Reasoning** - Generating multiple valid outputs

## Ambiguity-Injected NL2VIS Data Synthesizer

![Figure 2: An overview of ambiguity-injected nl2vis data synthesizer](https://claude.ai/chat/figures/fig2.png)

We developed an ambiguity-injected nl2vis data synthesizer that systematically introduces controlled ambiguity into visualization specifications. As shown in Figure 2, our pipeline:

(a)  **Ambiguity-aware VIS Tree Synthesis** : Begins with seed visualizations and injects ambiguity nodes to create ambiguity-aware visualization trees
(b)  **VIS Synthesis** : Uses an ASP solver to resolve these trees into multiple valid visualizations
(c)  **NL Synthesis** : Generates ambiguous natural language queries that correspond to the multiple valid visualizations
(d)  **Reasoning Path Synthesis** : Produces step-wise reasoning paths that document how ambiguities are resolved

## Controlled Ambiguity Injection Process

![Figure 3: Injecting ambiguities into a seed visualization](https://claude.ai/chat/figures/fig3.png)

Figure 3 demonstrates how we inject ambiguities into a seed visualization:

1. Starting with a seed chart (e.g., a bar chart showing gross by year)
2. Converting it to a seed visualization tree with explicit nodes
3. Injecting ambiguity nodes (e.g., introducing a choice between Local_Gross and World_Gross)
4. Resolving the tree into multiple valid visualization specifications
5. Flattening the trees into concrete visualization queries

## Benchmark Comparison

**Table 1: Comparison of nl2vis benchmarks**

[Table 1 will be placed here]

nvBench 2.0 distinguishes itself from existing benchmarks by:

* Supporting one-to-many mapping from NL queries to visualizations
* Explicitly modeling query ambiguity
* Providing reasoning paths to explain ambiguity resolution
* Using LLM-based query generation for natural, diverse queries

## Dataset Statistics

**Table 3: Distribution of natural language styles across chart types and word count statistics**

[Table 3 will be placed here]

The dataset includes diverse query styles (commands, questions, and captions) across various chart types. The average query length is approximately 14 words, with a good balance across all visualization types.

**Table 4: Ambiguity count at each reasoning step**

[Table 4 will be placed here]

**Table 5: Statistics of ambiguity patterns**

[Table 5 will be placed here]

Our dataset contains diverse ambiguity patterns, with Channel Encoding (CE) being the most common type of ambiguity (88.06%), followed by Data Transformation (DT) ambiguities (46.00%). Many samples contain multiple types of ambiguity, highlighting the complexity of real-world visualization requests.

## Step-NL2VIS for Ambiguous NL2VIS Tasks

We propose Step-nl2vis, an LLM-based model trained on nvBench 2.0, which enhances performance in ambiguous scenarios through step-wise preference optimization.

### Preference Optimization with Step-DPO

Step-nl2vis incorporates step-wise direct preference optimization (Step-DPO), which aims to maximize the probability of correct reasoning steps and minimize incorrect ones. The objective function is formulated as:

```
L(θ) = -E(x,s₁~ₖ₋₁,sₘᵢₙ,sₗₒₛₑ)~Dₚ[log σ(β log(πθ(sₘᵢₙ|x,s₁~ₖ₋₁)/πᵣₑf(sₘᵢₙ|x,s₁~ₖ₋₁)) - β log(πθ(sₗₒₛₑ|x,s₁~ₖ₋₁)/πᵣₑf(sₗₒₛₑ|x,s₁~ₖ₋₁)))]
```

where:

* Dₚ represents the step-wise preference dataset
* πθ is the policy model to be optimized
* πᵣₑf is the reference model
* β controls the divergence between the optimized policy and reference model

## Experimental Evaluation

We conducted comprehensive experiments to validate the effectiveness of nvBench 2.0 for training and evaluating nl2vis systems under ambiguity.

**Table 6: Overall performance comparison between different models on nvBench 2.0**

[Table 6 will be placed here]

Our proposed Step-nl2vis achieves state-of-the-art performance across most metrics, significantly outperforming both prompting-based and fine-tuning-based baselines. Step-nl2vis obtains the highest F1@3 (81.50%) and F1@5 (80.88%), demonstrating its superior ability to handle ambiguity in nl2vis tasks.

**Figure 7: F1 across different models and ambiguity levels**

[Figure 7 will be placed here]

The heatmap shows that Step-nl2vis consistently outperforms other models across most chart types and ambiguity levels. Models incorporating step-wise reasoning generally show better performance than their direct prompting counterparts, confirming the effectiveness of decomposing complex visualization reasoning into explicit steps.

**Figure 8: Recall across different models and ambiguity levels**

[Figure 8 will be placed here]

Step-nl2vis demonstrates superior recall performance across all ambiguity levels examined. At ambiguity level 3, it achieves 83.3% recall, representing a significant improvement over comparative approaches. The performance advantage of Step-nl2vis over alternative approaches expands with increasing ambiguity levels.

## Citation

If you find nvBench 2.0 useful for your work, please cite:

```
@article{luo2024nvbench2,
  author    = {Luo, Tianqi and Huang, Chuhan and Shen, Leixian and Li, Boyan and Shen, Shuyu and Zeng, Wei and Tang, Nan and Luo, Yuyu},
  title     = {nvBench 2.0: A Benchmark for Natural Language to Visualization under Ambiguity},
  journal   = {PVLDB},
  year      = {2024},
}
```

<!-- ## License

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/). -->
