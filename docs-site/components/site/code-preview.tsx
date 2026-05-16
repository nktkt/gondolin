import { cn } from "@/lib/utils";

/**
 * Pre-styled, syntax-highlighted Lean snippet rendered as static spans.
 *
 * This is a placeholder until Shiki is wired into the runtime. Tokens are
 * hand-coloured with Tailwind utilities so the home page can ship without
 * a build-time highlighter.
 */
export function CodePreview({
  className,
  filename = "Gondolin.lean",
}: {
  className?: string;
  filename?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-border bg-zinc-950 text-[13px] shadow-2xl shadow-black/30 ring-1 ring-white/5",
        className,
      )}
    >
      <div className="flex items-center gap-2 border-b border-white/5 bg-zinc-900/80 px-4 py-2.5">
        <span className="flex items-center gap-1.5">
          <span className="size-3 rounded-full bg-red-500/70" aria-hidden />
          <span className="size-3 rounded-full bg-yellow-500/70" aria-hidden />
          <span className="size-3 rounded-full bg-green-500/70" aria-hidden />
        </span>
        <span className="ml-2 font-mono text-xs text-zinc-400">{filename}</span>
      </div>
      <pre className="overflow-x-auto px-5 py-5 font-mono text-zinc-200 leading-relaxed">
        <code>
          <span className="text-purple-400">import</span>
          <span className="text-sky-300"> NN.API.Public</span>
          {"\n"}
          <span className="text-purple-400">open</span>
          <span className="text-sky-300"> NN</span>
          {"\n\n"}
          <span className="text-purple-400">def</span>
          <span className="text-sky-300"> mlp</span>
          <span className="text-zinc-400"> : </span>
          <span className="text-sky-300">Spec.Model</span>
          <span className="text-zinc-400"> :=</span>
          {"\n  "}
          <span className="text-sky-300">Linear</span>
          <span className="text-zinc-400"> (</span>
          <span className="text-purple-400">in</span>
          <span className="text-zinc-400"> := </span>
          <span className="text-emerald-300">4</span>
          <span className="text-zinc-400">) (</span>
          <span className="text-purple-400">out</span>
          <span className="text-zinc-400"> := </span>
          <span className="text-emerald-300">8</span>
          <span className="text-zinc-400">)</span>
          {"\n    "}
          <span className="text-zinc-400">|&gt;.</span>
          <span className="text-sky-300">then</span>
          <span className="text-sky-300"> ReLU</span>
          {"\n    "}
          <span className="text-zinc-400">|&gt;.</span>
          <span className="text-sky-300">then</span>
          <span className="text-zinc-400"> (</span>
          <span className="text-sky-300">Linear</span>
          <span className="text-zinc-400"> (</span>
          <span className="text-purple-400">in</span>
          <span className="text-zinc-400"> := </span>
          <span className="text-emerald-300">8</span>
          <span className="text-zinc-400">) (</span>
          <span className="text-purple-400">out</span>
          <span className="text-zinc-400"> := </span>
          <span className="text-emerald-300">1</span>
          <span className="text-zinc-400">))</span>
          {"\n\n"}
          <span className="text-zinc-400">#eval</span>
          <span className="text-sky-300"> mlp</span>
          <span className="text-zinc-400">.</span>
          <span className="text-sky-300">run</span>
          <span className="text-zinc-400"> (</span>
          <span className="text-sky-300">Tensor</span>
          <span className="text-zinc-400">.</span>
          <span className="text-sky-300">ones</span>
          <span className="text-zinc-400"> [</span>
          <span className="text-emerald-300">1</span>
          <span className="text-zinc-400">, </span>
          <span className="text-emerald-300">4</span>
          <span className="text-zinc-400">])</span>
        </code>
      </pre>
    </div>
  );
}

export default CodePreview;
