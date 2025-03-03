# nvBench 2.0

This is the repository that contains source code for the [nvBench 2.0 website](https://nvbench2.github.io).

## nvBench 2.0: A Benchmark for Natural Language to Visualization under Ambiguity

Natural Language to Visualization (nl2vis) enables users to create visualizations from natural language queries, making data insights more accessible. However, nl2vis faces challenges in interpreting ambiguous queries, as users often express their visualization needs in imprecise language.

To address this challenge, we introduce nvBench 2.0, a new benchmark designed to evaluate nl2vis systems in scenarios involving ambiguous queries. nvBench 2.0 includes 7,878 natural language queries and 24,076 corresponding visualizations, derived from 780 tables across 153 domains. It is built using a controlled ambiguity-injection pipeline that generates ambiguous queries through a reverse-generation workflow. By starting with unambiguous seed visualizations and selectively injecting ambiguities, the pipeline yields multiple valid interpretations for each query, with each ambiguous query traceable to its corresponding visualization through step-wise reasoning paths.

We evaluate various Large Language Models (LLMs) on their ability to perform ambiguous nl2vis tasks using nvBench 2.0. We also propose Step-nl2vis, an LLM-based model trained on nvBench 2.0, which enhances performance in ambiguous scenarios through step-wise preference optimization. Our results show that Step-nl2vis outperforms all baselines, setting a new state-of-the-art for ambiguous nl2vis tasks.

## BibTeX

If you find nvBench 2.0 useful for your work please cite:

```
@article{luo2024nvbench2,
  author    = {Luo, Tianqi and Huang, Chuhan and Shen, Leixian and Li, Boyan and Shen, Shuyu and Zeng, Wei and Tang, Nan and Luo, Yuyu},
  title     = {nvBench 2.0: A Benchmark for Natural Language to Visualization under Ambiguity},
  journal   = {PVLDB},
  year      = {2024},
}
```

## Website License

`<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" />``</a><br />`This work is licensed under a `<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">`Creative Commons Attribution-ShareAlike 4.0 International License `</a>`.
