/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Runtime.PyTorch.Export
public import NN.Runtime.PyTorch.Import

/-!
# `NN.Runtime.PyTorch`

Gondlin’s reusable PyTorch interoperability layer.

This umbrella intentionally contains only bridge infrastructure:

- export Gondlin IR / parameters to readable PyTorch source;
- convert PyTorch `state_dict` checkpoints to Lean-readable JSON through a generated Python
  adapter; and
- capture supported PyTorch `nn.Module` graphs into Gondlin IR JSON; and
- parse those JSON artifacts into shape-checked Gondlin tensors, IR graphs, or verification
  parameter stores.

Model demos and tutorial round-trips live under `NN.Examples.Interop.PyTorch.*`; keeping them there
prevents runtime imports from quietly depending on example-only shapes.
-/

@[expose] public section
