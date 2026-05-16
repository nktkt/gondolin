/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Runtime.Autograd.Gondolin.Fno1d

/-!
# Gondolin-executable model: FNO1D

This is the `Models`-namespaced alias for Gondolin's 1D Fourier Neural Operator implementations.

The actual implementation lives in `NN.Runtime.Autograd.Gondolin.Fno1d` under
`Runtime.Autograd.Gondolin.NN.FNO1D`. We keep the executable architecture definitions in one
canonical runtime file and expose aliases here so broad model imports never duplicate definitions
or create namespace collisions.

## Reference

- Zongyi Li et al., “Fourier Neural Operator for Parametric Partial Differential Equations”, 2020.
-/

@[expose] public section

namespace NN
namespace GraphSpec
namespace Models
namespace Gondolin

/-- FFT-based 1D FNO model constructor (see `NN.FNO1D.model`). -/
abbrev fno1d := _root_.Runtime.Autograd.Gondolin.NN.FNO1D.model

/-- Real-valued dense-DFT 1D FNO model constructor (see `NN.FNO1D.Real.model`). -/
abbrev fno1dReal := _root_.Runtime.Autograd.Gondolin.NN.FNO1D.Real.model

/-- Parameter-shape lemma for `fno1d` (see `NN.FNO1D.model_paramShapes`). -/
abbrev fno1dParamShapes := _root_.Runtime.Autograd.Gondolin.NN.FNO1D.model_paramShapes

end Gondolin
end Models
end GraphSpec
end NN
