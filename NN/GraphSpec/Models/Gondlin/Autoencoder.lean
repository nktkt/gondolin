/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Runtime.Autograd.Gondlin.NN
import Mathlib.Algebra.Order.Algebra

/-!
# Gondlin-executable model: Autoencoder

Compact MLP autoencoder:

`Linear(in→hid) → Tanh → Linear(hid→in)`

This is a convenient “small-but-real” model for demos and tests:
- it has parameters,
- it has a nonlinearity,
- and it is still fast to run inside Lean.
-/

@[expose] public section


namespace NN
namespace GraphSpec
namespace Models
namespace Gondlin

open NN.Tensor

/-- 2-layer MLP autoencoder model. -/
def autoencoder
    (inDim hidDim : Nat)
    (seedW1 seedB1 seedW2 seedB2 : Nat := 0) :
    _root_.Runtime.Autograd.Gondlin.NN.Seq (Shape.Vec inDim) (Shape.Vec inDim) :=
  tlseq[
    _root_.Runtime.Autograd.Gondlin.NN.linear inDim hidDim
      (seedW := seedW1) (seedB := seedB1),
    _root_.Runtime.Autograd.Gondlin.NN.tanh,
    _root_.Runtime.Autograd.Gondlin.NN.linear hidDim inDim
      (seedW := seedW2) (seedB := seedB2)
  ]

end Gondlin
end Models
end GraphSpec
end NN
