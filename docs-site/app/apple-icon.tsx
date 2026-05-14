import { ImageResponse } from "next/og";

// Required for `output: "export"` — generate this image at build time.
export const dynamic = "force-static";

export const size = {
  width: 180,
  height: 180,
};
export const contentType = "image/png";

/**
 * Apple touch icon — same lambda-as-graph mark as the favicon, scaled up
 * with a little more breathing room and a hairline border.
 */
export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#09090b",
          padding: 18,
        }}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "linear-gradient(145deg, #27272a 0%, #09090b 100%)",
            borderRadius: 40,
            border: "2px solid rgba(148, 163, 184, 0.18)",
          }}
        >
          <svg width="116" height="116" viewBox="0 0 100 100" fill="none">
            <path
              d="M37 22 L76 80"
              stroke="#fafafa"
              strokeWidth="10"
              strokeLinecap="round"
            />
            <path
              d="M51 43 L24 80"
              stroke="#fafafa"
              strokeWidth="10"
              strokeLinecap="round"
            />
            <circle cx="37" cy="22" r="9" fill="#fafafa" />
            <circle cx="76" cy="80" r="9" fill="#fafafa" />
            <circle cx="24" cy="80" r="9" fill="#fafafa" />
          </svg>
        </div>
      </div>
    ),
    {
      ...size,
    }
  );
}
