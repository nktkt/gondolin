/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.IR.Check
public import NN.IR.Graph
public import NN.IR.Infer
public import NN.IR.OpContracts
public import NN.IR.Pretty
public import NN.IR.Semantics

/-!
# IR entrypoint

Curated umbrella import for Gondolin's op-tagged intermediate representation.

Use this when you want the whole IR subsystem: graph syntax, operation contracts, shape inference,
validation wrappers, denotational semantics, and pretty-printers. The individual `NN.IR.*` files
remain focused implementation modules for internal code that needs a smaller dependency footprint.
-/

@[expose] public section

