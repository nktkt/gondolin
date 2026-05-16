/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Proofs.Verification.ODE

/-!
# Verification Proofs

Stable umbrella for proof-backed verification results.

This namespace is for theorems that turn verification hypotheses into mathematical guarantees.
Executable certificate checkers and parsers live under `NN.Verification`; the proof layer here is
where the accepted hypotheses are connected to real-analysis or model-level soundness statements.
-/

@[expose] public section

