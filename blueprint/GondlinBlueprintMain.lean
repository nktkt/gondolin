import VersoManual
import VersoBlueprint.PreviewManifest
import GondlinBlueprint.Guide

open Verso Doc
open Verso.Genre Manual

def main (args : List String) : IO UInt32 :=
  Informal.PreviewManifest.manualMainWithSharedPreviewManifest
    (%doc GondlinBlueprint.Guide)
    args
    (extensionImpls := by exact extension_impls%)
