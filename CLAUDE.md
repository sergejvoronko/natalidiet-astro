# natalidiet-astro — Project Handover

Diet/recipe site natalidiet.eu. Astro + Cloudflare Pages (`pages_build_output_dir: ./dist` in wrangler.jsonc).

## Stack & commands
- Build: `source ~/.nvm/nvm.sh && nvm use 22 && npm run build`
- Recipes are an Astro content collection under `src/content/`
- `generate-blog-images.py` for blog imagery

## n8n recipe generator (critical workflow)
Lives in n8n stack at `/home/sergej/stacks/n8n/` (host) → mounted as `/opt/drafts/` in the n8n container.

State files in `/home/sergej/stacks/n8n/drafts/`:
- `natalidiet-draft.json` — pending draft. **If this file exists, the generator refuses to create new recipes** (throws "approve or skip it first").
- `natalidiet-published-slugs.json` — flat JSON array of published recipe slugs; generator uses it to avoid duplicates.

Publish flow: generator writes draft → human approves → recipe added to Astro content collection + image → **add slug to published-slugs.json → delete draft file** → generator unblocked.

**Image step (mandatory):** generator output is often a JPEG/PNG mislabeled as `.webp`, full-res (2400px+, 1.5–3.5MB). Before copying into `public/images/`, convert: `cwebp -q 78 -resize 1600 0 <src> -o public/images/<slug>.webp`. Target ≤250KB. (SEO audit 2026-06-12 found 86 oversized images, 92MB→25MB after batch fix.)

**FAQ step (mandatory):** every recipe gets `faqs:` frontmatter — 3 Q&As (`- q:` / `a:` pairs), grounded in the actual recipe (substitutions, storage/freezing, technique pitfalls). Renders as FAQ section + FAQPage schema via FAQBlock component. Keep titles ≤47 chars or add `metaTitle`/`metaDescription` (meta title ≤60 incl. "| Natali Diet", description ≤155).

If generator reports a pending draft that's already published on the site: verify recipe exists in `src/content/`, append slug to published-slugs.json, delete the draft (confirm with user before delete).

## Related assets
- `/home/sergej/Downloads/natalidiet-assets/` — logo, style guide, SEO strategy docs, WP export, original handoff doc
