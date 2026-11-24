# Hi-Puter visual system

## Reference findings

The light reference is a pale blue, lavender, and mint field with no hard section bands. A compact white navigation pill floats inside the page with low-contrast links and a blue gradient CTA. The hero is split: dense black sans-serif copy on the left, an airy technical grid and frosted glass focal object on the right. Controls are fully rounded, cards use translucent white borders, and shadows stay broad and soft. Small floating chips use white glass and slight depth blur.

The dark reference contributes only atmosphere: a very dark navy canvas with quiet indigo and blue radial glows. It should feel calm and spacious, with low-alpha borders and no saturated color bands. The orb remains transparent and keeps its ribbon colors unchanged between themes.

The voice effect is represented as a transparent frosted sphere. Its body is built from cool, pale lavender shading and the interior ribbon moves through violet, blue, and cyan. The ribbon is a deterministic parametric band with hairline strands, clipped to the sphere and redrawn at the element size.

## Tokens

| Role | Light | Dark |
| --- | --- | --- |
| Canvas | `#d3d7fc → #cbe6f9 → #d4edf2` | `#03050f → #050818` |
| Surface | `rgba(255,255,255,.72)` | `rgba(20,28,68,.55)` |
| Raised surface | `#ffffff` | `rgba(14,20,48,.7)` |
| Text | `#0a0e1a` | `#eef1ff` |
| Muted text | `#5b6478` | `#8d96b8` |
| Border | `rgba(255,255,255,.7)` | `rgba(150,170,255,.14)` |
| Primary | `#5189e6 → #8cb5ed` | `#3563d6 → #4b7ff0` |
| Signal cyan | `#6edafd` | `#6edafd` |
| Grid | `rgba(110,210,225,.35)` | `rgba(120,170,255,.08)` |

## Geometry and motion

- Content width is 1180px, with 96px desktop and 64px mobile section padding.
- Controls are 10px or fully pill-shaped; cards use 18px to 28px radii.
- Ambient layers fade through opacity over 300ms. Gradients do not transition.
- The orb uses a 4.32 second deterministic loop, pauses off-screen and when the tab is hidden, and renders one static frame for reduced motion.
- Decorative motion is slow and low amplitude. Interactive transitions are 180ms ease-out.
