/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Runtime.Autograd.Gondolin.NN
import Mathlib.Algebra.Order.Algebra

/-!
# Gondolin-executable model: compact Transformer block

Small Transformer-style block used by the ModelZoo compact block:

`MultiHeadAttention(x) → LayerNorm`

This is primarily useful as a “heavy op” test bed (MHA + LayerNorm) that still runs in Lean.
-/

@[expose] public section


namespace NN
namespace GraphSpec
namespace Models
namespace Gondolin

open NN.Tensor

/-- Attention + normalization block (no residuals yet). -/
def transformerBlock
    (batch n dModel numHeads headDim : Nat)
    {h_n : n ≠ 0} {h_dModel : dModel > 0}
    (seedW : Nat := 0)
    (seedGamma seedBeta : Nat := 0) :
    _root_.Runtime.Autograd.Gondolin.NN.Seq (.dim batch (.dim n (.dim dModel .scalar)))
      (.dim batch (.dim n (.dim dModel .scalar))) :=
  tlseq[
    _root_.Runtime.Autograd.Gondolin.NN.multiHeadAttention
      (batch := batch) (n := n) (dModel := dModel) (numHeads := numHeads) (headDim := headDim)
      (h1 := h_n) (seedW := seedW),
    _root_.Runtime.Autograd.Gondolin.NN.layerNorm
      (batch := batch) (seqLen := n) (embedDim := dModel)
      (h_seq_pos := Nat.pos_of_ne_zero h_n)
      (h_embed_pos := h_dModel)
      (seedGamma := seedGamma) (seedBeta := seedBeta)
  ]

end Gondolin
end Models
end GraphSpec
end NN
