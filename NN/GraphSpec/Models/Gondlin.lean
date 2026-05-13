/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.GraphSpec.Models.Gondlin.Autoencoder
public import NN.GraphSpec.Models.Gondlin.Cnn
public import NN.GraphSpec.Models.Gondlin.Fno1d
public import NN.GraphSpec.Models.Gondlin.Mlp
public import NN.GraphSpec.Models.Gondlin.Resnet18
public import NN.GraphSpec.Models.Gondlin.TransformerBlock

/-!
# Gondlin-Executable GraphSpec Models

This module is the architecture-facing home for reusable model constructors that still execute via
the Gondlin autograd runtime.

The split is intentional:
- `NN.GraphSpec.Models.*` contains graph-authored architectures and architecture-facing wrappers.
- `NN.GraphSpec.Models.Gondlin.*` contains executable `Gondlin.NN.Seq` / `Gondlin.Program`
  constructors for common models.
- `NN.Runtime.Autograd.Gondlin.*` contains runtime machinery: tensors, ops, backends, sessions,
  losses, optimizers, and training loops.

So users looking for models start from GraphSpec, while runtime internals stay focused on execution.
-/

@[expose] public section

namespace NN
namespace GraphSpec
namespace Models
namespace Gondlin
end Gondlin
end Models
end GraphSpec
end NN
