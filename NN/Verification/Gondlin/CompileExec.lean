/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Runtime.Autograd.Compiled.IRExec
public import NN.Verification.Gondlin.Compile
public import NN.Verification.Gondlin.Correctness

/-!
# CompileExec

Gondlin → IR → executable compiled graph.

This is a small convenience wrapper that:
1) compiles a Gondlin `Program` to `NN.IR.Graph` (plus a verifier-style `ParamStore`), then
2) converts the `ParamStore` to an IR `Payload`, and
3) compiles the IR graph to an executable `Runtime.Autograd.Compiled.ExecGraphData`.

This keeps the shared IR boundary explicit: the same IR artifact can be used both for verification
and for execution.
-/

@[expose] public section


namespace NN.Verification.Gondlin

open Spec
open Tensor
open NN.IR

/-- Compile a Gondlin forward model (single distinguished input) to both IR and executable SSA
  graph. -/
def compileForward1Exec
    {α : Type} [Context α] [DecidableEq Shape] [Inhabited α]
    {paramShapes : List Shape} {inShape outShape : Shape}
    (model : Runtime.Autograd.Gondlin.Program α (paramShapes ++ [inShape]) outShape)
    (params : Runtime.Autograd.Torch.TList α paramShapes) :
    Except String (CompiledIR α × Runtime.Autograd.Compiled.ExecGraphData α) := do
  let c ← compileForward1 (α := α) (paramShapes := paramShapes) (inShape := inShape) (outShape :=
    outShape) model params
  let payload : Payload α := payloadOfParamStore (α := α) c.ps
  let exec ← Runtime.Autograd.Compiled.execGraphOfIR (α := α) c.graph payload
  pure (c, exec)

end NN.Verification.Gondlin
