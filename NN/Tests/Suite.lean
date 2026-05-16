/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import Std

public import NN.Tests.Runtime.Floats.Suite
public import NN.Tests.Runtime.Rationals.Suite
public import NN.Tests.Runtime.Cuda.Suite

/-!
# Suite

Top-level executable test entrypoint for Gondolin.

This suite is intentionally not a replacement for the theorem stack in `NN/Proofs`. It is the
regression harness for runtime trust boundaries: native CUDA kernels, FFI buffers,
floating-point execution, executable parsers, and public API smoke tests.
-/

@[expose] public section

open Std

namespace NN.Tests

def usage : String :=
  String.intercalate "\n"
    [ "Gondolin test suite"
    , ""
    , "Usage:"
    , "  lake build nn_tests_suite && lake exe nn_tests_suite"
    , ""
    , "Notes:"
    , "  Heavier verification certificate checkers are separate executables:"
    , "    lake exe verify -- all    # run bundled cert checkers"
    , "    lake exe verify -- list   # list all verifier tools"
    ]

def run : IO Unit := do
  IO.println "== Gondolin: curated tests =="
  Tests.Floats.run
  Tests.Rationals.Suite.run
  Tests.Cuda.run
  IO.println "== Gondolin: all curated tests passed =="

def main (args : List String) : IO Unit := do
  match args with
  | ["--help"] | ["-h"] =>
      IO.println usage
  | [] =>
      run
  | _ =>
      IO.eprintln s!"Unknown args: {args}"
      IO.eprintln ""
      IO.eprintln usage
      IO.throwServerError "bad CLI args"

end NN.Tests

def main (args : List String) : IO Unit :=
  NN.Tests.main args
