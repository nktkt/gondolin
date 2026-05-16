import { ImageResponse } from "next/og";
import { siteConfig } from "@/lib/site-config";

// Required for `output: "export"` — generate this image at build time.
export const dynamic = "force-static";

export const alt = "Gondolin — Formalizing Neural Networks in Lean";
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = "image/png";

export default function OpengraphImage() {
  // Keep the subtitle to a single tidy line.
  const subtitle = siteConfig.description.split(".")[0].trim() + ".";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#020617",
          backgroundImage:
            "radial-gradient(900px 500px at 78% 8%, rgba(56, 189, 248, 0.18), transparent 60%), radial-gradient(700px 600px at 8% 100%, rgba(99, 102, 241, 0.16), transparent 55%)",
          padding: 72,
          fontFamily:
            "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        }}
      >
        {/* Wordmark */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 18,
          }}
        >
          <div
            style={{
              width: 64,
              height: 64,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "linear-gradient(135deg, #1e293b 0%, #020617 100%)",
              borderRadius: 16,
              border: "2px solid rgba(148, 163, 184, 0.22)",
              fontSize: 38,
              fontWeight: 700,
              color: "#f1f5f9",
              lineHeight: 1,
            }}
          >
            λ
          </div>
          <div
            style={{
              fontSize: 34,
              fontWeight: 700,
              color: "#f1f5f9",
              letterSpacing: -0.5,
            }}
          >
            {siteConfig.name}
          </div>
        </div>

        {/* Headline + subtitle */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 24,
          }}
        >
          <div
            style={{
              fontSize: 76,
              fontWeight: 800,
              color: "#f8fafc",
              letterSpacing: -1.5,
              lineHeight: 1.05,
              maxWidth: 940,
            }}
          >
            Formalizing Neural Networks in Lean
          </div>
          <div
            style={{
              fontSize: 30,
              fontWeight: 400,
              color: "#94a3b8",
              lineHeight: 1.4,
              maxWidth: 920,
            }}
          >
            {subtitle}
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            fontSize: 24,
            fontWeight: 500,
            color: "#64748b",
          }}
        >
          torchlean.org
        </div>
      </div>
    ),
    {
      ...size,
    }
  );
}
