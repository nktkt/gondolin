/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Examples.Models.Common
public import NN.Examples.Models.Supervised
public import NN.Examples.Models.Vision
public import NN.Examples.Models.Sequence
public import NN.Examples.Models.Generative
public import NN.Examples.Models.Operators
public import NN.Examples.Models.RL

/-!
# Model Examples

Umbrella for Gondlin's runnable model/training examples.

The source tree is grouped by what the example teaches:

- `Common`: shared data helpers used by several examples.
- `Supervised`: small supervised/tabular models.
- `Vision`: CNN, ResNet, and ViT examples.
- `Sequence`: recurrent, transformer, GPT, text, and Mamba examples.
- `Generative`: autoencoder, VAE/VQ-VAE/GAN/diffusion/MAE examples.
- `Operators`: operator-learning examples such as FNO.
- `RL`: executable RL trainers (artifact viewers live under `NN.Examples.RL`).

The command-line interface remains stable through `lake exe gondlin <name>`.
-/

@[expose] public section
