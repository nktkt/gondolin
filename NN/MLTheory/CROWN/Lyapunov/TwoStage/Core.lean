/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Entrypoint.Spec
public import NN.Runtime.Autograd.Gondlin.Functional
public import NN.Tensor.API

/-!
# TwoStage Core

Shared core for the **TwoStage neural-controller / neural-Lyapunov workflows**.

This directory (`NN/MLTheory/CROWN/Lyapunov/TwoStage/`) is the Lean counterpart of the “three
pipeline” workflow in the Gondlin paper (`arXiv:2602.22631`, Figure 7):

- (i) **Python-only**: PyTorch + α/β-CROWN produce numeric bounds; Lean *checks* the resulting
  certificate (trusted boundary = oracle statement).
- (ii) **Hybrid**: Stage-1 training in PyTorch, exported as *float32 bit patterns*; Stage-2
  refinement + the final IBP/CROWN check run inside Gondlin under exact `IEEE32Exec` semantics.
- (iii) **All-in-Lean**: both stages run inside Gondlin under `IEEE32Exec`; the final IBP/CROWN
  check is also in Lean.

This file is shared by (ii) and (iii). It contains:
- the shapes / parameter pack layout for a small controller and a 1-hidden-layer Lyapunov net, and
- the scalar Gondlin `lossProgram` used for both training and verification compilation.

Key point: the *same* Gondlin program is used in two roles:
- **execution/training** (with `α = IEEE32Exec`), and
- **compilation** to the op-tagged verifier IR used by in-repo IBP/CROWN bound propagation.
-/

@[expose] public section


open _root_.Spec
open _root_.Spec.Tensor
open Runtime
open Runtime.Autograd

namespace NN.MLTheory.CROWN.Lyapunov.TwoStage.Core

/-- State dimension for the 2D Lyapunov example. -/
abbrev xDim : Nat := 2
/-- Control dimension for the 2D Lyapunov example. -/
abbrev uDim : Nat := 1

/-- Tensor shape for the state vector `x`. -/
def xShape : Shape := .dim xDim .scalar
/-- Tensor shape for the control vector `u`. -/
def uShape : Shape := .dim uDim .scalar

/-- Parameter shapes for the two-stage controller and Lyapunov network, as a flat list. -/
def paramShapes (width : Nat) : List Shape :=
  [ .dim uDim (.dim xDim .scalar)      -- Wc
  , .dim uDim .scalar                  -- bc
  , .dim width (.dim xDim .scalar)     -- W1
  , .dim width .scalar                 -- b1
  , .dim 1 (.dim width .scalar)        -- W2
  , .dim 1 .scalar                     -- b2
  ]

/-!
Loss program:

  penalty_pos = relu(cV*||x||^2 - V(x))
  penalty_dec = relu(Vdot(x) + cD*V(x))
  loss = penalty_pos + penalty_dec

Where:
  u(x) = scaleU * tanh(Wc x + bc)
  s(x) = w2 · tanh(W1 x + b1) + b2
  V(x) = s(x)^2
  Vdot(x) = ∇V(x) · f(x, u(x))  (van-der-Pol-like)

We compute ∇V analytically (1-hidden-layer tanh + square), so training uses only first-order AD.
-/
def lossProgram (width : Nat) :
    ∀ {β : Type}, [Context β] → [DecidableEq Shape] →
      Gondlin.Program β (paramShapes width ++ [xShape]) Shape.scalar :=
  fun {β} _ _ =>
    fun {m} _ _ =>
      fun wC bC w1 b1 w2 b2 x =>
        (do
          let mu : β := ((1 : Nat) : β)
          let scaleU : β := ((1 : Nat) : β)
          let cV : β := ((1 : Nat) : β) / ((10 : Nat) : β)
          let cD : β := ((1 : Nat) : β) / ((10 : Nat) : β)
          let one : β := ((1 : Nat) : β)
          let two : β := ((2 : Nat) : β)

          -- controller: u = scaleU * tanh(Wc x + bc) ∈ R^1
          let uPre ← Gondlin.linear (m := m) (α := β) (inDim := xDim) (outDim := uDim) wC bC x
          let uT ← Gondlin.tanh (m := m) (α := β) (s := uShape) uPre
          let uVec ← Gondlin.scale (m := m) (α := β) (s := uShape) uT (c := scaleU)
          let u0 ← Gondlin.gatherScalar (m := m) (α := β) (n := uDim) uVec fin0!

          -- Lyapunov: V = (w2 · tanh(W1 x + b1) + b2)^2
          let z1 ← Gondlin.linear (m := m) (α := β) (inDim := xDim) (outDim := width) w1 b1 x
          let h1 ← Gondlin.tanh (m := m) (α := β) (s := .dim width .scalar) z1
          let sVec ← Gondlin.linear (m := m) (α := β) (inDim := width) (outDim := 1) w2 b2 h1
          let s0 ← Gondlin.gatherScalar (m := m) (α := β) (n := 1) sVec fin0!
          let V ← Gondlin.mul (m := m) (α := β) (s := Shape.scalar) s0 s0

          -- gradV = 2*s0 * W1^T (w2Row ⊙ (1 - tanh(z1)^2))
          let w2Row ← Gondlin.gatherRow (m := m) (α := β) (rows := 1) (cols := width) w2 fin0!
          let h1Sq ← Gondlin.mul (m := m) (α := β) (s := .dim width .scalar) h1 h1
          let oneS ← Gondlin.const (m := m) (α := β) (s := Shape.scalar) (Tensor.scalar one)
          let oneW ← Gondlin.broadcastTo (m := m) (α := β) (s₁ := Shape.scalar) (s₂ := .dim width
            .scalar)
            (Shape.CanBroadcastTo.scalar_to_any (.dim width .scalar)) oneS
          let dh ← Gondlin.sub (m := m) (α := β) (s := .dim width .scalar) oneW h1Sq
          let gHidden ← Gondlin.mul (m := m) (α := β) (s := .dim width .scalar) w2Row dh

          let gHiddenM ← Gondlin.reshape (m := m) (α := β)
            (s₁ := .dim width .scalar) (s₂ := .dim width (.dim 1 .scalar)) gHidden (by simp
              [_root_.Spec.Shape.size])
          let w1T ← Gondlin.transpose2d (m := m) (α := β) (mDim := width) (nDim := xDim) w1
          let dsM ← Gondlin.matmul (m := m) (α := β) (mDim := xDim) (nDim := width) (pDim := 1)
            w1T gHiddenM
          let ds ← Gondlin.reshape (m := m) (α := β)
            (s₁ := .dim xDim (.dim 1 .scalar)) (s₂ := xShape) dsM (by
              simp [xShape, _root_.Spec.Shape.size])

          let k ← Gondlin.scale (m := m) (α := β) (s := Shape.scalar) s0 (c := two)
          let kV ← Gondlin.broadcastTo (m := m) (α := β) (s₁ := Shape.scalar) (s₂ := xShape)
            (Shape.CanBroadcastTo.scalar_to_any xShape) k
          let gradV ← Gondlin.mul (m := m) (α := β) (s := xShape) kV ds

          -- dynamics f(x,u): dx1 = x2, dx2 = -x1 + mu*(1-x1^2)*x2 + u
          let x1 ← Gondlin.gatherScalar (m := m) (α := β) (n := xDim) x fin0!
          let x2 ← Gondlin.gatherScalar (m := m) (α := β) (n := xDim) x fin1!
          let x1Sq0 ← Gondlin.mul (m := m) (α := β) (s := Shape.scalar) x1 x1
          let oneMinus ← Gondlin.sub (m := m) (α := β) (s := Shape.scalar) oneS x1Sq0
          let term0 ← Gondlin.mul (m := m) (α := β) (s := Shape.scalar) oneMinus x2
          let term ← Gondlin.scale (m := m) (α := β) (s := Shape.scalar) term0 (c := mu)
          let negx1 ← Gondlin.scale (m := m) (α := β) (s := Shape.scalar) x1 (c := (-one))
          let dx2pre ← Gondlin.add (m := m) (α := β) (s := Shape.scalar) negx1 term
          let dx2 ← Gondlin.add (m := m) (α := β) (s := Shape.scalar) dx2pre u0

          let x2V ← Gondlin.reshape (m := m) (α := β) (s₁ := Shape.scalar) (s₂ := .dim 1 .scalar)
            x2 (by simp [_root_.Spec.Shape.size])
          let dx2V ← Gondlin.reshape (m := m) (α := β) (s₁ := Shape.scalar) (s₂ := .dim 1 .scalar)
            dx2 (by simp [_root_.Spec.Shape.size])
          let fVec ← Gondlin.concatVectors (m := m) (α := β) (nDim := 1) (mDim := 1) x2V dx2V

          let prod ← Gondlin.mul (m := m) (α := β) (s := xShape) gradV fVec
          let Vdot ← Gondlin.sum (m := m) (α := β) (s := xShape) prod

          let xSqV ← Gondlin.mul (m := m) (α := β) (s := xShape) x x
          let xSq ← Gondlin.sum (m := m) (α := β) (s := xShape) xSqV

          -- penalties
          let posScaled ← Gondlin.scale (m := m) (α := β) (s := Shape.scalar) xSq (c := cV)
          let posExpr ← Gondlin.sub (m := m) (α := β) (s := Shape.scalar) posScaled V
          let posPenalty ← Gondlin.relu (m := m) (α := β) (s := Shape.scalar) posExpr

          let decScaled ← Gondlin.scale (m := m) (α := β) (s := Shape.scalar) V (c := cD)
          let decExpr ← Gondlin.add (m := m) (α := β) (s := Shape.scalar) Vdot decScaled
          let decPenalty ← Gondlin.relu (m := m) (α := β) (s := Shape.scalar) decExpr
          Gondlin.add (m := m) (α := β) (s := Shape.scalar) posPenalty decPenalty
          : m (Gondlin.RefTy (m := m) (α := β) Shape.scalar))

end NN.MLTheory.CROWN.Lyapunov.TwoStage.Core
