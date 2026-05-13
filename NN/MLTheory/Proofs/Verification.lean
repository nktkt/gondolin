/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.MLTheory.Proofs.Verification.Robustness

/-!
# Verification-oriented proofs

This entrypoint gathers theorem files that connect verification certificates to mathematical
properties. At present this chapter focuses on robustness: Lipschitz and margin certificates imply
stable classifier outputs under bounded perturbations.
-/

@[expose] public section
