# ASUNA Frontend Design Direction

ASUNA is a **single-page image retrieval workstation** designed desktop-first for high information density. The interface prioritizes efficient operation and comparison of many results at once; it is not a promotional landing page. Its visual language follows Chakra Bloom, defined in [PALETTE.md](./PALETTE.md).

## 1. Main Layout

- **Left sidebar:** search mode, query input, model selection, filters, and the **Run Search** button. Group controls in the order users need them; keep the primary button prominent and associated with the search form.
- **Central results area:** occupies most of the screen and displays candidate images in a grid. Keep the sidebar at a stable width on desktop; the results area uses the remaining space and scrolls independently when needed.
- **Bottom shortcut bar:** lists frequently used actions such as switching modes and running a search. Show only shortcuts that are actually supported.

## 2. Visual Language

### Color and Hierarchy

- Use **Warm Cream** (`#FAF7F2`) for the page background, **White** (`#FFFFFF`) for the sidebar and control surfaces, and **Deep Forest** (`#203B36`) for primary text. Use **Border** (`#E8E4DC`) to separate regions instead of adding layers of shadows.
- **Jade** (`#287D6D`) is the primary action and brand color. Use the remaining Chakra colors as purposeful accents rather than covering the results area in color.
- Distinguish search modes with both color and a label or icon: **Semantic** uses Jade, **Image** uses Coral, and **Skeleton/Pose** uses Matcha. Color is never the only indicator. If Sketch or Video modes are added later, use Lavender or Sky respectively, as specified in `PALETTE.md`.
- Use the corresponding pastel surfaces for selected states or subtle annotations; preserve the natural colors of candidate images. Reserve Sunlight for secondary highlights that do not compete with the search button.
- Use gradients sparingly for brand details, not behind the image grid or frequently read text.

### Results Grid and Cards

- Use compact cards with thin borders and **1–2 px** gaps to maximize image space and the number of visible candidates. Use a regular grid with consistent thumbnail dimensions to make comparison easier.
- Keep card layouts stable across images with different aspect ratios. Crop or fit images consistently while avoiding the loss of important pose information. Do not place decorative labels over images; put essential information in a compact area below or reveal it contextually.
- Clearly distinguish hover, focus, and selected states with borders or outlines without changing card dimensions or shifting the grid. Avoid large shadows on individual candidates.

### Typography, Icons, and Details

- Prefer **Plus Jakarta Sans** or **Manrope** for labels, forms, and metadata; choose a font with Vietnamese character support. Use the serif heading options in `PALETTE.md` sparingly for branding where appropriate, not for dense controls.
- Establish hierarchy through font size and weight: region headings, control labels, then metadata. Keep labels concise and scannable; do not sacrifice readability to increase density.
- Use one consistent icon family as specified in `TECH_STACK.md`; pair important icons with labels or accessible names. Apply subtle, consistent corner radii to buttons, inputs, and dialogs. Result cards may be square or only slightly rounded to maintain a compact grid.
- Keep transitions quick and restrained; avoid continuous decorative animation. Respect the operating system's reduced-motion preference.

### States and Accessibility

- **Before searching:** show brief guidance in the results area. **Loading:** preserve the grid layout and use placeholders matching image dimensions. **No results:** provide a clear message and suggest adjusting the query or filters. **Error:** show a specific message and a way to retry.
- Check the contrast of text, buttons, and focus indicators against each surface; do not assume every pastel color is suitable for text. Keyboard focus must be visible and must not rely on color alone.
- Keep control targets easy to use despite the dense image grid. Support keyboard navigation and provide accessible labels for icon-only actions.

## 3. Interaction Flow

Users select a mode such as **Semantic**, **Image**, or **Skeleton** in the sidebar, provide the appropriate query, choose a model and filters, then run the search and inspect candidates in the central area. Place secondary actions in drawers or dialogs so users remain on the results screen; return focus to the opening control when a drawer or dialog closes.

On smaller screens, the sidebar may become a drawer to make room for results. Search controls and status information must remain accessible without relying on desktop keyboard shortcuts.
