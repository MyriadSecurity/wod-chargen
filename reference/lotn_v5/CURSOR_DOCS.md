# Using the LoTN SRD in Cursor

## @Docs (site indexing)

Cursor can crawl and index public documentation so you reference it with `@` in chat.

### Add the SRD

1. **Cursor Settings** → **Features** → **Docs**
2. **Add new doc**
3. Paste: `https://www.oneworldofdarkness.com/laws-of-the-night/`
4. Name it e.g. **`LoTN V5 SRD`**
5. Confirm and wait for indexing (may take a few minutes)

### Use in prompts

```
@LoTN V5 SRD What are the XP costs to raise an in-clan discipline from 2 to 3?
```

```
Using @LoTN V5 SRD and reference/lotn_v5/SRD_INDEX.md, add missing predator types to predator_types.json
```

Official Cursor docs: [Context — @Docs](https://docs.cursor.com/context/@-symbols/@-docs)

### Tips

- **Root URL:** Use the `/laws-of-the-night/` path (not the OWOD homepage) so the crawl stays on the SRD.
- **Deep links:** `reference/lotn_v5/SRD_INDEX.md` lists section URLs when `@Docs` retrieval is vague.
- **Rules vs @Docs:** Project rules (`.cursor/rules/`) cannot invoke `@Docs` automatically — paste `@LoTN V5 SRD` in chat or open `SRD_INDEX.md` / `RULES_INDEX.md` for repo-local context.
- **Private PDF:** The pocket PDF stays local (gitignored). Use SRD + index for shareable, team-visible reference.

## Repo-local reference (always available)

These files work without Cursor Docs indexing:

| File | Purpose |
|------|---------|
| `reference/lotn_v5/SRD_INDEX.md` | URL map to OWOD SRD sections |
| `reference/lotn_v5/RULES_INDEX.md` | PDF page ↔ `wod_chargen/.../data/*.json` mapping |
| `.cursor/rules/lotn-v5-srd.mdc` | Agent rule when editing LoTN data |

In chat you can also `@reference/lotn_v5/SRD_INDEX.md` to pin the link map.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Doc stuck indexing | Remove and re-add the URL; try again later |
| Wrong content retrieved | Quote the exact SRD URL from `SRD_INDEX.md` in your prompt |
| 404 on guessed slug | Check section index pages (e.g. `/clans`, `/backgrounds`) for correct slugs |
| SPA / empty fetch | Use Cursor @Docs or browser — some paths only render client-side |
