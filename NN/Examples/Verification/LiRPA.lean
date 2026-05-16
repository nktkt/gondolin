/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Examples.Verification.LiRPA.AttentionVerify
public import NN.Examples.Verification.LiRPA.CnnVerify
public import NN.Examples.Verification.LiRPA.GruVerify
public import NN.Examples.Verification.LiRPA.MlpVerify
public import NN.Examples.Verification.LiRPA.TransformerEncoderVerify

/-!
# LiRPA Verification Examples

Bundled certificate checkers for small LiRPA-style artifacts: MLPs, CNNs, attention, GRU gates,
and transformer encoder blocks.
-/

@[expose] public section
