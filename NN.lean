/-
Copyright (c) 2026 Gondlin
Released under MIT license as described in the file LICENSE.
Authors: Gondlin Team
-/

module

public import NN.Library

/-!
# Gondlin

Root umbrella import.

This re-exports `NN.Library`, the curated umbrella for Gondlin's reusable library surface.
Examples and CLI registries are documented as additional `NN:docs` roots, but they do not sit under
`import NN` because many examples intentionally import `NN`.

For subsystem-specific imports, use the `NN/Entrypoint/*` modules.
-/

@[expose] public section
