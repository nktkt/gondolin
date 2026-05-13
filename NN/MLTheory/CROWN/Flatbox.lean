/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Spec.Core.Tensor
public import NN.Runtime.Context

/-!
# Flattened interval bounds (`FlatBox`)

`FlatBox α` is a small container for interval bounds on a *flattened* tensor value.

It is used by the graph-based LiRPA/CROWN development (`NN.MLTheory.CROWN.Graph`) and by some
operator-level transfer rules that operate on flattened vectors (e.g. slice/reduce rules).

`dim` is the flattened size, and `lo`/`hi` are tensors of shape `.dim dim .scalar`.
-/

@[expose] public section


namespace NN.MLTheory.CROWN

open _root_.Spec
open _root_.Spec.Tensor

variable {α : Type} [Context α]

/--
Flattened interval bounds.

`dim` is the flattened size (number of scalar components).
-/
structure FlatBox (α : Type) [Context α] where
  /-- Flattened output dimension. -/
  dim : Nat
  /-- Lower bound vector (shape `.dim dim .scalar`). -/
  lo  : Tensor α (.dim dim .scalar)
  /-- Upper bound vector (shape `.dim dim .scalar`). -/
  hi  : Tensor α (.dim dim .scalar)

namespace FlatBox

/-- Extract the scalar entry at index `i` from a flat vector tensor. -/
def getScalar {n : Nat} (t : Tensor α (.dim n .scalar)) (i : Fin n) : α :=
  match t with
  | .dim f =>
    match f i with
    | .scalar v => v

/--
Componentwise validity of a flat interval box: `lo ≤ hi` for every coordinate.

This is a proof-facing predicate; it is used to state preservation properties of IBP/CROWN box
operators over ordered backends (e.g. `ℝ`).
-/
def Valid [Preorder α] (B : FlatBox α) : Prop :=
  -- Important: `Context α` also provides an `LE α` instance. To keep `Valid` tied to the *order*
  -- coming from `Preorder α` (so we can use `le_rfl`, `le_trans`, etc.), we apply `LE.le`
  -- explicitly with the `Preorder`-provided `LE` instance.
  let inst : Preorder α := inferInstance
  ∀ i : Fin B.dim,
    @LE.le α inst.toLE (getScalar (α := α) B.lo i) (getScalar (α := α) B.hi i)

/--
Build a singleton `FlatBox` from an exact vector tensor `t` (set `lo = hi = t`).
-/
def ofTensor {n : Nat} (t : Tensor α (.dim n .scalar)) : FlatBox α :=
  { dim := n, lo := t, hi := t }

/-- A singleton flat box is always valid (over any preorder). -/
theorem valid_ofTensor [Preorder α] {n : Nat} (t : Tensor α (.dim n .scalar)) :
    (ofTensor (α := α) t).Valid := by
  intro i
  -- After unfolding `Valid`/`ofTensor`, the goal is reflexivity in the `Preorder` order.
  dsimp [Valid, ofTensor]
  exact le_rfl

end FlatBox

end NN.MLTheory.CROWN
