/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.GraphSpec.Models.Gondolin

/-!
# Gondolin executable model zoo

This module re-exports Gondolin’s small runnable model constructors (MLP/CNN/Transformer/etc.).
It is the executable model-zoo counterpart to the pure specs in `NN.Spec.Models.*`.

The implementations live under `NN.GraphSpec.Models.Gondolin.*`, because they are architecture
constructors. The runtime namespace stays focused on execution machinery: ops, backends, sessions,
losses, optimizers, and training loops.

We keep this short `NN.GondolinModels` facade so examples can write `GondolinModels.mlp` without
threading a long namespace path everywhere.
-/

@[expose] public section


namespace NN
namespace GondolinModels

export _root_.NN.GraphSpec.Models.Gondolin
  (mlp autoencoder cnn2 softmaxRegression mlpClassifier transformerBlock
   fno1d fno1dParamShapes
   resnet18Model resnet18Program resnet18InitParams
  )

end GondolinModels
end NN
