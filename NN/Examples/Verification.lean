/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Examples.Verification.LiRPA
public import NN.Examples.Verification.Robustness
public import NN.Examples.Verification.Splines
public import NN.Examples.Verification.Gondolin
public import NN.Examples.Verification.VNNComp

/-!
# Verification Examples

Runnable and theorem-backed examples that demonstrate Gondolin's verification stack on concrete
artifacts. The reusable checkers remain under `NN.Verification`; the bundled certs and wrapper
modules live here so the examples tree is the visible place users look first.
-/

@[expose] public section
