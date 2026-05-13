/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.GraphSpec.Models.Gondlin

/-!
# Gondlin executable model zoo

This module re-exports Gondlin’s small runnable model constructors (MLP/CNN/Transformer/etc.).
It is the executable model-zoo counterpart to the pure specs in `NN.Spec.Models.*`.

The implementations live under `NN.GraphSpec.Models.Gondlin.*`, because they are architecture
constructors. The runtime namespace stays focused on execution machinery: ops, backends, sessions,
losses, optimizers, and training loops.

We keep this short `NN.GondlinModels` facade so examples can write `GondlinModels.mlp` without
threading a long namespace path everywhere.
-/

@[expose] public section


namespace NN
namespace GondlinModels

export _root_.NN.GraphSpec.Models.Gondlin
  (mlp autoencoder cnn2 softmaxRegression mlpClassifier transformerBlock
   fno1d fno1dParamShapes
   resnet18Model resnet18Program resnet18InitParams
  )

end GondlinModels
end NN
