/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Runtime.PyTorch.Export
public import NN.Runtime.PyTorch.Import

/-!
# `NN.Runtime.PyTorch`

Gondolin’s reusable PyTorch interoperability layer.

This umbrella intentionally contains only bridge infrastructure:

- export Gondolin IR / parameters to readable PyTorch source;
- convert PyTorch `state_dict` checkpoints to Lean-readable JSON through a generated Python
  adapter; and
- capture supported PyTorch `nn.Module` graphs into Gondolin IR JSON; and
- parse those JSON artifacts into shape-checked Gondolin tensors, IR graphs, or verification
  parameter stores.

Model demos and tutorial round-trips live under `NN.Examples.Interop.PyTorch.*`; keeping them there
prevents runtime imports from quietly depending on example-only shapes.
-/

@[expose] public section
