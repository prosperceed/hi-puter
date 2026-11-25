/**
 * The Hi-Puter mark: two eyes and a wide smile, tilted 10° for a bit of character.
 * Colored with `currentColor`; `.mark` sets it to the `--mark` token.
 * Keep the geometry in sync with app/icon.svg, app/apple-icon.tsx and app/opengraph-image.tsx.
 */
export function Mark({ size = 26, className = "" }: { size?: number; className?: string }) {
  return (
    <svg className={`mark ${className}`.trim()} width={size} height={size} viewBox="10 10 44 44" aria-hidden="true" focusable="false">
      <g transform="rotate(-10 32 33)">
        <rect x="22.5" y="17" width="6.5" height="14" rx="3.25" fill="currentColor" />
        <rect x="35" y="17" width="6.5" height="14" rx="3.25" fill="currentColor" />
        <path d="M20.5 40q11.5 9 23 0" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
      </g>
    </svg>
  );
}
