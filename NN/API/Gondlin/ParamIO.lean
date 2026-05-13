/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Runtime.Autograd.Gondlin.ParamIO
public import NN.Runtime.Autograd.Gondlin.Module

/-!
# Gondlin ParamIO (Model Checkpoints)

Gondlin examples often want the same simple workflow:

1. train a model for a few steps,
2. save its parameters, and
3. reload those parameters later to sample / run inference.

This module is the **API-facing** wrapper around the lower-level format implementation in
`Runtime.Autograd.Gondlin.ParamIO`.

## What Is Supported

Today we keep the checkpoint format intentionally small and explicit:

- **Scalar backend:** `Float` (Lean `Float`).
- **Encoding:** exact bitwise round-trip via `Float.toBits` (`UInt64`) stored in JSON.
- **Payload:** a shape-indexed parameter pack `Torch.TList Float paramShapes`.

This is enough to checkpoint *any* Gondlin runtime model implemented as a
`Gondlin.Module.ScalarModule` over `Float`, independent of architecture.

If you need float32/complex checkpoints, that belongs in this module too. The initial JSON format is
kept conservative so checkpoint compatibility is predictable.
-/

@[expose] public section

namespace NN
namespace API
namespace Gondlin
namespace ParamIO

open Spec

/--
Write a parameter pack to a JSON bits checkpoint.

This is the lowest-level API entrypoint: it is useful when you already have a
`TList Float paramShapes` (for example from `nn.evalParams`) and just want to persist it.
-/
def saveTListBits
    {paramShapes : List Shape}
    (path : System.FilePath)
    (ps : _root_.Runtime.Autograd.Torch.TList Float paramShapes)
    (pretty : Bool := true) : IO Unit := do
  _root_.Runtime.Autograd.Gondlin.ParamIO.writeTListBits (ss := paramShapes) path ps pretty

/--
Save the current parameter values of a Gondlin runtime module to a JSON bits file.

This is architecture-agnostic: it works for any `ScalarModule Float …`.
-/
def saveModuleParamsBits
    {paramShapes inputShapes : List Shape}
    (m : _root_.Runtime.Autograd.Gondlin.Module.ScalarModule Float paramShapes inputShapes)
    (path : System.FilePath) : IO Unit := do
  let ps ← _root_.Runtime.Autograd.Torch.ParamList.valuesSynced (α := Float) (ss := paramShapes)
    m.trainer.params
  _root_.Runtime.Autograd.Gondlin.ParamIO.writeTListBits (ss := paramShapes) path ps

/--
Load a JSON bits checkpoint and overwrite the module's parameter values.

This performs a shape check against `paramShapes` and fails with a readable error if the file does
not match the model.
-/
def loadModuleParamsBits
    {paramShapes inputShapes : List Shape}
    (m : _root_.Runtime.Autograd.Gondlin.Module.ScalarModule Float paramShapes inputShapes)
    (path : System.FilePath) : IO Unit := do
  let psRes ← _root_.Runtime.Autograd.Gondlin.ParamIO.readTListBits (ss := paramShapes) path
  match psRes with
  | Except.error e =>
      throw <| IO.userError s!"ParamIO: load failed for {path}: {e}"
  | Except.ok ps =>
      _root_.Runtime.Autograd.Torch.ParamList.setValues (α := Float) (ss := paramShapes)
        m.trainer.params ps

/--
Load a JSON bits checkpoint as a parameter list (without mutating a module).

This is useful when you want to run inference with `nn.evalParams` directly and never instantiate a
trainer.
-/
def loadTListBits
    {paramShapes : List Shape}
    (path : System.FilePath) : IO (_root_.Runtime.Autograd.Torch.TList Float paramShapes) := do
  let psRes ← _root_.Runtime.Autograd.Gondlin.ParamIO.readTListBits (ss := paramShapes) path
  match psRes with
  | Except.error e =>
      throw <| IO.userError s!"ParamIO: load failed for {path}: {e}"
  | Except.ok ps =>
      pure ps

/--
Read a JSON bits checkpoint, returning an error string instead of throwing an exception.

This is useful in batch tools or CI-style runs where you want to keep going and report failures.
-/
def readTListBits
    {paramShapes : List Shape}
    (path : System.FilePath) : IO (Except String (_root_.Runtime.Autograd.Torch.TList Float paramShapes)) :=
  _root_.Runtime.Autograd.Gondlin.ParamIO.readTListBits (ss := paramShapes) path

end ParamIO
end Gondlin
end API
end NN
