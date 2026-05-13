/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Runtime.Autograd.Gondlin.Autodiff
public import NN.Runtime.Autograd.Gondlin.Backend
public import NN.Runtime.Autograd.Gondlin.Fft
public import NN.Runtime.Autograd.Gondlin.Fno1d
public import NN.Runtime.Autograd.Gondlin.Functional
public import NN.Runtime.Autograd.Gondlin.Loss
public import NN.Runtime.Autograd.Gondlin.Metrics
public import NN.Runtime.Autograd.Gondlin.Module
public import NN.Runtime.Autograd.Gondlin.NN
public import NN.Runtime.Autograd.Gondlin.Norm
public import NN.Runtime.Autograd.Gondlin.Optim
public import NN.Runtime.Autograd.Gondlin.Session
public import NN.Runtime.Autograd.Gondlin.Training

/-!
# Gondlin

Gondlin is the runtime front-end for training and execution.

This module is the user-facing wrapper around the lower-level runtime session implementation:
- write a model/loss once over a small `Ops` interface,
- choose `backend := .eager` (dynamic tape) or `backend := .compiled` (typed SSA/DAG),
- run `forward`, `backward`, and `step` with the same call shape.

`Runtime.Autograd.Gondlin` is the stable runtime namespace re-exported by `NN.API.Runtime`.
`Runtime.Autograd.Torch` remains available as the lower-level session layer used internally by
Gondlin and by linked compiled sessions.

This umbrella deliberately does **not** own model catalogs or RL objectives. Reusable architecture
specifications live under `NN.GraphSpec.Models.Gondlin`, while differentiable PPO / actor-critic
loss helpers live under `NN.Runtime.RL.PolicyGradient.Autograd`. Keeping those out of the runtime
core makes the dependency graph easier to audit: this folder should provide tensors, ops, modules,
sessions, losses, optim/training glue, and executable autodiff utilities.
-/

@[expose] public section


namespace Runtime
namespace Autograd
namespace Gondlin

export _root_.Runtime.Autograd.Torch
  (TList
   TensorRef Param AnyParam
   CompiledScalar compileScalar
   CompiledOut compileOut
   ParamList ScalarTrainer scalarTrainer)

-- Unified imperative session (choose eager vs compiled at `new` time):
-- `Gondlin.Session` is defined in `NN.Runtime.Autograd.Gondlin.Session` and is available
-- automatically via the import above.

/-! ## Training helpers -/

export _root_.Runtime.Autograd.Torch
  (scalarOf tlist1 tlist2 tlist3 tlist4 trainCycleSGD meanLoss)

namespace Init
export _root_.Runtime.Autograd.Torch.Init (Scheme tensor xavierW kaimingW)
end Init

namespace Samples
export _root_.Runtime.Autograd.Torch.Samples (vec1 vec2 affine2)
end Samples

namespace ScalarTrainer

export _root_.Runtime.Autograd.Torch.ScalarTrainer (forwardT backwardT stepT)

end ScalarTrainer

/-! ## Optimizers -/
export _root_.Runtime.Autograd.Gondlin.Optim (StateList Optimizer)
export _root_.Runtime.Autograd.Gondlin.Optim
  (sgd momentumSGD adagrad rmsprop adam adamw adadelta projectedSGD muon)

/-! ## Module wrappers (PyTorch-style) -/
export _root_.Runtime.Autograd.Gondlin.Module
  (ScalarModuleDef ScalarModule)
export _root_.Runtime.Autograd.Gondlin.Module.ScalarModule
  (create forward backward step initOptim stepWith params)
export _root_.Runtime.Autograd.Gondlin.Module.ScalarModuleDef
  (instantiate)

end Gondlin
end Autograd
end Runtime
