/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.GraphSpec.Models.Resnet18
import Mathlib.Algebra.Order.Algebra

/-!
# Gondlin-executable model: ResNet-18 (GraphSpec.DAG-backed)

This is the executable-facing wrapper for `NN.GraphSpec.Models.ResNet18`.

Important design point:
- Gondlin `NN.Seq` is sequential, so it cannot directly represent residual DAGs.
- GraphSpec.DAG *can* represent them, and can compile to a backend-generic Gondlin program.

So we expose:
- `resnet18Model`: the DAG `Model` (parameters + typed body),
- `resnet18Program`: a `Gondlin.Program` you can run on eager/compiled backends,
- `resnet18InitParams`: deterministic Float initialization matching the parameter layout.
-/

@[expose] public section


namespace NN
namespace GraphSpec
namespace Models
namespace Gondlin

open Spec
open NN.Tensor

/-- The ResNet-18 model as a `GraphSpec.DAG.Model` (typed residual graph). -/
def resnet18Model
    (inC h w numClasses : Nat)
    (h_inC : inC > 0) (h_h : h > 0) (h_w : w > 0) (h_cls : numClasses > 0) :
    _root_.NN.GraphSpec.DAG.Model
      (ps := _root_.NN.GraphSpec.Models.ResNet18.params inC numClasses)
      (ins := [Shape.CHW inC h w])
      (τ := Shape.Vec numClasses) :=
  _root_.NN.GraphSpec.Models.ResNet18.model
    (inC := inC) (h := h) (w := w) (numClasses := numClasses)
    h_inC h_h h_w h_cls

/-- Compile `resnet18Model` into a backend-polymorphic Gondlin program.

You can run this on the eager backend or record it into the compiled backend.
-/
def resnet18Program
    (inC h w numClasses : Nat)
    (h_inC : inC > 0) (h_h : h > 0) (h_w : w > 0) (h_cls : numClasses > 0)
    {α : Type 0} [Context α] [DecidableEq Spec.Shape] :
    _root_.Runtime.Autograd.Gondlin.Program α
      (_root_.NN.GraphSpec.Models.ResNet18.params inC numClasses ++ [Shape.CHW inC h w])
      (Shape.Vec numClasses) :=
  (_root_.NN.GraphSpec.DAG.Model.torchProgram (m := resnet18Model inC h w numClasses h_inC h_h h_w
    h_cls) (α := α))

/-- Deterministic Float initialization for the ResNet-18 parameter list. -/
def resnet18InitParams
    (inC h w numClasses : Nat)
    (h_inC : inC > 0) (h_h : h > 0) (h_w : w > 0) (h_cls : numClasses > 0) :
    _root_.Runtime.Autograd.Torch.TList Float
      (_root_.NN.GraphSpec.Models.ResNet18.params inC numClasses) :=
  (resnet18Model inC h w numClasses h_inC h_h h_w h_cls).initParams

end Gondlin
end Models
end GraphSpec
end NN
