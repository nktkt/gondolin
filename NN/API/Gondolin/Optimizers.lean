/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.API.Runtime

/-!
# Optimizer Convenience Constructors

This module provides a compact PyTorch-shaped optimizer surface for the Gondolin trainer API.

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
namespace Gondolin
namespace Optimizers

/-- Public optimizer config alias for the high-level trainer surface. -/
abbrev Config := API.Gondolin.Trainer.Optimizer

-- Re-export constructors from `API.Gondolin.Trainer` (canonical).
/-- Construct an SGD optimizer configuration. -/
abbrev sgd := API.Gondolin.Trainer.sgd

/-- Construct a momentum-SGD optimizer configuration. -/
abbrev momentumSGD := API.Gondolin.Trainer.momentumSGD

/-- Construct an Adam optimizer configuration. -/
abbrev adam := API.Gondolin.Trainer.adam

/-- Construct an AdamW optimizer configuration. -/
abbrev adamw := API.Gondolin.Trainer.adamw

end Optimizers
end Gondolin
end API
end NN
