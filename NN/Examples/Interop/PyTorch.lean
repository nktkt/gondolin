/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Examples.Interop.PyTorch.Export
public import NN.Examples.Interop.PyTorch.Import
public import NN.Examples.Interop.PyTorch.Roundtrip
public import NN.Examples.Interop.PyTorch.TorchExportSmoke

/-!
# PyTorch Interop Examples

Curated umbrella for PyTorch-facing examples.

The folder has two intentionally separate paths:

- `TorchExportSmoke`: model-agnostic `nn.Module` graph capture into `gondolin.ir.v1`, followed by
  Lean-side parsing, value-graph handling, and tensor-IR shape validation.
- `Roundtrip`: small MLP/CNN/Transformer state-dict examples that generate/read JSON weights.

The reusable bridge lives under `NN.Runtime.PyTorch`; this module only collects examples.
-/

@[expose] public section
