/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Examples.Verification.Gondolin.GondolinCrownOps
public import NN.Examples.Verification.Gondolin.GondolinIBP
public import NN.Examples.Verification.Gondolin.GondolinMlpWorkflow
public import NN.Examples.Verification.Gondolin.GondolinTransformerIBP

/-!
# Gondolin Verification Workflows

End-to-end examples that build Gondolin models, lower them into verification artifacts, and run
IBP/CROWN-style checks.
-/

@[expose] public section
