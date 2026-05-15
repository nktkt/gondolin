#!/usr/bin/env python3
"""
Gondlin SBOM generator (Phase 7.4 release prep).

Produces a minimal SPDX 2.3 JSON document describing Gondlin and its direct
Lake dependencies, suitable for attaching to GitHub Releases as a
license/supply-chain artifact.

Sources of truth:

  - ``lake-manifest.json`` for dependency name, revision, and download URL.
  - ``lakefile.lean``      for Gondlin's own ``version := v!"x.y.z"`` literal.

License inference is intentionally simple: we keep a short hand-curated table
of upstream license SPDX identifiers (all our Lake deps are Apache-2.0). Any
package we have not vetted falls back to ``NOASSERTION``, the SPDX-defined
placeholder for "I could not determine this".

CLI:

  --output PATH    Write SBOM to ``PATH`` instead of stdout.
  --pretty         Pretty-print JSON (2-space indent).
  --summary        Emit a human-readable text summary instead of JSON.

Style: stdlib only, no third-party imports.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Iterable


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "lake-manifest.json"
LAKEFILE_PATH = REPO_ROOT / "lakefile.lean"

TOOL_VERSION = "gondlin-sbom-generate/0.1"

# Hand-vetted upstream licenses for Gondlin's Lake dependency closure. All are
# Apache-2.0 today (matches THIRD_PARTY_NOTICES.md). Anything not listed here
# falls back to NOASSERTION, the SPDX placeholder for "license not yet
# determined" — that surfaces gaps explicitly instead of guessing.
LICENSE_TABLE: dict[str, str] = {
    "mathlib": "Apache-2.0",
    "doc-gen4": "Apache-2.0",
    "«doc-gen4»": "Apache-2.0",
    "Comparator": "Apache-2.0",
    "lean4export": "Apache-2.0",
    "batteries": "Apache-2.0",
    "aesop": "Apache-2.0",
    "plausible": "Apache-2.0",
}

# Regex for ``version := v!"x.y.z"`` in lakefile.lean. We deliberately allow
# trailing pre-release identifiers (``0.1.0-rc.1``) so future releases work.
_VERSION_RE = re.compile(r'version\s*:=\s*v!"([^"]+)"')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_gondlin_version() -> str:
    """Extract Gondlin's package version from ``lakefile.lean``.

    Returns ``0.0.0-unknown`` if the lakefile can't be parsed; we prefer a
    visibly-broken value over silently emitting a real-looking but wrong SBOM.
    """
    try:
        text = LAKEFILE_PATH.read_text(encoding="utf-8")
    except OSError:
        return "0.0.0-unknown"
    m = _VERSION_RE.search(text)
    if not m:
        return "0.0.0-unknown"
    return m.group(1).strip()


def _sanitize_spdx_id(name: str) -> str:
    """SPDX identifiers must match ``[A-Za-z0-9.-]+``; strip everything else.

    Lake package names occasionally carry French quotes (``«doc-gen4»``); we
    keep the visible name in the ``name`` field but normalize the SPDXID.
    """
    cleaned = re.sub(r"[^A-Za-z0-9.\-]+", "", name)
    return cleaned or "unknown"


def _license_for(pkg_name: str) -> str:
    """Look up a package's SPDX license identifier; default to ``NOASSERTION``.

    We try the exact name first, then strip French quotes (``«...»``) which
    Lake uses to escape hyphens in identifiers — ``«doc-gen4»`` and
    ``doc-gen4`` should resolve identically.
    """
    if pkg_name in LICENSE_TABLE:
        return LICENSE_TABLE[pkg_name]
    stripped = pkg_name.strip("«»")
    if stripped in LICENSE_TABLE:
        return LICENSE_TABLE[stripped]
    return "NOASSERTION"


@dataclass(frozen=True)
class LakePackage:
    """A single entry from ``lake-manifest.json`` — only the fields we render."""

    name: str
    url: str
    rev: str
    input_rev: str
    inherited: bool

    @property
    def spdx_id(self) -> str:
        """Stable SPDX identifier for cross-references in the relationships array."""
        return f"SPDXRef-Package-{_sanitize_spdx_id(self.name)}"


def _load_packages() -> list[LakePackage]:
    """Parse ``lake-manifest.json`` into structured ``LakePackage`` records."""
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    out: list[LakePackage] = []
    for pkg in data.get("packages", []):
        out.append(
            LakePackage(
                name=pkg.get("name", "unknown"),
                url=pkg.get("url", "NOASSERTION"),
                rev=pkg.get("rev", "NOASSERTION"),
                input_rev=pkg.get("inputRev", "") or "",
                inherited=bool(pkg.get("inherited", False)),
            )
        )
    return out


# ---------------------------------------------------------------------------
# SBOM construction
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """Return the current UTC time in SPDX-compatible ISO-8601 (``...Z``)."""
    return _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_sbom(packages: Iterable[LakePackage], version: str) -> dict:
    """Assemble the SPDX 2.3 JSON document as an in-memory dict."""
    created = _utc_now_iso()

    # Document namespace is supposed to be unique per SBOM document; we encode
    # the creation timestamp into the URL so re-runs do not collide.
    namespace = (
        "https://github.com/nktkt/gondlin/sbom/"
        f"{version}/{created.replace(':', '').replace('-', '')}"
    )

    spdx_packages: list[dict] = [
        {
            "SPDXID": "SPDXRef-Package-gondlin",
            "name": "Gondlin",
            "versionInfo": version,
            "downloadLocation": "https://github.com/nktkt/gondlin",
            "licenseDeclared": "MIT",
            "licenseConcluded": "MIT",
            "supplier": "Organization: Gondlin Team",
            "filesAnalyzed": False,
        }
    ]

    relationships: list[dict] = [
        {
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relationshipType": "DESCRIBES",
            "relatedSpdxElement": "SPDXRef-Package-gondlin",
        }
    ]

    # We emit one Package entry per Lake-manifest package and a DEPENDS_ON
    # relationship from Gondlin to every *direct* (non-inherited) dependency.
    # Transitive deps still get Package entries (so an auditor sees them) but
    # not a DEPENDS_ON edge from the root; that matches SPDX semantics for
    # "package described by this document".
    for pkg in packages:
        # downloadLocation should be a VCS URL when available; SPDX has a
        # specific ``git+https://...@<rev>`` form, which is more useful than
        # the bare GitHub URL because it pins to the resolved revision.
        download = pkg.url
        if pkg.url and pkg.url.startswith("https://") and pkg.rev:
            download = f"git+{pkg.url}@{pkg.rev}"

        version_info = pkg.input_rev or pkg.rev or "NOASSERTION"
        license_id = _license_for(pkg.name)

        spdx_packages.append(
            {
                "SPDXID": pkg.spdx_id,
                "name": pkg.name,
                "versionInfo": version_info,
                "downloadLocation": download or "NOASSERTION",
                "licenseDeclared": license_id,
                "licenseConcluded": license_id,
                "filesAnalyzed": False,
                # ``externalRefs`` lets downstream tooling (e.g. Grype, Trivy)
                # locate the upstream by PURL. We use the ``github`` PURL type
                # because every Gondlin dep is hosted on github.com today.
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": _purl_for(pkg),
                    }
                ],
                # Useful audit metadata; not part of the SPDX 2.3 required set
                # but allowed as long as it doesn't conflict.
                "comment": (
                    f"inputRev={pkg.input_rev or 'n/a'}; "
                    f"inherited={'yes' if pkg.inherited else 'no'}"
                ),
            }
        )

        if not pkg.inherited:
            relationships.append(
                {
                    "spdxElementId": "SPDXRef-Package-gondlin",
                    "relationshipType": "DEPENDS_ON",
                    "relatedSpdxElement": pkg.spdx_id,
                }
            )

    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "Gondlin-SBOM",
        "documentNamespace": namespace,
        "creationInfo": {
            "created": created,
            "creators": [f"Tool: {TOOL_VERSION}"],
        },
        "packages": spdx_packages,
        "relationships": relationships,
    }


def _purl_for(pkg: LakePackage) -> str:
    """Best-effort Package URL for a Lake-manifest entry.

    We parse the GitHub URL into ``pkg:github/<owner>/<repo>@<rev>``. Anything
    that doesn't look like a GitHub URL gets a ``pkg:generic`` fallback.
    """
    url = pkg.url or ""
    rev = pkg.rev or ""
    m = re.match(r"^https?://github\.com/([^/]+)/([^/.]+)(?:\.git)?/?$", url)
    if m:
        owner, repo = m.group(1), m.group(2)
        if rev:
            return f"pkg:github/{owner}/{repo}@{rev}"
        return f"pkg:github/{owner}/{repo}"
    # Fallback: encode the bare name; downstream tools can ignore it.
    name = _sanitize_spdx_id(pkg.name).lower()
    if rev:
        return f"pkg:generic/{name}@{rev}"
    return f"pkg:generic/{name}"


# ---------------------------------------------------------------------------
# Output / CLI
# ---------------------------------------------------------------------------


def _summary_text(sbom: dict) -> str:
    """Human-readable summary used by ``--summary``."""
    pkgs = sbom["packages"]
    rels = sbom["relationships"]
    depends_on = [r for r in rels if r["relationshipType"] == "DEPENDS_ON"]

    lines: list[str] = []
    lines.append("Gondlin SBOM summary")
    lines.append(f"  spdxVersion:   {sbom['spdxVersion']}")
    lines.append(f"  created:       {sbom['creationInfo']['created']}")
    lines.append(f"  packages:      {len(pkgs)}")
    lines.append(f"  relationships: {len(rels)} (direct deps: {len(depends_on)})")
    lines.append("")
    lines.append("Packages:")
    for pkg in pkgs:
        lic = pkg.get("licenseDeclared", "NOASSERTION")
        ver = pkg.get("versionInfo", "?")
        lines.append(f"  - {pkg['name']:<22} {ver:<46}  {lic}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args and emit the SBOM (or summary)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Write SBOM to PATH (default: stdout).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON (2-space indent).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Emit a human-readable text summary instead of JSON.",
    )
    args = parser.parse_args(argv)

    if not MANIFEST_PATH.exists():
        print(
            f"sbom_generate: expected lake-manifest.json at {MANIFEST_PATH}",
            file=sys.stderr,
        )
        return 2
    if not LAKEFILE_PATH.exists():
        print(
            f"sbom_generate: expected lakefile.lean at {LAKEFILE_PATH}",
            file=sys.stderr,
        )
        return 2

    version = _read_gondlin_version()
    packages = _load_packages()
    sbom = build_sbom(packages, version)

    if args.summary:
        text = _summary_text(sbom)
        if args.output is not None:
            args.output.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0

    rendered = json.dumps(
        sbom,
        indent=2 if args.pretty else None,
        sort_keys=True,
    )
    if not rendered.endswith("\n"):
        rendered += "\n"

    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
