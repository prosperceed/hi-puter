# Hi-Puter visual system

## Direction

Black canvas, monochrome interface, one source of color: the **spectrum**. The page sits inside a hairline-bordered frame; sections are separated by full-width rules with small `+` ticks at the corners. Content is laid out as cells divided by 1px lines rather than as floating cards with shadows.

Color appears in only two places:

- **Spectrum bar**: a 4px gradient strip at the very top of the page (magenta → yellow → red → rose → pale lavender → blue).
- **Spectrum glow**: a blurred radial "sunrise" anchored to the bottom edge of a section (magenta core, red, orange, a yellow ring, then a wide blue haze). It is used in the hero, the final CTA, and inside dark panels (wake name output, privacy badge, utility screens).

The hero pairs the glow with a dark **voice console** card that cycles through example commands (listening → working → done). The console and other "device" panels stay dark in both themes.

## Tokens

All tokens are CSS variables at the top of `app/globals.css`. Dark is the default theme.

| Role | Variable | Dark | Light |
| --- | --- | --- | --- |
| Canvas | `--canvas` | `#000000` | `#fafafa` |
| Surface | `--surface` / `--surface-2` | `#0a0a0b` / `#111113` | `#ffffff` / `#f2f2f3` |
| Text | `--ink` | `#f4f4f5` | `#0a0a0b` |
| Muted text | `--muted` | `#9b9ba3` | `#55555c` |
| Faint text | `--faint` | `#6b6b73` | `#85858d` |
| Hairlines | `--line` / `--line-strong` | `rgba(255,255,255,.1 / .22)` | `rgba(10,10,11,.1 / .2)` |
| Solid button | `--btn-solid-bg` | white, black text | black, white text |
| Soft button | `--btn-soft-bg` | `#e4e4e7` | `#e8e8ea` |
| Spectrum | `--spectrum` | `#e33cf2 → #f7c843 → #f4503b → #ec8f9a → #cdd7ef → #6b96ff → #1f5eff` | same |
| Status | `--live` / `--sun` | `#22c55e` / `#f7c843` | same |

## Type

- **Geist** for everything, set light: headlines at weight 400 with `-0.03em` to `-0.035em` tracking.
- **Geist Mono** for eyebrows, labels, step numbers and commands.

## Components

- Buttons are always pills: solid (primary), outlined (secondary), soft grey (tertiary).
- Icons come from `lucide-react` at stroke 1.75–2; platform logos come from `react-icons/fa6`. Icons are monochrome and decorative (`aria-hidden`) next to visible text.
- Icon containers (`.icon-mark`) are outlined rounded squares, not filled chips.

## Motion

- Interactive transitions are 180ms ease-out.
- The console cycles every 1.4s per phase. Status chips use a small waveform, a spinner, or a check.
- `prefers-reduced-motion` collapses all animation and transitions.
