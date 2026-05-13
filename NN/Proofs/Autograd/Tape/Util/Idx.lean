/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Proofs.Autograd.Tape.Core.Soundness

/-!
# Idx

Utilities for working with typed context indices (`Idx`) in tape-style graphs.

Many graph-construction proofs need two basic operations:
- **weaken** an index when the context is extended by more intermediates; and
- refer to the **last** element of an appended shape list (`Γ ++ ss ++ [τ]`).

We centralize them here to avoid repeating the same list-arithmetic boilerplate in every op graph
(LayerNorm, BatchNorm, attention, …).
-/

@[expose] public section


namespace Proofs
namespace Autograd

open Spec

namespace Idx

private lemma get_append_last {α : Type} (l : List α) (a : α) :
    (l ++ [a]).get ⟨l.length, by simp⟩ = a := by
  induction l with
  | nil => simp
  | cons _ xs ih =>
      simp [List.length]

private lemma get_append_left {α : Type} (l₁ l₂ : List α) (i : Fin l₁.length) :
    (l₁ ++ l₂).get ⟨i.1, by
        -- `i.1 < l₁.length` and `l₁.length ≤ l₁.length + l₂.length`.
        simpa [List.length_append] using
          Nat.lt_of_lt_of_le i.2 (Nat.le_add_right l₁.length l₂.length)⟩ =
      l₁.get i := by
  induction l₁ with
  | nil =>
      cases i with
      | mk _ hk => cases hk
  | cons _ tl ih =>
      classical
      cases i using Fin.cases with
      | zero =>
          simp
      | succ i =>
          simp

/--
Weaken a typed index when the context is extended by appending more shapes.

If `idx : Idx Γ s`, then `weaken idx rest : Idx (Γ ++ rest) s`.
-/
def weaken {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (rest : List Shape) :
    Idx (Γ ++ rest) s :=
  let i' : Fin (Γ ++ rest).length := ⟨idx.i.1, by
    simpa [List.length_append] using
      Nat.lt_of_lt_of_le idx.i.2 (Nat.le_add_right Γ.length rest.length)⟩
  have hget : (Γ ++ rest).get i' = s := by
    have hleft := get_append_left (l₁ := Γ) (l₂ := rest) (i := idx.i)
    have hi' :
        (⟨idx.i.1, by
          simpa [List.length_append] using
            Nat.lt_of_lt_of_le idx.i.2 (Nat.le_add_right Γ.length rest.length)⟩ :
          Fin (Γ ++ rest).length) = i' := by
      ext; rfl
    simpa [hi'] using (hleft.trans idx.h)
  ⟨i', hget⟩

/--
Typed index for the last element of an appended shape list.

`Idx.last` is the canonical index of `τ` in `Γ ++ ss ++ [τ]`.
-/
def last {Γ : List Shape} {ss : List Shape} {τ : Shape} : Idx (Γ ++ ss ++ [τ]) τ :=
  ⟨⟨(Γ ++ ss).length, by
      simp [List.length_append]⟩, by
    simp [List.append_assoc]⟩

end Idx

end Autograd
end Proofs
