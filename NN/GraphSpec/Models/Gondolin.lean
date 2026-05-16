/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.GraphSpec.Models.Gondolin.Autoencoder
public import NN.GraphSpec.Models.Gondolin.Cnn
public import NN.GraphSpec.Models.Gondolin.Fno1d
public import NN.GraphSpec.Models.Gondolin.Mlp
public import NN.GraphSpec.Models.Gondolin.Resnet18
public import NN.GraphSpec.Models.Gondolin.TransformerBlock

/-!
# Gondolin-Executable GraphSpec Models

This module is the architecture-facing home for reusable model constructors that still execute via
the Gondolin autograd runtime.

The split is intentional:
- `NN.GraphSpec.Models.*` contains graph-authored architectures and architecture-facing wrappers.
- `NN.GraphSpec.Models.Gondolin.*` contains executable `Gondolin.NN.Seq` / `Gondolin.Program`
  constructors for common models.
- `NN.Runtime.Autograd.Gondolin.*` contains runtime machinery: tensors, ops, backends, sessions,
  losses, optimizers, and training loops.

So users looking for models start from GraphSpec, while runtime internals stay focused on execution.
-/

@[expose] public section

namespace NN
namespace GraphSpec
namespace Models
namespace Gondolin
end Gondolin
end Models
end GraphSpec
end NN
