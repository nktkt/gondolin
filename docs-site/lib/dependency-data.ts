// Auto-extracted from the gondolin repo home_page/graphs/dependency-audit.json.
// Trimmed to the layer-graph + stats subset (the 873-module / 3216-edge raw
// lists are intentionally dropped to keep the bundle small).

export type LayerEdge = { src_layer: string; dst_layer: string; count: number };
export type LayerSize = { layer: string; files: number; lines: number };
export type HubModule = { module: string; count: number };

export interface DependencyData {
  summary: {
    modules: number;
    import_edges: number;
    internal_import_edges: number;
    public_import_edges: number;
    private_import_edges: number;
    critical_path_import_edges: number;
    layers: string[];
    errors: number;
    warnings: number;
    findings: number;
    critical_path_excluded_umbrellas: string[];
  };
  code_stats: {
    total_lines: number;
    code_lines: number;
    blank_or_comment_lines: number;
    lean_files: number;
    declarations: number;
    theorem_like_declarations: number;
    declaration_counts: Record<string, number>;
    layer_sizes: LayerSize[];
    top_level_files: { directory: string; files: number }[];
  };
  layer_edges: LayerEdge[];
  top_fan_in: HubModule[];
  top_fan_out: HubModule[];
}

export const dependencyData: DependencyData = {
  "summary": {
    "critical_path_excluded_umbrellas": [
      "NN",
      "NN.CI.All",
      "NN.Examples.Zoo",
      "NN.Library",
      "NN.Tests.Suite",
      "NN.Verification.CLI"
    ],
    "critical_path_import_edges": 33,
    "errors": 0,
    "findings": 0,
    "import_edges": 3216,
    "internal_import_edges": 2668,
    "layers": [
      "Library",
      "NN",
      "NN.API",
      "NN.CI",
      "NN.Entrypoint",
      "NN.Examples",
      "NN.Floats",
      "NN.GraphSpec",
      "NN.IR",
      "NN.MLTheory",
      "NN.Proofs",
      "NN.Runtime",
      "NN.Spec",
      "NN.Tensor",
      "NN.Tests",
      "NN.Verification",
      "Widgets",
      "blueprint",
      "lakefile",
      "scripts"
    ],
    "modules": 873,
    "private_import_edges": 333,
    "public_import_edges": 2883,
    "warnings": 0
  },
  "code_stats": {
    "blank_or_comment_lines": 93345,
    "code_lines": 180957,
    "declaration_counts": {
      "abbrev": 685,
      "axiom": 2,
      "class": 24,
      "def": 7267,
      "inductive": 86,
      "instance": 227,
      "lemma": 646,
      "opaque": 93,
      "structure": 503,
      "theorem": 1323
    },
    "declarations": 10856,
    "layer_sizes": [
      {
        "files": 114,
        "layer": "NN.Proofs",
        "lines": 54516
      },
      {
        "files": 132,
        "layer": "NN.Runtime",
        "lines": 47768
      },
      {
        "files": 114,
        "layer": "NN.MLTheory",
        "lines": 40458
      },
      {
        "files": 116,
        "layer": "NN.Spec",
        "lines": 31055
      },
      {
        "files": 60,
        "layer": "NN.Floats",
        "lines": 24442
      },
      {
        "files": 110,
        "layer": "NN.Examples",
        "lines": 17459
      },
      {
        "files": 40,
        "layer": "NN.API",
        "lines": 14235
      },
      {
        "files": 49,
        "layer": "blueprint",
        "lines": 13217
      },
      {
        "files": 40,
        "layer": "NN.Verification",
        "lines": 11696
      },
      {
        "files": 34,
        "layer": "NN.Tests",
        "lines": 6056
      },
      {
        "files": 17,
        "layer": "Widgets",
        "lines": 4767
      },
      {
        "files": 21,
        "layer": "NN.GraphSpec",
        "lines": 4284
      },
      {
        "files": 6,
        "layer": "NN.IR",
        "lines": 2354
      },
      {
        "files": 1,
        "layer": "NN.Tensor",
        "lines": 752
      },
      {
        "files": 12,
        "layer": "NN.Entrypoint",
        "lines": 518
      },
      {
        "files": 3,
        "layer": "NN.CI",
        "lines": 417
      },
      {
        "files": 1,
        "layer": "lakefile",
        "lines": 190
      },
      {
        "files": 1,
        "layer": "Library",
        "lines": 48
      },
      {
        "files": 1,
        "layer": "scripts",
        "lines": 47
      },
      {
        "files": 1,
        "layer": "NN",
        "lines": 23
      }
    ],
    "lean_files": 873,
    "theorem_like_declarations": 1969,
    "top_level_files": [
      {
        "directory": "NN",
        "files": 821
      },
      {
        "directory": "blueprint",
        "files": 49
      },
      {
        "directory": "NN.lean",
        "files": 1
      },
      {
        "directory": "lakefile.lean",
        "files": 1
      },
      {
        "directory": "scripts",
        "files": 1
      }
    ],
    "total_lines": 274302
  },
  "layer_edges": [
    {
      "count": 297,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Spec"
    },
    {
      "count": 267,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.Runtime"
    },
    {
      "count": 196,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 196,
      "dst_layer": "NN.Proofs",
      "src_layer": "NN.Proofs"
    },
    {
      "count": 144,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.Floats"
    },
    {
      "count": 142,
      "dst_layer": "NN.Examples",
      "src_layer": "NN.Examples"
    },
    {
      "count": 88,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.CI"
    },
    {
      "count": 76,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 69,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.CI"
    },
    {
      "count": 69,
      "dst_layer": "NN.Verification",
      "src_layer": "NN.Verification"
    },
    {
      "count": 57,
      "dst_layer": "NN.API",
      "src_layer": "NN.API"
    },
    {
      "count": 57,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Proofs"
    },
    {
      "count": 52,
      "dst_layer": "NN.Tests",
      "src_layer": "NN.Tests"
    },
    {
      "count": 49,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.CI"
    },
    {
      "count": 48,
      "dst_layer": "NN.API",
      "src_layer": "NN.Examples"
    },
    {
      "count": 45,
      "dst_layer": "NN",
      "src_layer": "NN.Examples"
    },
    {
      "count": 42,
      "dst_layer": "NN.Proofs",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 42,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.Tests"
    },
    {
      "count": 37,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Runtime"
    },
    {
      "count": 36,
      "dst_layer": "NN.Proofs",
      "src_layer": "NN.CI"
    },
    {
      "count": 35,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Tests"
    },
    {
      "count": 33,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.Examples"
    },
    {
      "count": 28,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.CI"
    },
    {
      "count": 26,
      "dst_layer": "NN.Verification",
      "src_layer": "NN.Examples"
    },
    {
      "count": 25,
      "dst_layer": "NN.GraphSpec",
      "src_layer": "NN.GraphSpec"
    },
    {
      "count": 24,
      "dst_layer": "NN.Verification",
      "src_layer": "NN.CI"
    },
    {
      "count": 23,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Examples"
    },
    {
      "count": 18,
      "dst_layer": "NN.Entrypoint",
      "src_layer": "NN.Tests"
    },
    {
      "count": 17,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.API"
    },
    {
      "count": 17,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.API"
    },
    {
      "count": 17,
      "dst_layer": "Widgets",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 15,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 15,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.Verification"
    },
    {
      "count": 15,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Verification"
    },
    {
      "count": 15,
      "dst_layer": "NN",
      "src_layer": "blueprint"
    },
    {
      "count": 15,
      "dst_layer": "NN.Runtime",
      "src_layer": "blueprint"
    },
    {
      "count": 14,
      "dst_layer": "NN.Tests",
      "src_layer": "NN.CI"
    },
    {
      "count": 14,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 14,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 13,
      "dst_layer": "NN.API",
      "src_layer": "NN.CI"
    },
    {
      "count": 12,
      "dst_layer": "NN.Entrypoint",
      "src_layer": "Library"
    },
    {
      "count": 12,
      "dst_layer": "NN.Floats",
      "src_layer": "blueprint"
    },
    {
      "count": 11,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.Examples"
    },
    {
      "count": 10,
      "dst_layer": "NN.Entrypoint",
      "src_layer": "NN.CI"
    },
    {
      "count": 10,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 9,
      "dst_layer": "NN.GraphSpec",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 9,
      "dst_layer": "NN.Verification",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 9,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.Proofs"
    },
    {
      "count": 8,
      "dst_layer": "NN.Entrypoint",
      "src_layer": "NN.Examples"
    },
    {
      "count": 8,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.Verification"
    },
    {
      "count": 7,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.GraphSpec"
    },
    {
      "count": 7,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.IR"
    },
    {
      "count": 7,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.Proofs"
    },
    {
      "count": 7,
      "dst_layer": "NN.Proofs",
      "src_layer": "blueprint"
    },
    {
      "count": 6,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 6,
      "dst_layer": "NN.IR",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 6,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.Examples"
    },
    {
      "count": 6,
      "dst_layer": "NN.Proofs",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 5,
      "dst_layer": "NN.IR",
      "src_layer": "NN.Examples"
    },
    {
      "count": 5,
      "dst_layer": "NN.IR",
      "src_layer": "NN.IR"
    },
    {
      "count": 5,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.Runtime"
    },
    {
      "count": 5,
      "dst_layer": "NN.API",
      "src_layer": "NN.Verification"
    },
    {
      "count": 5,
      "dst_layer": "NN.Runtime",
      "src_layer": "Widgets"
    },
    {
      "count": 5,
      "dst_layer": "NN.Entrypoint",
      "src_layer": "blueprint"
    },
    {
      "count": 4,
      "dst_layer": "NN.API",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 4,
      "dst_layer": "NN.Entrypoint",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 4,
      "dst_layer": "NN.Proofs",
      "src_layer": "NN.Runtime"
    },
    {
      "count": 4,
      "dst_layer": "NN.Tensor",
      "src_layer": "NN.Runtime"
    },
    {
      "count": 4,
      "dst_layer": "NN",
      "src_layer": "NN.Tests"
    },
    {
      "count": 4,
      "dst_layer": "NN.MLTheory",
      "src_layer": "blueprint"
    },
    {
      "count": 3,
      "dst_layer": "NN.Examples",
      "src_layer": "NN.CI"
    },
    {
      "count": 3,
      "dst_layer": "NN.Proofs",
      "src_layer": "NN.Examples"
    },
    {
      "count": 3,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.GraphSpec"
    },
    {
      "count": 3,
      "dst_layer": "NN.Verification",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 3,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.Proofs"
    },
    {
      "count": 2,
      "dst_layer": "NN.Tensor",
      "src_layer": "NN.API"
    },
    {
      "count": 2,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 2,
      "dst_layer": "NN.GraphSpec",
      "src_layer": "NN.Examples"
    },
    {
      "count": 2,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Floats"
    },
    {
      "count": 2,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.IR"
    },
    {
      "count": 2,
      "dst_layer": "NN.IR",
      "src_layer": "NN.Runtime"
    },
    {
      "count": 2,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.Runtime"
    },
    {
      "count": 2,
      "dst_layer": "NN.Verification",
      "src_layer": "NN.Runtime"
    },
    {
      "count": 2,
      "dst_layer": "NN.Spec",
      "src_layer": "NN.Tensor"
    },
    {
      "count": 2,
      "dst_layer": "NN.Verification",
      "src_layer": "NN.Tests"
    },
    {
      "count": 2,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.Verification"
    },
    {
      "count": 2,
      "dst_layer": "NN.IR",
      "src_layer": "NN.Verification"
    },
    {
      "count": 2,
      "dst_layer": "NN.IR",
      "src_layer": "blueprint"
    },
    {
      "count": 2,
      "dst_layer": "NN.Spec",
      "src_layer": "blueprint"
    },
    {
      "count": 1,
      "dst_layer": "Library",
      "src_layer": "NN"
    },
    {
      "count": 1,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.API"
    },
    {
      "count": 1,
      "dst_layer": "NN.GraphSpec",
      "src_layer": "NN.API"
    },
    {
      "count": 1,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.API"
    },
    {
      "count": 1,
      "dst_layer": "NN.CI",
      "src_layer": "NN.CI"
    },
    {
      "count": 1,
      "dst_layer": "NN.Entrypoint",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 1,
      "dst_layer": "NN.Tensor",
      "src_layer": "NN.Entrypoint"
    },
    {
      "count": 1,
      "dst_layer": "NN.Tensor",
      "src_layer": "NN.Examples"
    },
    {
      "count": 1,
      "dst_layer": "NN.Proofs",
      "src_layer": "NN.Floats"
    },
    {
      "count": 1,
      "dst_layer": "NN.Runtime",
      "src_layer": "NN.Floats"
    },
    {
      "count": 1,
      "dst_layer": "NN.IR",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 1,
      "dst_layer": "NN.Tensor",
      "src_layer": "NN.MLTheory"
    },
    {
      "count": 1,
      "dst_layer": "NN.MLTheory",
      "src_layer": "NN.Spec"
    },
    {
      "count": 1,
      "dst_layer": "NN.Floats",
      "src_layer": "NN.Tensor"
    },
    {
      "count": 1,
      "dst_layer": "NN.IR",
      "src_layer": "NN.Tests"
    },
    {
      "count": 1,
      "dst_layer": "NN.Entrypoint",
      "src_layer": "NN.Verification"
    },
    {
      "count": 1,
      "dst_layer": "NN.Examples",
      "src_layer": "NN.Verification"
    },
    {
      "count": 1,
      "dst_layer": "NN.Tensor",
      "src_layer": "NN.Verification"
    },
    {
      "count": 1,
      "dst_layer": "NN.Verification",
      "src_layer": "blueprint"
    }
  ],
  "top_fan_in": [
    {
      "count": 64,
      "module": "NN"
    },
    {
      "count": 39,
      "module": "NN.Spec.Core.Tensor"
    },
    {
      "count": 36,
      "module": "NN.Spec.Core.TensorOps"
    },
    {
      "count": 32,
      "module": "NN.Spec.Core.Context"
    },
    {
      "count": 31,
      "module": "NN.Spec.Core.TensorReductionShape"
    },
    {
      "count": 31,
      "module": "NN.Spec.Layers.Activation"
    },
    {
      "count": 29,
      "module": "NN.MLTheory.CROWN.Graph"
    },
    {
      "count": 27,
      "module": "NN.Floats.IEEEExec.Exec32"
    },
    {
      "count": 24,
      "module": "NN.Spec.Module.SpecModule"
    },
    {
      "count": 23,
      "module": "NN.MLTheory.CROWN.Core"
    },
    {
      "count": 21,
      "module": "NN.Entrypoint.Tensor"
    },
    {
      "count": 21,
      "module": "NN.Runtime.Autograd.Engine.Core"
    },
    {
      "count": 18,
      "module": "NN.API.Public"
    },
    {
      "count": 18,
      "module": "NN.Runtime.Autograd.Engine.Cuda.Ops"
    },
    {
      "count": 17,
      "module": "NN.Verification.Gondolin.Compile"
    },
    {
      "count": 16,
      "module": "NN.Runtime.Autograd.Gondolin.NN"
    },
    {
      "count": 15,
      "module": "NN.Runtime.Context"
    },
    {
      "count": 15,
      "module": "NN.Spec.Core.Utils"
    },
    {
      "count": 15,
      "module": "NN.Spec.Layers.Linear"
    },
    {
      "count": 15,
      "module": "NN.Tests.Runtime.Cuda.Utils"
    }
  ],
  "top_fan_out": [
    {
      "count": 333,
      "module": "NN.CI.All"
    },
    {
      "count": 42,
      "module": "NN.Entrypoint.Proofs"
    },
    {
      "count": 28,
      "module": "NN.Spec.Module"
    },
    {
      "count": 26,
      "module": "NN.Spec.Models"
    },
    {
      "count": 24,
      "module": "NN.Examples.Zoo"
    },
    {
      "count": 23,
      "module": "NN.MLTheory.API"
    },
    {
      "count": 19,
      "module": "NN.Tests.Runtime.Floats.ModelsSmoke"
    },
    {
      "count": 18,
      "module": "NN.Spec.Layers"
    },
    {
      "count": 17,
      "module": "NN.Entrypoint.Widgets"
    },
    {
      "count": 17,
      "module": "NN.Floats.IEEEExec"
    },
    {
      "count": 16,
      "module": "NN.Entrypoint.Runtime"
    },
    {
      "count": 16,
      "module": "NN.Tests.Runtime.Cuda.Suite"
    },
    {
      "count": 14,
      "module": "NN.Proofs.Autograd.Coverage"
    },
    {
      "count": 14,
      "module": "NN.Runtime.Autograd.Compiled.IRExec.Correctness.SemanticEquivalence"
    },
    {
      "count": 13,
      "module": "NN.Examples.BugZoo.All"
    },
    {
      "count": 13,
      "module": "NN.Runtime.Autograd.Engine.Cuda"
    },
    {
      "count": 13,
      "module": "NN.Runtime.Autograd.Gondolin"
    },
    {
      "count": 12,
      "module": "NN.API.Public"
    },
    {
      "count": 12,
      "module": "NN.API.Runtime"
    },
    {
      "count": 12,
      "module": "NN.Library"
    }
  ]
};
