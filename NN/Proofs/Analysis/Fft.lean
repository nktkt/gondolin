/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import Mathlib.Data.Matrix.Basic
public import Mathlib.RingTheory.RootsOfUnity.Complex
public import Mathlib.LinearAlgebra.Matrix.ConjTranspose
import Mathlib.LinearAlgebra.Matrix.SemiringInverse

/-!
# Discrete Fourier Transform (DFT) theorems over mathlib `ℂ`

Gondlin’s runtime FFT building blocks (`NN.Runtime.Autograd.Gondlin.Fft`) implement FFT/IFFT by
explicit DFT matrices. This file proves the corresponding *exact* math facts over mathlib’s complex
numbers `ℂ`:

- the inverse DFT matrix is a left inverse of the DFT matrix, and therefore
- `ifft (fft x) = x` for vectors.

We prove these statements in the mathlib `Matrix` world first. That choice is deliberate:
primitive roots of unity, conjugate transposes, geometric sums, and matrix inverse facts already
live cleanly in mathlib for `ℂ`.

The Gondlin runtime FFT code uses shape-indexed tensors and scalar-polymorphic twiddle factors
written with `cos`/`sin`. Connecting that runtime representation to these exact matrices is a
separate transport theorem in `NN.Proofs.Analysis.FftBridge`. Keeping the files split avoids making
the pure DFT algebra import the runtime/autograd stack.

References:
- Any standard Fourier analysis / numerical linear algebra text (this is the classical DFT
  inversion formula).
- For the primitive-root-of-unity facts used here, we rely on mathlib’s
  `Complex.isPrimitiveRoot_exp` and the geometric-sum identity `mul_geom_sum`.
-/

@[expose] public section

open scoped BigOperators Matrix

noncomputable section

namespace Proofs

namespace Fft

/-! ## DFT / IDFT matrices -/

/-- Primitive `n`-th root of unity: `ζₙ = exp(2π i / n)`. -/
def ζ (n : Nat) : ℂ :=
  Complex.exp (2 * Real.pi * Complex.I / n)

/-- The “negative-frequency” root used by the DFT: `ωₙ = ζₙ⁻¹ = exp(-2π i / n)`. -/
def ω (n : Nat) : ℂ :=
  (ζ n)⁻¹

/--
DFT matrix `F : n×n` (frequency × spatial), with entries:

`F[k,j] = ωₙ^(j*k)`.

This matches the usual `exp(-2π i j*k/n)` convention (since `ωₙ = exp(-2π i / n)`).
-/
def dftMatrix (n : Nat) : Matrix (Fin n) (Fin n) ℂ :=
  fun k j => ω n ^ (j.val * k.val)

/--
Inverse DFT matrix `F⁻¹ : n×n` (spatial × frequency), with entries:

`F⁻¹[j,k] = ζₙ^(j*k) / n`.

This matches the classical inverse scaling `1/n`.
-/
def idftMatrix (n : Nat) : Matrix (Fin n) (Fin n) ℂ :=
  fun j k => ζ n ^ (j.val * k.val) / n

/-! ## Inversion theorem

The proof follows the textbook orthogonality argument. The `(i,k)` entry of `IDFT * DFT` is

`(1/n) * ∑ j, (ζ^i * (ζ^k)⁻¹)^j`.

If `i = k`, the ratio is `1` and the sum is `n`. If `i ≠ k`, the ratio is a nontrivial `n`-th root
of unity, so the geometric sum is `0`.
-/

private lemma zeta_ne_zero (n : Nat) : ζ n ≠ 0 := by
  -- `exp` is never zero in `ℂ`.
  simp [ζ]

/--
Geometric-sum lemma (specialized): if `r^n = 1` and `r ≠ 1`, then `∑_{j=0}^{n-1} r^j = 0`.
-/
private lemma geom_sum_eq_zero_of_pow_eq_one {r : ℂ} {n : Nat} (hr : r ≠ 1) (hrn : r ^ n = 1) :
    (∑ j ∈ Finset.range n, r ^ j) = 0 := by
  -- Use `(r - 1) * (∑ r^j) = r^n - 1`.
  have hmul : (r - 1) * (∑ j ∈ Finset.range n, r ^ j) = 0 := by
    calc
      (r - 1) * (∑ j ∈ Finset.range n, r ^ j) = r ^ n - 1 := by
        simpa using (mul_geom_sum r n)
      _ = 0 := by
        simp [hrn]
  exact
    eq_zero_of_ne_zero_of_mul_left_eq_zero
      (sub_ne_zero.mpr hr)
      hmul

/--
Main algebraic identity: `IDFT * DFT = 1` (over `ℂ`), for `n ≠ 0`.

This is the standard DFT inversion theorem.
-/
theorem idft_mul_dft (n : Nat) (hn : n ≠ 0) :
    idftMatrix n * dftMatrix n = 1 := by
  classical
  have hprim : IsPrimitiveRoot (ζ n) n := Complex.isPrimitiveRoot_exp n hn
  have hn0 : (n : ℂ) ≠ 0 := by exact_mod_cast hn

  ext i k
  -- Write the (i,k) entry as a geometric series in the ratio `r = ζ^i * (ζ^k)⁻¹`.
  set r : ℂ := (ζ n) ^ i.val * ((ζ n) ^ k.val)⁻¹

  have hmul_apply :
      (idftMatrix n * dftMatrix n) i k =
        (1 / (n : ℂ)) * ∑ j : Fin n, r ^ (j : Nat) := by
    -- Expand the matrix product and normalize each summand.
    have hz0 : ζ n ≠ 0 := zeta_ne_zero n
    calc
      (idftMatrix n * dftMatrix n) i k
          = ∑ j : Fin n, idftMatrix n i j * dftMatrix n j k := by
              simp [Matrix.mul_apply]
      _ = ∑ j : Fin n,
            ((ζ n) ^ (i.val * j.val) / n) * ((ω n) ^ (k.val * j.val)) := by
              simp [idftMatrix, dftMatrix]
      _ = ∑ j : Fin n,
            ((ζ n) ^ (i.val * j.val) / n) * (((ζ n) ^ (k.val * j.val))⁻¹) := by
              simp [ω, inv_pow]
      _ = (1 / (n : ℂ)) * ∑ j : Fin n,
            ((ζ n) ^ i.val * ((ζ n) ^ k.val)⁻¹) ^ (j : Nat) := by
              -- Rewrite each summand as `(1/n) * r^j`, then pull `(1/n)` out of the sum.
              --
              -- Key algebra:
              --   ζ^(i*j) = (ζ^i)^j,
              --   (ζ^(k*j))⁻¹ = ((ζ^k)⁻¹)^j,
              --   (a^j) * (b^j) = (a*b)^j in a commutative monoid.
              --
              -- And we interpret `/ n` as multiplication by `(n:ℂ)⁻¹`.
              have : ∀ j : Fin n,
                  ((ζ n) ^ (i.val * j.val) / n) * (((ζ n) ^ (k.val * j.val))⁻¹) =
                    (1 / (n : ℂ)) * ((ζ n) ^ i.val * ((ζ n) ^ k.val)⁻¹) ^ (j : Nat) := by
                intro j
                -- Reduce both sides to the same normal form.
                simp [div_eq_mul_inv, mul_assoc, mul_comm, pow_mul, mul_pow, inv_pow]
              -- Use the pointwise rewrite, then factor the constant out.
              simp [this, Finset.mul_sum]
      _ = (1 / (n : ℂ)) * ∑ j : Fin n, r ^ (j : Nat) := by
            -- Unfold `r` back in.
            simp [r]

  -- Now split on whether `i = k`.
  by_cases hik : i = k
  · subst hik
    -- Then `r = 1`, so the sum is `n` and `(1/n) * n = 1`.
    have hr1 : r = 1 := by
      -- `ζ^i * (ζ^i)⁻¹ = 1` since `ζ ≠ 0`.
      have hz0 : (ζ n) ^ i.val ≠ 0 := pow_ne_zero _ (zeta_ne_zero n)
      simp [r, hz0]
    -- Finish by rewriting the entry to the sum-of-ones form.
    calc
      (idftMatrix n * dftMatrix n) i i
          = (1 / (n : ℂ)) * ∑ j : Fin n, r ^ (j : Nat) := by
              simpa using hmul_apply
      _ = (1 / (n : ℂ)) * ∑ _j : Fin n, (1 : ℂ) := by simp [hr1]
      _ = (1 / (n : ℂ)) * (n : ℂ) := by simp
      _ = 1 := by simp [div_eq_mul_inv, hn0]
      _ = (1 : Matrix (Fin n) (Fin n) ℂ) i i := by simp
  · -- `i ≠ k`: show the geometric sum is zero.
    have hir : i.val < n := i.isLt
    have hkr : k.val < n := k.isLt

    have hr_ne_one : r ≠ 1 := by
      intro hr1
      -- If `r = 1` then `ζ^i = ζ^k`, contradicting primitivity/injectivity on `[0,n)`.
      have hzPowK0 : (ζ n) ^ k.val ≠ 0 := pow_ne_zero _ (zeta_ne_zero n)
      have hEq : (ζ n) ^ i.val = (ζ n) ^ k.val := by
        -- Multiply `r = 1` on the right by `ζ^k`.
        have h := congrArg (fun x => x * (ζ n) ^ k.val) hr1
        -- Simplify using `inv_mul_cancel` and associativity.
        simpa [r, mul_assoc, hzPowK0] using h
      have : i.val = k.val := hprim.pow_inj hir hkr hEq
      exact hik (Fin.ext this)

    have hr_pow_n : r ^ n = 1 := by
      -- `(ζ^i * (ζ^k)⁻¹)^n = (ζ^i)^n * ((ζ^k)⁻¹)^n = 1 * 1`.
      have hzi : ((ζ n) ^ i.val) ^ n = 1 := by
        calc
          ((ζ n) ^ i.val) ^ n = (ζ n) ^ (i.val * n) := by
            simpa using (pow_mul (ζ n) i.val n).symm
          _ = (ζ n) ^ (n * i.val) := by simp [Nat.mul_comm]
          _ = ((ζ n) ^ n) ^ i.val := by
            simpa using (pow_mul (ζ n) n i.val)
          _ = 1 := by simp [hprim.pow_eq_one]
      have hzk : ((ζ n) ^ k.val) ^ n = 1 := by
        calc
          ((ζ n) ^ k.val) ^ n = (ζ n) ^ (k.val * n) := by
            simpa using (pow_mul (ζ n) k.val n).symm
          _ = (ζ n) ^ (n * k.val) := by simp [Nat.mul_comm]
          _ = ((ζ n) ^ n) ^ k.val := by
            simpa using (pow_mul (ζ n) n k.val)
          _ = 1 := by simp [hprim.pow_eq_one]
      calc
        r ^ n = (((ζ n) ^ i.val) * ((ζ n) ^ k.val)⁻¹) ^ n := by simp [r]
        _ = ((ζ n) ^ i.val) ^ n * (((ζ n) ^ k.val)⁻¹) ^ n := by simp [mul_pow]
        _ = 1 * (((ζ n) ^ k.val) ^ n)⁻¹ := by simp [hzi, inv_pow]
        _ = 1 := by simp [hzk]

    have hsum0 : (∑ j : Fin n, r ^ (j : Nat)) = 0 := by
      -- Convert the `Fin n` sum to a `range n` sum, then apply the geometric-sum lemma.
      have hsumRange : (∑ j ∈ Finset.range n, r ^ j) = 0 :=
        geom_sum_eq_zero_of_pow_eq_one (r := r) (n := n) hr_ne_one hr_pow_n
      have hfin :
          (∑ j : Fin n, r ^ (j : Nat)) = (∑ j ∈ Finset.range n, r ^ j) := by
        simpa using (Fin.sum_univ_eq_sum_range (f := fun j : Nat => r ^ j) n)
      simpa [hfin] using hsumRange

    -- Finish: entry is `(1/n) * 0 = 0`.
    calc
      (idftMatrix n * dftMatrix n) i k
          = (1 / (n : ℂ)) * ∑ j : Fin n, r ^ (j : Nat) := by
              simpa using hmul_apply
      _ = 0 := by simp [hsum0]
      _ = (1 : Matrix (Fin n) (Fin n) ℂ) i k := by
            simp [hik]

/-! ## Orthogonality / unitary form -/

private lemma star_zeta (n : Nat) : star (ζ n) = ω n := by
  -- Conjugation sends `exp z` to `exp (conj z)`, and `conj (2π I / n) = -(2π I / n)`.
  -- Then `exp (-z) = (exp z)⁻¹`.
  set x : ℂ := (2 * Real.pi * Complex.I) / n
  have hstar : star (Complex.exp x) = Complex.exp (star x) := by
    simp
  calc
    star (ζ n) = star (Complex.exp x) := by simp [ζ, x]
    _ = Complex.exp (star x) := hstar
    _ = Complex.exp (-x) := by simp [x, neg_div]
    _ = (Complex.exp x)⁻¹ := by simp [Complex.exp_neg]
    _ = (ζ n)⁻¹ := by simp [ζ, x]
    _ = ω n := rfl

/-- Conjugation sends the negative-frequency DFT root `ωₙ` back to the positive root `ζₙ`. -/
private lemma star_omega (n : Nat) : star (ω n) = ζ n := by
  -- `ω = ζ⁻¹` and `star` preserves inverses.
  simp [ω, star_zeta (n := n)]

/--
On `ℂ`, the inverse DFT matrix is a scaled conjugate transpose of the DFT matrix:

`F⁻¹ = (1/n) • Fᴴ`.
-/
theorem idftMatrix_eq_invNat_smul_conjTranspose_dftMatrix (n : Nat) :
    idftMatrix n = (1 / (n : ℂ)) • (dftMatrix n)ᴴ := by
  classical
  ext j k
  -- `simp` reduces the RHS to `((1/n) * star (ω^(j*k)))`, and `star ω = ζ`.
  simp [idftMatrix, dftMatrix, Matrix.conjTranspose_apply, ζ, star_pow, star_omega (n := n),
    div_eq_mul_inv, mul_left_comm, mul_comm]

/--
Orthogonality identity (unitary form): `Fᴴ * F = n • 1`.

Equivalently, the DFT columns form an orthogonal basis with squared norm `n`.
-/
theorem conjTranspose_dft_mul_dft (n : Nat) (hn : n ≠ 0) :
    (dftMatrix n)ᴴ * dftMatrix n = (n : ℂ) • 1 := by
  classical
  have hn0 : (n : ℂ) ≠ 0 := by exact_mod_cast hn
  have h :
      ((1 / (n : ℂ)) • (dftMatrix n)ᴴ) * dftMatrix n = 1 := by
    simpa [idftMatrix_eq_invNat_smul_conjTranspose_dftMatrix (n := n)] using idft_mul_dft (n := n)
      hn
  have h' : (1 / (n : ℂ)) • ((dftMatrix n)ᴴ * dftMatrix n) = 1 := by
    simpa [Matrix.smul_mul] using h
  have := congrArg (fun M => (n : ℂ) • M) h'
  -- Cancel the scalar `n` against `1/n`.
  simpa [smul_smul, div_eq_mul_inv, hn0] using this

/-- Right-inverse form: `DFT * IDFT = 1` (for `n ≠ 0`). -/
theorem dft_mul_idft (n : Nat) (hn : n ≠ 0) :
    dftMatrix n * idftMatrix n = 1 := by
  -- Square matrices over a commutative semiring are Dedekind-finite, so a right-inverse is also a
  -- left-inverse.
  simpa using mul_eq_one_symm (idft_mul_dft (n := n) hn)

/-! ## Vector form -/

/-- DFT as a linear operator on `Fin n → ℂ`. -/
def dft (n : Nat) (x : Fin n → ℂ) : Fin n → ℂ :=
  Matrix.mulVec (dftMatrix n) x

/-- Inverse DFT as a linear operator on `Fin n → ℂ`. -/
def idft (n : Nat) (x : Fin n → ℂ) : Fin n → ℂ :=
  Matrix.mulVec (idftMatrix n) x

/--
Vector inversion theorem: `idft (dft x) = x`, for `n ≠ 0`.
-/
theorem idft_dft (n : Nat) (hn : n ≠ 0) (x : Fin n → ℂ) :
    idft n (dft n x) = x := by
  classical
  -- Use `(IDFT * DFT).mulVec x = IDFT.mulVec (DFT.mulVec x)` and the matrix identity.
  have hmulVec :
      Matrix.mulVec (idftMatrix n) (Matrix.mulVec (dftMatrix n) x) =
        Matrix.mulVec (idftMatrix n * dftMatrix n) x := by
    exact Matrix.mulVec_mulVec (v := x) (M := idftMatrix n) (N := dftMatrix n)
  calc
    idft n (dft n x) = Matrix.mulVec (idftMatrix n) (Matrix.mulVec (dftMatrix n) x) := rfl
    _ = Matrix.mulVec (idftMatrix n * dftMatrix n) x := hmulVec
    _ = Matrix.mulVec 1 x := by simp [idft_mul_dft (n := n) hn]
    _ = x := by simp [Matrix.one_mulVec]

/--
Vector inversion theorem (other direction): `dft (idft x) = x`, for `n ≠ 0`.
-/
theorem dft_idft (n : Nat) (hn : n ≠ 0) (x : Fin n → ℂ) :
    dft n (idft n x) = x := by
  classical
  have hmulVec :
      Matrix.mulVec (dftMatrix n) (Matrix.mulVec (idftMatrix n) x) =
        Matrix.mulVec (dftMatrix n * idftMatrix n) x := by
    exact Matrix.mulVec_mulVec (v := x) (M := dftMatrix n) (N := idftMatrix n)
  calc
    dft n (idft n x) = Matrix.mulVec (dftMatrix n) (Matrix.mulVec (idftMatrix n) x) := rfl
    _ = Matrix.mulVec (dftMatrix n * idftMatrix n) x := hmulVec
    _ = Matrix.mulVec 1 x := by simp [dft_mul_idft (n := n) hn]
    _ = x := by simp [Matrix.one_mulVec]

end Fft

end Proofs
