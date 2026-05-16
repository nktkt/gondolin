import { ImageResponse } from "next/og";

// Required for `output: "export"` — generate this image at build time.
export const dynamic = "force-static";

export const size = {
  width: 32,
  height: 32,
};
export const contentType = "image/png";

/**
 * Gondolin favicon: a lambda drawn as a 3-node graph — the Lean "λ"
 * meeting the neural-network motif. Monochrome, to match the site brand.
 */
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(145deg, #27272a 0%, #09090b 100%)",
          borderRadius: 7,
        }}
      >
        <svg width="32" height="32" viewBox="0 0 100 100" fill="none">
          <path
            d="M37 22 L76 80"
            stroke="#fafafa"
            strokeWidth="11"
            strokeLinecap="round"
          />
          <path
            d="M51 43 L24 80"
            stroke="#fafafa"
            strokeWidth="11"
            strokeLinecap="round"
          />
          <circle cx="37" cy="22" r="9.5" fill="#fafafa" />
          <circle cx="76" cy="80" r="9.5" fill="#fafafa" />
          <circle cx="24" cy="80" r="9.5" fill="#fafafa" />
        </svg>
      </div>
    ),
    {
      ...size,
    }
  );
}
