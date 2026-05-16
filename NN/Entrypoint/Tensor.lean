/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Tensor.API

/-!
# Tensor entrypoint

Curated umbrella import for Gondolin's core tensor/shape API.

This is the stable subsystem import path for tensor literals, shape aliases, dynamic tensors, and
small executable tensor helpers. `NN.Tensor.API` remains the implementation leaf; downstream users
should prefer either `NN.Library` for the broad public surface or `NN.Entrypoint.Tensor` for just
the tensor layer.
-/

@[expose] public section
