import { ImageResponse } from "next/og";

// Required for `output: "export"` — generate this image at build time.
export const dynamic = "force-static";

export const size = {
  width: 32,
  height: 32,
};
export const contentType = "image/png";

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
          background: "linear-gradient(135deg, #1e293b 0%, #020617 100%)",
          borderRadius: 7,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 22,
            fontWeight: 700,
            color: "#f1f5f9",
            lineHeight: 1,
            // Nudge the lambda to sit optically centered.
            marginTop: -1,
          }}
        >
          λ
        </div>
      </div>
    ),
    {
      ...size,
    }
  );
}
