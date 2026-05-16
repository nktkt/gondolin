/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN
public import NN.Spec.Models.Mlp
public import NN.Tests.Runtime.Floats.Utils
public import Std

/-!
# GondolinSpecMlpEquivSmoke

Smoke test: Gondolin MLP forward agrees with Spec MLP forward.

Goal: make the "Spec vs Gondolin" relationship concrete with an executable check:
given the *same* initialized parameters, both front-ends produce the same output tensor.

This is not a performance test; it is a regression guard for:
- parameter ordering conventions (W,b pairs),
- shape conventions (Vec/Mat layout),
- and the meaning of `Linear → ReLU → Linear`.
-/

@[expose] public section


open Spec
open Tensor
open NN.API
open Tests.Floats.Utils

namespace Tests
namespace Floats
namespace GondolinSpecMLPEquivSmoke

def run : IO Unit := do
  IO.println "gondolin_spec_mlp_equiv_smoke: begin"

  let inDim : Nat := 2
  let hidDim : Nat := 3
  let outDim : Nat := 1
  let xShape : Shape := NN.Tensor.Shape.Vec inDim
  let yShape : Shape := NN.Tensor.Shape.Vec outDim

  -- Gondolin MLP (deterministic init via explicit seeds).
  let model :=
    NN.GraphSpec.Models.Gondolin.mlp
      (inDim := inDim) (hidDim := hidDim) (outDim := outDim)
      (seedW1 := 0) (seedB1 := 1) (seedW2 := 2) (seedB2 := 3)

  -- One input vector.
  let x : Tensor Float xShape :=
    Tensor.dim (fun i => Tensor.scalar ([0.5, 0.8][i.val]!))

  -- Extract Gondolin parameters and reinterpret them as Spec `LinearSpec`s.
  let ps := Runtime.Autograd.Gondolin.NN.Seq.initParams (m := model)
  let (w1, b1, w2, b2) :=
    match ps with
    | .cons w1 (.cons b1 (.cons w2 (.cons b2 .nil))) => (w1, b1, w2, b2)

  let l1 : Spec.LinearSpec Float inDim hidDim := { weights := w1, bias := b1 }
  let l2 : Spec.LinearSpec Float hidDim outDim := { weights := w2, bias := b2 }

  -- Spec forward reference.
  let ySpec : Tensor Float yShape := Examples.mlpForward (α := Float) l1 l2 x

  -- Gondolin forward reference (compiled-out evaluation of the Gondolin program).
  let compiled ← Gondolin.Autodiff.compileOut (α := Float)
    (paramShapes := Runtime.Autograd.Gondolin.NN.Seq.paramShapes model)
    (inputShapes := [xShape]) (τ := yShape)
    (fun {β} _ _ => Runtime.Autograd.Gondolin.NN.Seq.program (model := model) (α := β))

  let args : Gondolin.TList Float (Runtime.Autograd.Gondolin.NN.Seq.paramShapes model ++ [xShape])
    :=
    .cons w1 (.cons b1 (.cons w2 (.cons b2 (.cons x .nil))))

  let yTorch : Tensor Float yShape :=
    _root_.Runtime.Autograd.Torch.CompiledOut.forward compiled args

  -- Since `outDim = 1`, check the single coordinate. (Kept structured so it scales to `outDim >
  -- 1`.)
  for i in List.finRange outDim do
    assertApprox s!"mlp forward[{i.val}] spec/gondolin" (vecVal ySpec i) (vecVal yTorch i) 1e-6

  IO.println "gondolin_spec_mlp_equiv_smoke: ok"

end GondolinSpecMLPEquivSmoke
end Floats
end Tests
