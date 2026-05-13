/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Proofs.Autograd.Tape.Nodes.Context

/-!
# Elementwise tape nodes

Reusable `NodeFDerivCorrect` wrappers for scalar functions lifted pointwise to tensors, including
common activations such as ReLU, sigmoid, tanh, SiLU, GELU, ELU, and safe differentiable variants.
-/

@[expose] public section

namespace Proofs
namespace Autograd

open Spec
open Tensor

noncomputable section

open scoped BigOperators

namespace TapeNodes


/-- `CtxVec.get` specialized to vector shapes. -/
def getVec {Γ : List Shape} {n : Nat} (idx : Idx Γ (.dim n .scalar)) (x : CtxVec Γ) : Vec n :=
  castVec (by
    simp [Shape.size] : Shape.size (.dim n .scalar) = n) (CtxVec.get (Γ := Γ) (s := .dim n .scalar)
      idx x)

/-- `CtxVec.getCLM` specialized to vector shapes `.dim n .scalar`. -/
def getVecCLM {Γ : List Shape} {n : Nat} (idx : Idx Γ (.dim n .scalar)) : CtxVec Γ →L[ℝ] Vec n :=
  (Graph.castCLM (h := (by simp [Shape.size] : Shape.size (.dim n .scalar) = n))).comp
    (CtxVec.getCLM (Γ := Γ) (s := .dim n .scalar) idx)

@[simp] lemma getVecCLM_apply {Γ : List Shape} {n : Nat} (idx : Idx Γ (.dim n .scalar)) (x : CtxVec
  Γ) :
    getVecCLM (Γ := Γ) (n := n) idx x = getVec (Γ := Γ) (n := n) idx x := by
  simp [getVecCLM, getVec, CtxVec.getCLM_apply, Graph.castCLM]

@[simp] lemma getCLM_apply_ofLp {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (x : CtxVec Γ)
    (i : Fin (Shape.size s)) :
    ((CtxVec.getCLM (Γ := Γ) (s := s) idx) x).ofLp i = (CtxVec.get (Γ := Γ) (s := s) idx x).ofLp i
      := by
  simp

/-- Inject a `Vec n` into a vectorized context at `idx` (fills other blocks with zeros). -/
def singleVec {Γ : List Shape} {n : Nat} (idx : Idx Γ (.dim n .scalar)) (v : Vec n) : CtxVec Γ :=
  CtxVec.single (Γ := Γ) (s := .dim n .scalar) idx
    (castVec (by simp [Shape.size] : Shape.size (.dim n .scalar) = n).symm v)

@[simp] lemma inner_getVec_singleVec {Γ : List Shape} {n : Nat} (idx : Idx Γ (.dim n .scalar))
    (x : CtxVec Γ) (v : Vec n) :
    inner ℝ x (singleVec (Γ := Γ) (n := n) idx v) = inner ℝ (getVec (Γ := Γ) (n := n) idx x) v := by
  classical
  let hsz : Shape.size (.dim n .scalar) = n := by simp [Shape.size]
  -- reduce to `CtxVec.inner_get_single` plus cast isometries
  have h :=
    (CtxVec.inner_get_single (Γ := Γ) (s := .dim n .scalar) idx x (castVec hsz.symm v))
  -- rewrite both sides to `getVec`/`singleVec`
  -- RHS: move casts across `inner`
  have hcast :
      inner ℝ (castVec hsz (CtxVec.get (Γ := Γ) (s := .dim n .scalar) idx x)) v =
        inner ℝ (CtxVec.get (Γ := Γ) (s := .dim n .scalar) idx x) (castVec hsz.symm v) := by
    -- same trick as in `CtxVec.inner_get_single`
    have hv : castVec hsz (castVec hsz.symm v) = v := by
      simp
    calc
      inner ℝ (castVec hsz (CtxVec.get (Γ := Γ) (s := .dim n .scalar) idx x)) v
          = inner ℝ (castVec hsz (CtxVec.get (Γ := Γ) (s := .dim n .scalar) idx x)) (castVec hsz
            (castVec hsz.symm v)) := by
              simp [hv]
      _ = inner ℝ (CtxVec.get (Γ := Γ) (s := .dim n .scalar) idx x) (castVec hsz.symm v) := by
            simpa using
              (inner_castVec_castVec (h := hsz) (x := CtxVec.get (Γ := Γ) (s := .dim n .scalar) idx
                x) (y := castVec hsz.symm v))
  -- finish
  simpa [singleVec, getVec, hcast] using h

-- ---------------------------------------------------------------------------
-- Generic elementwise nodes on flattened tensors
-- ---------------------------------------------------------------------------

/-- Elementwise node: apply a scalar function pointwise on a context entry. -/
def elemwise {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (f f' : ℝ → ℝ) : Node Γ s :=
  let n : Nat := Shape.size s
  Node.ofVec (Γ := Γ) (τ := s)
    (f := fun xV =>
      vecOfFun (n := n) (fun i : Fin n => f (CtxVec.get (Γ := Γ) (s := s) idx xV i)))
    (jvp := fun xV dxV =>
      vecOfFun (n := n) (fun i : Fin n =>
        (CtxVec.get (Γ := Γ) (s := s) idx dxV i) * f' (CtxVec.get (Γ := Γ) (s := s) idx xV i)))
    (vjp := fun xV δ =>
      CtxVec.single (Γ := Γ) (s := s) idx
        (vecOfFun (n := n) (fun i : Fin n => δ i * f' (CtxVec.get (Γ := Γ) (s := s) idx xV i))))
    (correct_inner := by
      intro xV dxV δ
      classical
      -- First use the context adjointness, then expand both inners.
      simp [CtxVec.inner_get_single, vecOfFun]
      simp [inner_eq_sum_mul, mul_assoc, mul_comm]
      rfl)

/-- Analytic correctness for `elemwise` nodes from a scalar `HasDerivAt` hypothesis. -/
def elemwiseFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (f f' : ℝ → ℝ)
    (hf : ∀ z, HasDerivAt f (f' z) z) :
    NodeFDerivCorrect (elemwise (Γ := Γ) (s := s) idx f f') :=
by
  classical
  let n : Nat := Shape.size s
  refine
    { deriv := fun xV =>
        (elemwiseDerivCLM (n := n) f' (CtxVec.get (Γ := Γ) (s := s) idx xV)).comp
          (CtxVec.getCLM (Γ := Γ) (s := s) idx)
      hasFDerivAt := ?_
      jvp_eq := ?_ }
  · intro xV
    have hget :
        HasFDerivAt (fun x : CtxVec Γ => CtxVec.get (Γ := Γ) (s := s) idx x)
          (CtxVec.getCLM (Γ := Γ) (s := s) idx) xV := by
      have h := (CtxVec.getCLM (Γ := Γ) (s := s) idx).hasFDerivAt (x := xV)
      have hfun :
          (fun x : CtxVec Γ => CtxVec.get (Γ := Γ) (s := s) idx x)
            =
          (fun x : CtxVec Γ => (CtxVec.getCLM (Γ := Γ) (s := s) idx) x) := by
        funext x
        exact (CtxVec.getCLM_apply (Γ := Γ) (s := s) idx x).symm
      exact h.congr_of_eventuallyEq hfun.eventuallyEq
    have helem :
        HasFDerivAt (elemwiseVec (n := n) f) (elemwiseDerivCLM (n := n) f' (CtxVec.get (Γ := Γ) (s
          := s) idx xV))
          (CtxVec.get (Γ := Γ) (s := s) idx xV) :=
      hasFDerivAt_elemwiseVec (n := n) (x := CtxVec.get (Γ := Γ) (s := s) idx xV) (f := f) (f' :=
        f') hf
    have hcomp := helem.comp xV hget
    -- rewrite the forward function to match `elemwiseVec ∘ get`
    simpa [elemwise, Node.forwardVec_ofVec, elemwiseVec, n, ContinuousLinearMap.comp_apply] using
      hcomp
  · intro xV dxV
    ext i
    simp [elemwise, Node.jvpVec_ofVec, elemwiseDerivCLM, ContinuousLinearMap.comp_apply, n,
      CtxVec.getCLM_apply, vecOfFun]

/-- Pointwise analytic correctness for `elemwise` nodes from a coordinatewise `HasDerivAt`
  hypothesis. -/
def elemwiseFderivAt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (f f' : ℝ → ℝ) (xV : CtxVec Γ)
    (hf : ∀ i : Fin (Shape.size s),
      HasDerivAt f (f' (CtxVec.get (Γ := Γ) (s := s) idx xV i)) (CtxVec.get (Γ := Γ) (s := s) idx xV
        i)) :
    NodeFDerivCorrectAt (elemwise (Γ := Γ) (s := s) idx f f') xV :=
by
  classical
  let n : Nat := Shape.size s
  refine
    { deriv :=
        (elemwiseDerivCLM (n := n) f' (CtxVec.get (Γ := Γ) (s := s) idx xV)).comp
          (CtxVec.getCLM (Γ := Γ) (s := s) idx)
      hasFDerivAt := ?_
      jvp_eq := ?_ }
  · have hget :
        HasFDerivAt (fun x : CtxVec Γ => CtxVec.get (Γ := Γ) (s := s) idx x)
          (CtxVec.getCLM (Γ := Γ) (s := s) idx) xV := by
      have h := (CtxVec.getCLM (Γ := Γ) (s := s) idx).hasFDerivAt (x := xV)
      have hfun :
          (fun x : CtxVec Γ => CtxVec.get (Γ := Γ) (s := s) idx x)
            =
          (fun x : CtxVec Γ => (CtxVec.getCLM (Γ := Γ) (s := s) idx) x) := by
        funext x
        exact (CtxVec.getCLM_apply (Γ := Γ) (s := s) idx x).symm
      exact h.congr_of_eventuallyEq hfun.eventuallyEq
    have helem :
        HasFDerivAt (elemwiseVec (n := n) f) (elemwiseDerivCLM (n := n) f' (CtxVec.get (Γ := Γ) (s
          := s) idx xV))
          (CtxVec.get (Γ := Γ) (s := s) idx xV) :=
      hasFDerivAt_elemwiseVec_at (n := n) (x := CtxVec.get (Γ := Γ) (s := s) idx xV) (f := f) (f' :=
        f') hf
    have hcomp := helem.comp xV hget
    simpa [elemwise, Node.forwardVec_ofVec, elemwiseVec, n, ContinuousLinearMap.comp_apply] using
      hcomp
  · intro dxV
    ext i
    simp [elemwise, Node.jvpVec_ofVec, elemwiseDerivCLM, ContinuousLinearMap.comp_apply, n,
      CtxVec.getCLM_apply,
      vecOfFun]

/-- Runtime `relu` node (elementwise; nondifferentiable at zero). -/
def relu {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.reluSpec Activation.Math.reluDerivSpec

/-- Pointwise `NodeFDerivCorrectAt` for `relu` under the assumption that inputs are nonzero. -/
def reluFderivAt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (xV : CtxVec Γ)
    (hx : ∀ i : Fin (Shape.size s), CtxVec.get (Γ := Γ) (s := s) idx xV i ≠ 0) :
    NodeFDerivCorrectAt (relu (Γ := Γ) (s := s) idx) xV :=
  elemwiseFderivAt (Γ := Γ) (s := s) idx
    Activation.Math.reluSpec Activation.Math.reluDerivSpec xV
    (fun i => Proofs.relu_deriv_correct (x := CtxVec.get (Γ := Γ) (s := s) idx xV i) (h := hx i))

/-- Runtime `abs` node (elementwise; nondifferentiable at zero). -/
def abs {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx (fun x : ℝ => |x|) (fun x => (SignType.sign x : ℝ))

/-- Pointwise `NodeFDerivCorrectAt` for `abs` under the assumption that inputs are nonzero. -/
def absFderivAt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (xV : CtxVec Γ)
    (hx : ∀ i : Fin (Shape.size s), CtxVec.get (Γ := Γ) (s := s) idx xV i ≠ 0) :
    NodeFDerivCorrectAt (abs (Γ := Γ) (s := s) idx) xV :=
  elemwiseFderivAt (Γ := Γ) (s := s) idx (fun x : ℝ => |x|) (fun x => (SignType.sign x : ℝ)) xV
    (fun i => by simpa using (hasDerivAt_abs (hx i)))

/-- Runtime `log` node (elementwise; differentiable only away from zero). -/
def log {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Real.log (fun x => x⁻¹)

/-- Pointwise `NodeFDerivCorrectAt` for `log` under the assumption that inputs are nonzero. -/
def logFderivAt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (xV : CtxVec Γ)
    (hx : ∀ i : Fin (Shape.size s), CtxVec.get (Γ := Γ) (s := s) idx xV i ≠ 0) :
    NodeFDerivCorrectAt (log (Γ := Γ) (s := s) idx) xV :=
  elemwiseFderivAt (Γ := Γ) (s := s) idx Real.log (fun x => x⁻¹) xV
    (fun i => Real.hasDerivAt_log (hx i))

/-- Elementwise inverse node (differentiable only away from zero). -/
def inv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx (fun x => x⁻¹) (fun x => -((x ^ 2)⁻¹))

/-- Pointwise `NodeFDerivCorrectAt` for `inv` under the assumption that inputs are nonzero. -/
def invFderivAt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (xV : CtxVec Γ)
    (hx : ∀ i : Fin (Shape.size s), CtxVec.get (Γ := Γ) (s := s) idx xV i ≠ 0) :
    NodeFDerivCorrectAt (inv (Γ := Γ) (s := s) idx) xV :=
  elemwiseFderivAt (Γ := Γ) (s := s) idx (fun x => x⁻¹) (fun x => -((x ^ 2)⁻¹)) xV
    (fun i => by simpa using (hasDerivAt_inv (hx i)))

/-- Derivative of the scalar function `y ↦ sqrt (max y 0)` at positive points. -/
lemma hasDerivAt_sqrt_clamp_of_pos {x : ℝ} (hx : 0 < x) :
    HasDerivAt (fun y : ℝ => Real.sqrt (max y 0)) (1 / (2 * Real.sqrt x)) x := by
  have hpos : ∀ᶠ y in nhds x, 0 < y := by
    -- `Ioi 0` is an open neighborhood of any positive `x`.
    have hmem : Set.Ioi (0 : ℝ) ∈ nhds x := isOpen_Ioi.mem_nhds hx
    have hpos' : ∀ᶠ y in nhds x, y ∈ Set.Ioi (0 : ℝ) := by
      simpa using hmem
    simpa [Set.mem_Ioi] using hpos'
  have heq :
      (fun y : ℝ => Real.sqrt (max y 0)) =ᶠ[nhds x] fun y : ℝ => Real.sqrt y := by
    filter_upwards [hpos] with y hy
    simp [max_eq_left (le_of_lt hy)]
  have hs : HasDerivAt (fun y : ℝ => Real.sqrt y) (1 / (2 * Real.sqrt x)) x := by
    -- `Real.hasDerivAt_sqrt` expects `x ≠ 0`.
    simpa using (Real.hasDerivAt_sqrt (ne_of_gt hx))
  -- transport across the local equality `max y 0 = y` near positive `x`
  exact hs.congr_of_eventuallyEq heq

/-- Elementwise "clamped sqrt": `sqrt (max x 0)` (differentiable on `x > 0`). -/
def sqrtClamp {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx (fun x => Real.sqrt (max x 0)) (fun x => 1 / (2 * Real.sqrt x))

/-- Pointwise `NodeFDerivCorrectAt` for `sqrt_clamp` under the assumption that inputs are strictly
  positive. -/
def sqrtClampFderivAt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (xV : CtxVec Γ)
    (hx : ∀ i : Fin (Shape.size s), 0 < CtxVec.get (Γ := Γ) (s := s) idx xV i) :
    NodeFDerivCorrectAt (sqrtClamp (Γ := Γ) (s := s) idx) xV :=
  elemwiseFderivAt (Γ := Γ) (s := s) idx
    (fun x => Real.sqrt (max x 0)) (fun x => 1 / (2 * Real.sqrt x)) xV
    (fun i => hasDerivAt_sqrt_clamp_of_pos (hx i))

/-- Runtime `sqrt` node (elementwise; nondifferentiable at zero). -/
def sqrt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Real.sqrt (fun x => 1 / (2 * Real.sqrt x))

/-- Pointwise `NodeFDerivCorrectAt` for `sqrt` under the assumption that inputs are nonzero. -/
def sqrtFderivAt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (xV : CtxVec Γ)
    (hx : ∀ i : Fin (Shape.size s), CtxVec.get (Γ := Γ) (s := s) idx xV i ≠ 0) :
    NodeFDerivCorrectAt (sqrt (Γ := Γ) (s := s) idx) xV :=
  elemwiseFderivAt (Γ := Γ) (s := s) idx Real.sqrt (fun x => 1 / (2 * Real.sqrt x)) xV
    (fun i => by simpa using (Real.hasDerivAt_sqrt (hx i)))

/-- Runtime scalar logistic node, applied elementwise.

Vector and matrix softmax use the dedicated last-axis softmax nodes below; this node is the
one-dimensional logistic map used by scalar activations. -/
def logistic {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.logisticSpec Activation.Math.logisticDerivSpec

/-- Global `NodeFDerivCorrect` for `logistic` (uses the scalar derivative lemma). -/
def logisticFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (logistic (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    Activation.Math.logisticSpec Activation.Math.logisticDerivSpec
    (fun z => Proofs.logistic_deriv_correct (x := z))

/-- Runtime `sigmoid` node (elementwise). -/
def sigmoid {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.sigmoidSpec Activation.Math.sigmoidDerivSpec

/-- Global `NodeFDerivCorrect` for `sigmoid`. -/
def sigmoidFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (sigmoid (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    Activation.Math.sigmoidSpec Activation.Math.sigmoidDerivSpec
    (fun z => Proofs.sigmoid_deriv_correct (x := z))

/-- Runtime `tanh` node (elementwise). -/
def tanh {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.tanhSpec Activation.Math.tanhDerivSpec

/-- Global `NodeFDerivCorrect` for `tanh`. -/
def tanhFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (tanh (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    Activation.Math.tanhSpec Activation.Math.tanhDerivSpec
    (fun z => Proofs.tanh_deriv_correct (x := z))

/-- Runtime `softplus` node (elementwise, smooth ReLU surrogate). -/
def softplus {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.softplusSpec Activation.Math.softplusDerivSpec

/-- Global `NodeFDerivCorrect` for `softplus`. -/
def softplusFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (softplus (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    Activation.Math.softplusSpec Activation.Math.softplusDerivSpec
    (fun z => Proofs.softplus_deriv_correct (x := z))

/-- Runtime `silu` node (elementwise). -/
def silu {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.swishSpec Activation.Math.swishDerivSpec

/-- Global `NodeFDerivCorrect` for SiLU. -/
def siluFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (silu (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    Activation.Math.swishSpec Activation.Math.swishDerivSpec
    (fun z => Proofs.silu_deriv_correct (x := z))

/-- Runtime tanh-approximate `gelu` node (elementwise). -/
def gelu {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.geluSpec Activation.Math.geluDerivSpec

/-- Global `NodeFDerivCorrect` for tanh-approximate GELU. -/
def geluFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (gelu (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    Activation.Math.geluSpec Activation.Math.geluDerivSpec
    (fun z => Proofs.gelu_deriv_correct (x := z))

/-- Runtime `safe_log` node (elementwise, always-defined log surrogate). -/
def safeLog {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (ε : ℝ) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx
    (fun x => Activation.Math.safeLogSpec (α := ℝ) x ε)
    (fun x => Activation.Math.safeLogDerivSpec (α := ℝ) x ε)

/-- Global `NodeFDerivCorrect` for `safe_log` (requires `0 < ε`). -/
def safeLogFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (ε : ℝ) (hε : 0 < ε) :
    NodeFDerivCorrect (safeLog (Γ := Γ) (s := s) idx ε) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    (fun x => Activation.Math.safeLogSpec (α := ℝ) x ε)
    (fun x => Activation.Math.safeLogDerivSpec (α := ℝ) x ε)
    (fun z => Proofs.safe_log_deriv_correct (x := z) (ε := ε) hε)

/-- Runtime `smooth_abs` node (elementwise, smooth abs surrogate). -/
def smoothAbs {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (ε : ℝ) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx
    (fun x => Activation.Math.smoothAbsSpec (α := ℝ) x ε)
    (fun x => Activation.Math.smoothAbsDerivSpec (α := ℝ) x ε)

/-- Global `NodeFDerivCorrect` for `smooth_abs` (requires `0 < ε`). -/
def smoothAbsFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (ε : ℝ) (hε : 0 < ε) :
    NodeFDerivCorrect (smoothAbs (Γ := Γ) (s := s) idx ε) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    (fun x => Activation.Math.smoothAbsSpec (α := ℝ) x ε)
    (fun x => Activation.Math.smoothAbsDerivSpec (α := ℝ) x ε)
    (fun z => Proofs.smooth_abs_deriv_correct (x := z) (ε := ε) hε)

/-- Runtime `exp` node (elementwise). -/
def exp {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Real.exp Real.exp

/-- Global `NodeFDerivCorrect` instance for the elementwise exponential. -/
def expFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (exp (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx Real.exp Real.exp (fun z => Real.hasDerivAt_exp z)

/-- Runtime `sinh` node (elementwise). -/
def sinh {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.sinhSpec Activation.Math.sinhDerivSpec

/-- Global `NodeFDerivCorrect` for elementwise hyperbolic sine. -/
def sinhFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (sinh (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    Activation.Math.sinhSpec Activation.Math.sinhDerivSpec
    (fun z => Proofs.sinh_deriv_correct (x := z))

/-- Runtime `cosh` node (elementwise). -/
def cosh {Γ : List Shape} {s : Shape} (idx : Idx Γ s) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx Activation.Math.coshSpec Activation.Math.coshDerivSpec

/-- Global `NodeFDerivCorrect` for elementwise hyperbolic cosine. -/
def coshFderiv {Γ : List Shape} {s : Shape} (idx : Idx Γ s) :
    NodeFDerivCorrect (cosh (Γ := Γ) (s := s) idx) :=
  elemwiseFderiv (Γ := Γ) (s := s) idx
    Activation.Math.coshSpec Activation.Math.coshDerivSpec
    (fun z => Proofs.cosh_deriv_correct (x := z))

/-- Runtime `elu` node (elementwise; nondifferentiable at zero unless `alpha = 1`). -/
def elu {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (alpha : ℝ) : Node Γ s :=
  elemwise (Γ := Γ) (s := s) idx
    (fun x => Activation.Math.eluSpec x alpha)
    (fun x => Activation.Math.eluDerivSpec x alpha)

/--
Pointwise `NodeFDerivCorrectAt` for ELU under the usual no-coordinate-at-the-kink assumption.

For arbitrary `alpha`, ELU has left derivative `alpha` and right derivative `1` at zero. Keeping the
hypothesis here avoids baking PyTorch's subgradient convention into a mathematical derivative
theorem.
-/
def eluFderivAt {Γ : List Shape} {s : Shape} (idx : Idx Γ s) (alpha : ℝ) (xV : CtxVec Γ)
    (hx : ∀ i, CtxVec.get (Γ := Γ) (s := s) idx xV i ≠ 0) :
    NodeFDerivCorrectAt (elu (Γ := Γ) (s := s) idx alpha) xV :=
  elemwiseFderivAt (Γ := Γ) (s := s) idx
    (fun x => Activation.Math.eluSpec x alpha)
    (fun x => Activation.Math.eluDerivSpec x alpha)
    xV
    (fun i => Proofs.elu_deriv_correct
      (x := CtxVec.get (Γ := Γ) (s := s) idx xV i) (α := alpha) (h := hx i))

/-- Unary node applying an analytically-correct `OpSpec` at a context index. -/
def unaryOp {Γ : List Shape} {inDim outDim : Nat}
    (idx : Idx Γ (.dim inDim .scalar))
    (C : OpSpecFDerivCorrect inDim outDim) : Node Γ (.dim outDim .scalar) :=
  let hOut : Shape.size (.dim outDim .scalar) = outDim := by simp [Shape.size]
  Node.ofVec (Γ := Γ) (τ := .dim outDim .scalar)
    (f := fun ctxV => castVec hOut.symm (C.forwardVec ((getVecCLM (Γ := Γ) (n := inDim) idx) ctxV)))
    (jvp := fun ctxV dctxV =>
      castVec hOut.symm
        (toVecE (C.correct.jvp (ofVecE ((getVecCLM (Γ := Γ) (n := inDim) idx) ctxV))
          (ofVecE ((getVecCLM (Γ := Γ) (n := inDim) idx) dctxV)))))
    (vjp := fun ctxV δV =>
      let δV' : Vec outDim := castVec hOut δV
      singleVec (Γ := Γ) (n := inDim) idx
        (toVecE (C.correct.op.backward (ofVecE ((getVecCLM (Γ := Γ) (n := inDim) idx) ctxV)) (ofVecE
          δV'))))
    (correct_inner := by
      intro ctxV dctxV δV
      let δV' : Vec outDim := castVec hOut δV
      -- move the output cast across `inner`
      have hcast :
          inner ℝ (castVec hOut.symm
              (toVecE (C.correct.jvp (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                (ofVecE (getVec (Γ := Γ) (n := inDim) idx dctxV))))) δV
            =
          inner ℝ
              (toVecE (C.correct.jvp (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                (ofVecE (getVec (Γ := Γ) (n := inDim) idx dctxV)))) δV' := by
        -- `δV = castVec hOut.symm δV'`
        have hδ : castVec hOut.symm δV' = δV := by
          simp [δV']
        -- move the cast across `inner` via `inner_castVec_castVec`
        have hinner :=
          inner_castVec_castVec (h := hOut.symm)
            (x := toVecE (C.correct.jvp (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
              (ofVecE (getVec (Γ := Γ) (n := inDim) idx dctxV))))
            (y := δV')
        calc
          inner ℝ (castVec hOut.symm
              (toVecE (C.correct.jvp (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                (ofVecE (getVec (Γ := Γ) (n := inDim) idx dctxV))))) δV
              =
            inner ℝ (castVec hOut.symm
              (toVecE (C.correct.jvp (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                (ofVecE (getVec (Γ := Γ) (n := inDim) idx dctxV))))) (castVec hOut.symm δV') := by
                  simp [hδ]
          _ = inner ℝ (toVecE (C.correct.jvp (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                (ofVecE (getVec (Γ := Γ) (n := inDim) idx dctxV)))) δV' := by
                  simpa using hinner
      -- op-level correctness, converted from `dot` to `inner`
      have h :=
        C.correct.correct
          (x := ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
          (dx := ofVecE (getVec (Γ := Γ) (n := inDim) idx dctxV))
          (δ := ofVecE δV')
      have hinner :
          inner ℝ
              (toVecE (C.correct.jvp (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                (ofVecE (getVec (Γ := Γ) (n := inDim) idx dctxV))))
              δV'
            =
          inner ℝ
              (getVec (Γ := Γ) (n := inDim) idx dctxV)
              (toVecE (C.correct.op.backward (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                (ofVecE δV'))) := by
        simpa [dot_eq_inner_vec, toVecE_ofVecE, δV'] using h
      -- lift the vjp back to the full context with `singleVec`
      have hctx :
          inner ℝ dctxV
              (singleVec (Γ := Γ) (n := inDim) idx
                (toVecE (C.correct.op.backward (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                  (ofVecE δV'))))
            =
          inner ℝ
              (getVec (Γ := Γ) (n := inDim) idx dctxV)
              (toVecE (C.correct.op.backward (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV))
                (ofVecE δV'))) :=
        inner_getVec_singleVec (Γ := Γ) (n := inDim) idx dctxV
          (toVecE (C.correct.op.backward (ofVecE (getVec (Γ := Γ) (n := inDim) idx ctxV)) (ofVecE
            δV')))
      -- combine
      simpa [δV', hcast] using (hcast.trans (hinner.trans hctx.symm)))

/-- `NodeFDerivCorrect` for `unaryOp`. -/
def unaryOpFderiv {Γ : List Shape} {inDim outDim : Nat}
    (idx : Idx Γ (.dim inDim .scalar))
    (C : OpSpecFDerivCorrect inDim outDim) :
    NodeFDerivCorrect (unaryOp (Γ := Γ) (inDim := inDim) (outDim := outDim) idx C) :=
{ deriv := fun xV =>
    let hOut : Shape.size (.dim outDim .scalar) = outDim := by simp [Shape.size]
    (Graph.castCLM (h := hOut.symm)).comp
      ((C.deriv ((getVecCLM (Γ := Γ) (n := inDim) idx) xV)).comp (getVecCLM (Γ := Γ) (n := inDim)
        idx))
  hasFDerivAt := by
    intro xV
    let hOut : Shape.size (.dim outDim .scalar) = outDim := by simp [Shape.size]
    -- projection is linear
    have hproj :
        HasFDerivAt (fun xV : CtxVec Γ => (getVecCLM (Γ := Γ) (n := inDim) idx) xV)
          (getVecCLM (Γ := Γ) (n := inDim) idx) xV := by
      exact (getVecCLM (Γ := Γ) (n := inDim) idx).hasFDerivAt (x := xV)
    have hC :
        HasFDerivAt (C.forwardVec) (C.deriv ((getVecCLM (Γ := Γ) (n := inDim) idx) xV))
          ((getVecCLM (Γ := Γ) (n := inDim) idx) xV) := by
      simpa [OpSpecFDerivCorrect.forwardVec] using (C.hasFDerivAt ((getVecCLM (Γ := Γ) (n := inDim)
        idx) xV))
    have hcomp : HasFDerivAt (fun xV : CtxVec Γ => C.forwardVec ((getVecCLM (Γ := Γ) (n := inDim)
      idx) xV))
        ((C.deriv ((getVecCLM (Γ := Γ) (n := inDim) idx) xV)).comp (getVecCLM (Γ := Γ) (n := inDim)
          idx)) xV :=
      (hC.comp xV hproj)
    -- output cast is linear
    have hcast :
        HasFDerivAt (fun y : Vec outDim => castVec hOut.symm y) (Graph.castCLM (h := hOut.symm))
          (C.forwardVec ((getVecCLM (Γ := Γ) (n := inDim) idx) xV)) := by
      simpa [Graph.castCLM] using ((Graph.castCLM (h := hOut.symm)).hasFDerivAt (x := C.forwardVec
        ((getVecCLM (Γ := Γ) (n := inDim) idx) xV)))
    have hfinal := hcast.comp xV hcomp
    -- `unaryOp.forwardVec` is definitional to this composition (after unfolding casts).
    simpa [unaryOp, getVecCLM_apply, getVec, Graph.castCLM, hOut] using hfinal
  jvp_eq := by
    intro xV dxV
    let hOut : Shape.size (.dim outDim .scalar) = outDim := by simp [Shape.size]
    have hjvp :=
      C.jvp_eq
        (xV := (getVecCLM (Γ := Γ) (n := inDim) idx) xV)
        (dxV := (getVecCLM (Γ := Γ) (n := inDim) idx) dxV)
    -- apply the output cast to both sides
    have hjvp' := congrArg (castVec hOut.symm) hjvp
    -- unfold `unaryOp` and simplify
    simpa [unaryOp, getVecCLM_apply, getVec, Graph.castCLM, hOut, ContinuousLinearMap.comp_apply]
      using hjvp' }

  /-- Linear layer as a single tape node (fixed weights/bias in the `Spec.LinearSpec`). -/
  def linear {Γ : List Shape} {inDim outDim : Nat}
      (x : Idx Γ (.dim inDim .scalar)) (m : Spec.LinearSpec ℝ inDim outDim) :
      Node Γ (.dim outDim .scalar) :=
    unaryOp (Γ := Γ) (inDim := inDim) (outDim := outDim) x (OpSpecFDerivCorrect.linear m)

  /-- `NodeFDerivCorrect` for `linear`: the node derivative matches the spec's `OpSpec` derivative.
    -/
  def linearFderiv {Γ : List Shape} {inDim outDim : Nat}
      (x : Idx Γ (.dim inDim .scalar)) (m : Spec.LinearSpec ℝ inDim outDim) :
      NodeFDerivCorrect (linear (Γ := Γ) (inDim := inDim) (outDim := outDim) x m) :=
    unaryOpFderiv (Γ := Γ) (inDim := inDim) (outDim := outDim) x (OpSpecFDerivCorrect.linear m)

end TapeNodes

end

end Autograd
end Proofs
