# Hi-Puter visual system

## Reference findings

The light reference is a pale blue, lavender, and mint field with no hard section bands. A compact white navigation pill floats inside the page with low-contrast links and a blue gradient CTA. The hero is split: dense black sans-serif copy on the left, an airy technical grid and frosted glass focal object on the right. Controls are fully rounded, cards use translucent white borders, and shadows stay broad and soft. Small floating chips use white glass and slight depth blur.

The dark reference contributes only atmosphere: a very dark navy canvas with quiet indigo and blue radial glows. It should feel calm and spacious, with low-alpha borders and no saturated color bands. The orb remains transparent and keeps its ribbon colors unchanged between themes.

The voice effect is represented as a transparent frosted sphere. Its body is built from cool, pale lavender shading and the interior ribbon moves through violet, blue, and cyan. The ribbon is a deterministic parametric band with hairline strands, clipped to the sphere and redrawn at the element size.

## Tokens

All tokens live as CSS variables at the top of `app/globals.css`.

| Role | Variable | Light | Dark |
| --- | --- | --- | --- |
| Canvas | `--canvas` | `#f5f7fc` + soft blue/cyan glows | `#070a13` + indigo glows |
| Surface | `--panel` | `rgba(255,255,255,.78)` | `rgba(17,23,40,.7)` |
| Raised surface | `--panel-strong` | `#ffffff` | `#0f1528` |
| Text | `--ink` | `#0b1020` | `#e9edf7` |
| Muted text | `--muted` | `#4a5468` | `#a0a9be` |
| Faint text | `--faint` | `#6b7489` | `#737d96` |
| Border | `--line` / `--line-strong` | `rgba(15,23,42,.08 / .14)` | `rgba(148,163,200,.12 / .2)` |
| Accent text + icons | `--primary` | `#2f5bea` | `#7ea2ff` |
| Filled controls | `--brand` / `--brand-hover` | `#2f5bea` / `#2449c9` | `#3d6ef5` / `#5583ff` |
| Signal cyan | `--accent` | `#0891b2` | `#22d3ee` |
| Positive state | `--success` | `#059669` | `#34d399` |

## Icons

UI icons come from `lucide-react` (1.5–2px stroke, 13–19px in UI, 26px in feature chips). Platform logos (Windows, Linux) come from `react-icons/fa6`. Icons are always decorative (`aria-hidden`) next to a visible text label. Feature icons sit in an `.icon-chip`: a tinted rounded square using `--brand-soft` and `--brand-ring`.

## Geometry and motion

- Content width is 1180px, with 96px desktop and 64px mobile section padding.
- Controls are 10px or fully pill-shaped; cards use 18px to 28px radii.
- Ambient layers fade through opacity over 300ms. Gradients do not transition.
- The orb uses a 4.32 second deterministic loop, pauses off-screen and when the tab is hidden, and renders one static frame for reduced motion.
- Decorative motion is slow and low amplitude. Interactive transitions are 180ms ease-out.
