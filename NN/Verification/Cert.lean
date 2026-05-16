/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Verification.Cert.Common
public import NN.Verification.Cert.IBPCert
public import NN.Verification.Cert.IBPNodeCert
public import NN.Verification.Cert.CROWNNodeCert
public import NN.Verification.Cert.CROWNNodeCertAlphaBeta
public import NN.Verification.Cert.AbCrownLeafCert

/-!
# Certificate Verification

Public umbrella import for Gondolin's executable certificate checkers.

These modules define:
- artifact parsers (JSON → typed structures),
- recomputation checkers that replay bound propagation inside Lean, and
- the tolerance discipline used when comparing decimal-serialized floats to Lean recomputation.

Artifacts are treated as untrusted inputs: they only receive credit after passing these checkers.
-/

@[expose] public section

