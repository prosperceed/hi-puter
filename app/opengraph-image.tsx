import { ImageResponse } from "next/og";

export const alt = "Hi-Puter, your computer at your command";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/* Same face as components/brand/Mark.tsx, in the light blue used on dark backgrounds. */
const mark = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 10 44 44">
  <g transform="rotate(-10 32 33)" fill="#6b96ff">
    <rect x="22.5" y="17" width="6.5" height="14" rx="3.25"/>
    <rect x="35" y="17" width="6.5" height="14" rx="3.25"/>
    <path d="M20.5 40q11.5 9 23 0" fill="none" stroke="#6b96ff" stroke-width="5" stroke-linecap="round"/>
  </g>
</svg>`;

export default function Image() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: "#000", color: "#f4f4f5", fontFamily: "sans-serif", position: "relative", overflow: "hidden" }}>
        <div style={{ height: 8, width: "100%", background: "linear-gradient(90deg, #e33cf2 0%, #f7c843 18%, #f4503b 36%, #ec8f9a 50%, #cdd7ef 62%, #6b96ff 80%, #1f5eff 100%)" }} />
        <div style={{ position: "absolute", left: 100, bottom: -560, width: 1000, height: 760, borderRadius: "50%", background: "radial-gradient(closest-side, #ff2bd6 0%, #ff3b3b 20%, #ff7a1f 31%, #f7c843 41%, rgba(47,107,255,0.95) 55%, rgba(31,70,220,0.5) 72%, rgba(0,0,0,0) 100%)" }} />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 72 }}>
          <img alt="" width={72} height={72} src={`data:image/svg+xml;base64,${Buffer.from(mark).toString("base64")}`} />
          <div style={{ marginTop: 26, color: "#9b9ba3", fontSize: 24, letterSpacing: 3 }}>HI-PUTER · LOCAL VOICE ASSISTANT</div>
          <div style={{ marginTop: 30, fontSize: 84, fontWeight: 400, letterSpacing: -3.8 }}>Your computer,</div>
          <div style={{ fontSize: 84, fontWeight: 400, letterSpacing: -3.8 }}>at your command.</div>
          <div style={{ marginTop: 30, color: "#9b9ba3", fontSize: 26 }}>Windows + Linux · Audio stays local</div>
        </div>
      </div>
    ),
    { ...size },
  );
}
