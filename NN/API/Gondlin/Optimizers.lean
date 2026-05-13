/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.API.Runtime

/-!
# Optimizer Convenience Constructors

This module provides a compact PyTorch-shaped optimizer surface for the Gondlin trainer API.

## PyTorch Mapping

The names and default hyperparameters mirror common PyTorch optimizers:
- SGD: `https://pytorch.org/docs/stable/generated/torch.optim.SGD.html`
- Adam: `https://pytorch.org/docs/stable/generated/torch.optim.Adam.html`
- AdamW: `https://pytorch.org/docs/stable/generated/torch.optim.AdamW.html`

General optimizer docs:
`https://pytorch.org/docs/stable/optim.html`
-/

@[expose] public section


namespace NN
namespace API
namespace Gondlin
namespace Optimizers

/-- Public optimizer config alias for the high-level trainer surface. -/
abbrev Config := API.Gondlin.Trainer.Optimizer

-- Re-export constructors from `API.Gondlin.Trainer` (canonical).
/-- Construct an SGD optimizer configuration. -/
abbrev sgd := API.Gondlin.Trainer.sgd

/-- Construct a momentum-SGD optimizer configuration. -/
abbrev momentumSGD := API.Gondlin.Trainer.momentumSGD

/-- Construct an Adam optimizer configuration. -/
abbrev adam := API.Gondlin.Trainer.adam

/-- Construct an AdamW optimizer configuration. -/
abbrev adamw := API.Gondlin.Trainer.adamw

end Optimizers
end Gondlin
end API
end NN
