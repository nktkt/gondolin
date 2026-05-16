---
# layout: home
usemathjax: true
---

<div class="hero home-hero">
  <div class="hero-text">
    <p class="lede">
      Gondolin formalizes neural network infrastructure in Lean 4, connecting typed tensor and
      layer specifications, runnable training examples, graph IR semantics, floating-point
      contracts, CUDA trust boundaries, and artifacts that Lean checkers can inspect.
    </p>

    <p class="lede">
      The goal is a practical bridge between modern ML workflows and formal reasoning: models can be
      executed, lowered, inspected, imported from PyTorch-style pipelines, and checked against
      explicit mathematical contracts.
    </p>
  </div>
</div>

## What Gondolin Gives You

<div class="home-overview">
  <img
    src="{{ '/assets/media/figures/gondolin-layout.png' | relative_url }}"
    alt="Gondolin overview: typed tensors, shared graph IR, verified reverse mode autograd, IEEE-754 semantics, certificate checking, PyTorch round trip, CUDA trust boundary, approximation theorems, and Lean verification."
    loading="lazy" />
</div>

## Where It Fits

Gondolin sits between the software people already use and the proof artifacts they want to trust.
The project is written in [Lean 4](https://lean-lang.org/) and uses a PyTorch-style surface where
that makes model code easier to read. For the Python ecosystem, see the official
[PyTorch documentation](https://pytorch.org/docs/stable/index.html); for Lean itself, start with the
[Lean documentation](https://lean-lang.org/documentation/).

## Paper / Citation

```bibtex
@misc{george2026gondolinformalizingneuralnetworks,
      title={Gondolin: Formalizing Neural Networks in Lean},
      author={Robert Joseph George and Jennifer Cruden and Xiangru Zhong and Huan Zhang and Anima Anandkumar},
      year={2026},
      eprint={2602.22631},
      archivePrefix={arXiv},
      primaryClass={cs.MS},
      url={https://arxiv.org/abs/2602.22631},
}
```
