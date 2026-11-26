# Chakra Bloom

ASUNA's frontend uses **Chakra Bloom**: a nature- and yoga-inspired palette combining pastel surfaces with modern, richer accents. The direction is **Colorful Zen × Organic Minimalism × Modern AI**: mindful, organic, creative, intelligent, and modern.

ASUNA is a single-page retrieval application. The palette and retrieval colors below guide that interface; they do not imply additional pages, navigation, a landing page, or retrieval features that have not been implemented.

## Main palette

| Color | Hex | Intended use |
| --- | --- | --- |
| Jade Green | `#287D6D` | Primary actions and brand |
| Sunlight | `#F2B66D` | Highlights and secondary calls to action |
| Coral Pink | `#E88D86` | Image retrieval accent |
| Lavender | `#A69ACA` | Sketch retrieval accent |
| Sky Blue | `#84B9CB` | Video retrieval accent, if supported |
| Matcha Green | `#B8CC8B` | Pose retrieval accent |
| Warm Cream | `#FAF7F2` | Page background |
| White | `#FFFFFF` | Surfaces |
| Deep Forest | `#203B36` | Primary text |
| Border | `#E8E4DC` | Dividers and borders |

Use retrieval accents to distinguish available modes without relying on color alone; include a text label or icon. Use Deep Forest for readable text on light surfaces and check contrast before using accent colors for text or controls.

## Pastel surfaces

| Color | Hex |
| --- | --- |
| Jade light | `#D5E9E2` |
| Sunlight light | `#F7E4C9` |
| Coral light | `#F5D7D2` |
| Lavender light | `#E4DDF2` |
| Sky light | `#D5EAF0` |
| Matcha light | `#E2EBCD` |
| Muted | `#74847C` |

## Gradient direction

| Name | Colors |
| --- | --- |
| Morning Flow | `#F2B66D` → `#E88D86` |
| Mindful Balance | `#B8CC8B` → `#287D6D` |
| Inner Peace | `#84B9CB` → `#A69ACA` |
| Chakra Harmony | `#B8CC8B` → `#A69ACA` |

Use gradients sparingly so the retrieval workspace remains clear and functional.

## CSS variables

```css
:root {
  /* Brand colors */
  --primary: #287D6D;
  --secondary: #A69ACA;
  --accent: #F2B66D;

  /* Chakra colors */
  --jade: #287D6D;
  --sunlight: #F2B66D;
  --coral: #E88D86;
  --lavender: #A69ACA;
  --sky: #84B9CB;
  --matcha: #B8CC8B;

  /* Pastel surfaces */
  --jade-light: #D5E9E2;
  --sunlight-light: #F7E4C9;
  --coral-light: #F5D7D2;
  --lavender-light: #E4DDF2;
  --sky-light: #D5EAF0;
  --matcha-light: #E2EBCD;

  /* Neutral colors */
  --background: #FAF7F2;
  --surface: #FFFFFF;
  --foreground: #203B36;
  --muted: #74847C;
  --border: #E8E4DC;

  /* Gradients */
  --gradient-brand: linear-gradient(
    135deg, #B8CC8B, #F2B66D, #E88D86, #A69ACA
  );
  --gradient-hero: linear-gradient(
    120deg, #E0EBD2, #F7E8CE, #EBDCEF
  );
}
```

## Typography

- **Headings:** Fraunces or Cormorant Garamond.
- **Body and interface:** Plus Jakarta Sans or Manrope.

Choose fonts that support the interface's required Vietnamese characters and prioritize readability in the retrieval workspace.
