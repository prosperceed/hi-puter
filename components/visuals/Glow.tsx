/** Spectrum glow anchored to the bottom edge of its (relative, overflow-hidden) parent. */
export function Glow({ small = false }: { small?: boolean }) {
  return <div className={small ? "glow small" : "glow"} aria-hidden="true" />;
}
