/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Examples.Verification.Gondlin.GondlinCrownOps
public import NN.Examples.Verification.Gondlin.GondlinIBP
public import NN.Examples.Verification.Gondlin.GondlinMlpWorkflow
public import NN.Examples.Verification.Gondlin.GondlinTransformerIBP

/-!
# Gondlin Verification Workflows

End-to-end examples that build Gondlin models, lower them into verification artifacts, and run
IBP/CROWN-style checks.
-/

@[expose] public section
