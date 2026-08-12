# Design QA

- source visual truth: `/var/folders/91/w42ntpnd4m14pls3c8gnxtfh0000gn/T/codex-clipboard-059a3231-dc15-404b-affc-511698383843.png`
- implementation URL: `http://127.0.0.1:4174/#notice`
- implementation screenshot: `/tmp/gmzy-notice-desktop-updated.png`
- viewport: 1280 × 720 CSS px; screenshot captured at the same desktop state
- mobile verification viewport: 390 × 844 CSS px
- state: homepage, notification section visible, normal light theme
- density normalization: none required; browser screenshot and CSS viewport use 1× density

## Comparison evidence

- The implementation removes the `教务新闻` module and retains one `教务通知` module, as explicitly requested.
- The notification list now contains eight items arranged into two equal desktop columns with date blocks, separators, title/summary hierarchy, and a right-aligned `查看更多` control consistent with the reference composition.
- Mobile verification confirms all eight notifications collapse to one column without horizontal overflow.
- No `#news` element remains; one `#notice` module remains with eight notification items.
- The background pseudo-element remains at `opacity: 0.5`, but the notification content wrapper now has `position: relative; z-index: 1`, so the background image no longer washes out the text.

## Required fidelity surfaces

- Fonts and typography: existing site typography and hierarchy are retained; notification title, summary, date, and year styles remain distinct and readable.
- Spacing and layout rhythm: desktop list is two columns with a 54px column gap and consistent row separators; mobile list is one column.
- Colors and visual tokens: existing light-blue data-screen background, blue date accents, muted summaries, and white section surface are retained.
- Image quality and asset fidelity: existing background asset is reused unchanged; no new image asset or CSS-art substitute was introduced.
- Copy and content: the news module is removed, while four additional related entries were added so the notification module contains eight items.
- Accessibility: semantic section heading, list structure, links, and existing navigation remain intact.

## Findings

No actionable P0/P1/P2 findings.

The reference contains eight entries in two columns. The current implementation also contains eight entries; the four entries that previously belonged to the news module were retained as related notification content after the news module itself was removed.

## Comparison history

- Initial implementation: removed the news column and changed the remaining notice list to a desktop two-column grid.
- Follow-up fix: added four related entries and raised the notice content above the background pseudo-element to remove the washed-out text effect.
- Post-fix evidence: `/tmp/gmzy-notice-desktop-updated.png`; desktop metrics reported two grid columns and eight items.
- Responsive evidence: mobile metrics reported one grid column, eight items, and no horizontal overflow at 390 × 844 CSS px.

## Implementation checklist

- [x] Remove the academic news module.
- [x] Display eight academic notices in two columns on desktop.
- [x] Collapse notices to one column on mobile.
- [x] Update GSAP module selector from `#news` to `#notice`.
- [x] Preserve the final notification module from fading out at the page bottom.
- [x] Run `git diff --check`.

## Follow-up Polish

- P3: If more notification entries are added later, the same grid will place them row by row automatically.

final result: passed
