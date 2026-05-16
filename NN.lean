/-
Copyright (c) 2026 Gondolin
Released under MIT license as described in the file LICENSE.
Authors: Gondolin Team
-/

module

public import NN.Library

/-!
# Gondolin

Root umbrella import.

This re-exports `NN.Library`, the curated umbrella for Gondolin's reusable library surface.
Examples and CLI registries are documented as additional `NN:docs` roots, but they do not sit under
`import NN` because many examples intentionally import `NN`.

For subsystem-specific imports, use the `NN/Entrypoint/*` modules.
-/

@[expose] public section
