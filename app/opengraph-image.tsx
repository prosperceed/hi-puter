import { ImageResponse } from "next/og";

export const alt = "Hi-Puter, your computer at your command";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: "#000", color: "#f4f4f5", fontFamily: "sans-serif", position: "relative", overflow: "hidden" }}>
        <div style={{ height: 8, width: "100%", background: "linear-gradient(90deg, #e33cf2 0%, #f7c843 18%, #f4503b 36%, #ec8f9a 50%, #cdd7ef 62%, #6b96ff 80%, #1f5eff 100%)" }} />
        <div style={{ position: "absolute", left: 100, bottom: -560, width: 1000, height: 760, borderRadius: "50%", background: "radial-gradient(closest-side, #ff2bd6 0%, #ff3b3b 20%, #ff7a1f 31%, #f7c843 41%, rgba(47,107,255,0.95) 55%, rgba(31,70,220,0.5) 72%, rgba(0,0,0,0) 100%)" }} />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 110 }}>
          <div style={{ color: "#9b9ba3", fontSize: 24, letterSpacing: 3 }}>HI-PUTER · LOCAL VOICE ASSISTANT</div>
          <div style={{ marginTop: 34, fontSize: 84, fontWeight: 400, letterSpacing: -3 }}>Your computer,</div>
          <div style={{ fontSize: 84, fontWeight: 400, letterSpacing: -3 }}>at your command.</div>
          <div style={{ marginTop: 30, color: "#9b9ba3", fontSize: 26 }}>Windows + Linux · Audio stays local</div>
        </div>
      </div>
    ),
    { ...size },
  );
}
