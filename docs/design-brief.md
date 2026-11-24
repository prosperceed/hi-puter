# Hi-Puter design brief

## Reference read

The provided visual reference uses a near-black navy canvas, a cool blue-violet atmosphere, and a single high-energy green accent. Its rhythm is a compact navigation bar, a split hero with a strong left-aligned headline, an oversized hand/AI focal point, then generous dark breathing room before the next centered statement. Thin technical lines, soft glows, and hexagonal geometry make the interface feel intelligent without becoming a dashboard.

Hi-Puter keeps that sense of depth and controlled energy, but makes the story more direct: the page moves from voice control, to the four-step loop, to real commands, then trust and installation. The main visual is an illuminated hand and command waveform, not a generic robot illustration.

## Tokens

- Canvas: `#070a12` ink, `#0d1220` panel, `#121a2c` raised panel.
- Text: `#f5f7fb` primary, `#aab5c8` secondary, `#647089` muted.
- Accent: `#b8ff3d` signal green, with `#8eea26` hover and `#e6ffad` highlight.
- Secondary light: `#72d9ff` cyan used for signal paths and focus states.
- Type: Bricolage Grotesque for display and body, Geist Mono for commands.
- Scale: 12 / 14 / 16 / 20 / 28 / 40 / 64 / 88px, fluid from mobile to desktop.
- Spacing: 8px base, section padding 96px desktop and 64px mobile, max content width 1180px.
- Radius: 10px controls, 18px cards, 28px feature panels, pill tags.
- Shadows: dark ambient `0 24px 80px rgba(0,0,0,.28)`, green signal glow `0 0 48px rgba(184,255,61,.18)`.

## Motion rules

- Use slow, almost imperceptible drift for atmospheric glows and a 2.8s signal pulse for the waveform.
- Use short 180ms ease-out transitions for controls, tabs, accordions, and links.
- Reveal hierarchy through opacity and translate, never through constant motion or parallax.
- Keep motion decorative and deterministic. `prefers-reduced-motion` removes loops and collapses transitions to near-zero.
