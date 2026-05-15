# Gondlin schemas

This directory holds machine-readable schemas for artifacts that cross the
boundary between Gondlin and external producers/consumers.

Current contents:

- `certificate-v1.json` — the `Certificate.v1` envelope used by `lake exe verify`.
- `examples/` — small example documents that conform to the schemas here.

## `certificate-v1.json`

A JSON Schema 2020-12 document describing the common envelope shared by every
verifier family under `NN/Verification/`:

- `NN.Verification.Robustness` (adversarial robustness certificates)
- `NN.Verification.ODE` (ODE solver soundness certificates)
- `NN.Verification.PINN` (Physics-Informed NN residual bounds)
- `NN.Verification.Geometry3D` (geometric property certificates)
- `NN.Verification.Splines` (piecewise polynomial spline certificates)

The envelope captures the `claim`, the producer-supplied `evidence`, an optional
`lean_proof_script`, and a `checked_by` attestation. Per-`kind` claim shapes are
enforced by `if`/`then` blocks at the top level (the discriminator is `kind`).

The Lean side will read this format via a (future) `NN.Verification.Cert.v1`
module; the four currently-shipping verifier families will migrate to v1 with
backward-compatible readers for the v0 ad-hoc formats. Migration sequencing is
tracked in the private `nktkt/gondlin-docs` companion repository.

## Validating a certificate

Pick whichever validator is already installed in your environment.

### Python (`jsonschema`)

```sh
pip install jsonschema
python3 -c '
import json
from jsonschema import Draft202012Validator
schema = json.load(open("schemas/certificate-v1.json"))
instance = json.load(open("schemas/examples/robustness-example.json"))
Draft202012Validator(schema).validate(instance)
print("ok")
'
```

### Node (`ajv`)

```sh
npm install -g ajv-cli
ajv validate \
  --spec=draft2020 \
  -s schemas/certificate-v1.json \
  -d schemas/examples/robustness-example.json
```

Both validators must accept JSON Schema draft 2020-12; older drafts will
silently mis-handle the top-level `if`/`then` discriminator.
