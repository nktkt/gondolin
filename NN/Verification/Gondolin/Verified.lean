/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Verification.Gondolin.Proved

/-!
# Verified forward compiler bridge

This module is the public naming layer for the verified forward compiler bridge.

The implementation proof lives in `NN.Verification.Gondolin.Proved`; this file exposes the names we
want users and downstream modules to reach for: `compileForward1`, `compileForward1_wellFormed`, and
`compileForward1_correct`.
-/

@[expose] public section

namespace NN.Verification.Gondolin.Verified

open _root_.Spec
open _root_.Spec.Tensor
open NN.Verification.Gondolin

open NN.Verification.Gondolin.Proved

/-- Compile a verified single-input forward program into the verifier IR. -/
abbrev compileForward1
    {α : Type} [Context α]
    {paramShapes : List Shape} {inShape outShape : Shape}
    (p : Proved.Program α paramShapes inShape outShape)
    (params : Runtime.Autograd.Torch.TList α paramShapes) :
    NN.Verification.Gondolin.CompiledIR α :=
  NN.Verification.Gondolin.Proved.compileForward1 (α := α) (paramShapes := paramShapes)
    (inShape := inShape) (outShape := outShape) p params

/-- Compile-time structural safety of the compiled verifier graph. -/
theorem compileForward1_wellFormed
    {α : Type} [Context α]
    {paramShapes : List Shape} {inShape outShape : Shape}
    (p : Proved.Program α paramShapes inShape outShape)
    (params : Runtime.Autograd.Torch.TList α paramShapes) :
    (compileForward1 (α := α) (paramShapes := paramShapes) (inShape := inShape) (outShape := outShape) p
      params).graph.wellFormed = true :=
  NN.Verification.Gondolin.Proved.compileForward1_wellFormed (α := α)
    (paramShapes := paramShapes) (inShape := inShape) (outShape := outShape) p params

/-- Short, explicit alias for the main end-to-end compiler correctness theorem. -/
theorem compileForward1_correct
    {α : Type} [Context α] [DecidableEq Shape]
    {paramShapes : List Shape} {inShape outShape : Shape}
    (p : Proved.Program α paramShapes inShape outShape)
    (params : Runtime.Autograd.Torch.TList α paramShapes)
    (x : Tensor α inShape) :
    NN.Verification.Gondolin.evalCompiledForward1 (α := α) (inShape := inShape) (outShape := outShape)
        (c := NN.Verification.Gondolin.Proved.compileForward1 (α := α) (paramShapes := paramShapes)
          (inShape := inShape) (outShape := outShape) p params)
        x
      =
    NN.Verification.Gondolin.Proved.evalForward1 (α := α) (paramShapes := paramShapes) (inShape := inShape)
      (outShape := outShape) p params x :=
  NN.Verification.Gondolin.Proved.evalCompiledForward1_eq_evalForward1 (α := α)
    (paramShapes := paramShapes) (inShape := inShape) (outShape := outShape) p params x

/-- Same content with a more concise statement name. -/
theorem forward1_correct_eq_evalForward1
    {α : Type} [Context α] [DecidableEq Shape]
    {paramShapes : List Shape} {inShape outShape : Shape}
    (p : Proved.Program α paramShapes inShape outShape)
    (params : Runtime.Autograd.Torch.TList α paramShapes)
    (x : Tensor α inShape) :
    NN.Verification.Gondolin.evalCompiledForward1 (α := α) (inShape := inShape) (outShape := outShape)
        (c := compileForward1 (α := α) (paramShapes := paramShapes)
          (inShape := inShape) (outShape := outShape) p params)
        x
      =
    NN.Verification.Gondolin.Proved.evalForward1 (α := α) (paramShapes := paramShapes) (inShape := inShape)
      (outShape := outShape) p params x :=
  compileForward1_correct (α := α) (paramShapes := paramShapes) (inShape := inShape)
    (outShape := outShape) p params x

end NN.Verification.Gondolin.Verified
