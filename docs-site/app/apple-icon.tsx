import { ImageResponse } from "next/og";

// Required for `output: "export"` — generate this image at build time.
export const dynamic = "force-static";

export const size = {
  width: 180,
  height: 180,
};
export const contentType = "image/png";

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
          background: "#020617",
          padding: 22,
        }}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "linear-gradient(135deg, #1e293b 0%, #020617 100%)",
            borderRadius: 36,
            border: "2px solid rgba(148, 163, 184, 0.18)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 104,
              fontWeight: 700,
              color: "#f1f5f9",
              lineHeight: 1,
              marginTop: -6,
            }}
          >
            λ
          </div>
        </div>
      </div>
    ),
    {
      ...size,
    }
  );
}
