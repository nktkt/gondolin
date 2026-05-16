import VersoManual
import VersoBlueprint.PreviewManifest
import GondolinBlueprint.Guide

open Verso Doc
open Verso.Genre Manual

def main (args : List String) : IO UInt32 :=
  Informal.PreviewManifest.manualMainWithSharedPreviewManifest
    (%doc GondolinBlueprint.Guide)
    args
    (extensionImpls := by exact extension_impls%)
