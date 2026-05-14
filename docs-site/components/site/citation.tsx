import { ExternalLink } from "lucide-react";

import { siteConfig } from "@/lib/site-config";
import { CopyButton } from "@/components/site/copy-button";

const BIBTEX = `@misc{george2026torchleanformalizingneuralnetworks,
      title={TorchLean: Formalizing Neural Networks in Lean},
      author={Robert Joseph George and Jennifer Cruden and Xiangru Zhong and Huan Zhang and Anima Anandkumar},
      year={2026},
      eprint={2602.22631},
      archivePrefix={arXiv},
      primaryClass={cs.MS},
      url={https://arxiv.org/abs/2602.22631},
}`;

export function Citation() {
  return (
    <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 ring-1 ring-foreground/5">
      <div className="flex flex-col gap-1.5">
        <span className="font-mono text-xs uppercase tracking-wide text-muted-foreground">
          Paper
        </span>
        <h2 className="text-balance text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
          TorchLean: Formalizing Neural Networks in Lean
        </h2>
        <p className="text-sm text-muted-foreground">
          Robert Joseph George, Jennifer Cruden, Xiangru Zhong, Huan Zhang,
          Anima Anandkumar &middot; 2026
        </p>
        <a
          href={siteConfig.arxiv}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-1 inline-flex w-fit items-center gap-1.5 text-sm text-primary underline-offset-4 hover:underline"
        >
          arXiv:2602.22631
          <ExternalLink aria-hidden className="size-3.5" />
        </a>
      </div>

      <div className="relative mt-5 overflow-hidden rounded-lg border border-border bg-muted/40">
        <CopyButton
          text={BIBTEX}
          className="absolute top-2 right-2 z-10 size-7"
        />
        <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-foreground/90">
          <code>{BIBTEX}</code>
        </pre>
      </div>
    </div>
  );
}

export default Citation;
