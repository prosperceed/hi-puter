import { ImageResponse } from "next/og";

export const alt = "Hi-Puter, your computer at your command";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() { return new ImageResponse(<div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", padding: "80px", background: "#d3d7fc", color: "#0a0e1a", fontFamily: "sans-serif" }}><div style={{ color: "#5189e6", fontSize: 24 }}>HI-PUTER / LOCAL VOICE ASSISTANT</div><div style={{ marginTop: 30, fontSize: 82, fontWeight: 800, letterSpacing: -5 }}>Your computer,</div><div style={{ fontSize: 82, fontWeight: 800, color: "#5189e6", letterSpacing: -5 }}>at your command.</div><div style={{ marginTop: 35, color: "#5b6478", fontSize: 25 }}>Windows + Linux · Audio stays local</div></div>, { ...size }); }
