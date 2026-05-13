/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.MLTheory.SelfSupervised.JEPA
public import NN.MLTheory.SelfSupervised.MAE
public import NN.MLTheory.SelfSupervised.Masking
public import NN.MLTheory.SelfSupervised.PredictiveView
public import NN.MLTheory.SelfSupervised.VICReg

/-!
# Self-supervised learning theory

This is the umbrella import for Gondlin's finite self-supervised objective semantics.

The chapter contains:
- masking primitives for patch/token objectives;
- predictive-view SSL objective algebra;
- MAE-style masked reconstruction losses;
- JEPA-style joint-embedding prediction losses; and
- VICReg/Barlow-Twins-style finite collapse guards.

This layer is intentionally modest: these files formalize the objective-level contracts that model
code should preserve, rather than claiming full optimization or population generalization guarantees.
That keeps the statements reusable across ViT, convolutional, Mamba, or custom backbones.
-/

@[expose] public section
