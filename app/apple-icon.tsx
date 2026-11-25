import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

/* Home-screen icons need a solid background (iOS fills transparency with black and applies its own rounded mask),
   so the face from app/icon.svg sits in white on the brand blue here. */
const mark = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" fill="#1f5eff"/>
  <g transform="rotate(-10 32 33)">
    <rect x="22.5" y="17" width="6.5" height="14" rx="3.25" fill="#fff"/>
    <rect x="35" y="17" width="6.5" height="14" rx="3.25" fill="#fff"/>
    <path d="M20.5 40q11.5 9 23 0" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>
  </g>
</svg>`;

export default function AppleIcon() {
  return new ImageResponse(
    <img alt="" width={size.width} height={size.height} src={`data:image/svg+xml;base64,${Buffer.from(mark).toString("base64")}`} />,
    { ...size },
  );
}
