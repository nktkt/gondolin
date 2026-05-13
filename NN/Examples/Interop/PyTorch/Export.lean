/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Examples.Interop.PyTorch.CNN.Export
public import NN.Examples.Interop.PyTorch.MLP.Export
public import NN.Examples.Interop.PyTorch.Transformer.Export

/-!
# PyTorch Example Exporters

Example-specific PyTorch `nn.Module` generators used by the round-trip examples.

These are intentionally outside `NN.Runtime.PyTorch`: they bake in tutorial model shapes and naming
conventions, while the runtime bridge owns the general IR and `state_dict` paths. The actual files
live beside their fixtures under `MLP/`, `CNN/`, and `Transformer/`.
-/

@[expose] public section
