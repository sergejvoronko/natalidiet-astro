// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import fs from 'node:fs';
import path from 'node:path';

// lastmod for the sitemap, from each entry's publishDate (updatedDate if set).
// Git dates are deliberately not used: Cloudflare Pages builds from a shallow
// clone, so every file would report the build date. Listing pages (sections,
// courses, ingredient hubs, homepage) take the date of their newest entry.
const lastmod = new Map();
const newest = (key, d) => { if (!lastmod.has(key) || lastmod.get(key) < d) lastmod.set(key, d); };
for (const coll of ['recipes', 'blog', 'meal-plans']) {
  const dir = `./src/content/${coll}`;
  for (const f of fs.readdirSync(dir)) {
    if (!/\.mdx?$/.test(f)) continue;
    const fm = fs.readFileSync(path.join(dir, f), 'utf8').split('---')[1] ?? '';
    if (/^draft:\s*true/m.test(fm)) continue;
    const ds = (fm.match(/^updatedDate:\s*"?([\d-]+)/m) ?? fm.match(/^publishDate:\s*"?([\d-]+)/m) ?? [])[1];
    if (!ds) continue;
    const d = new Date(ds);
    lastmod.set(`/${coll}/${f.replace(/\.mdx?$/, '')}/`, d);
    newest(`/${coll}/`, d);
    newest('/', d);
    if (coll === 'recipes') {
      const course = (fm.match(/^course:\s*"?(\w+)/m) ?? [])[1];
      if (course) newest(`/recipes/course/${course}/`, d);
      const tags = (fm.match(/^tags:\s*\[(.*)\]/m) ?? [])[1] ?? '';
      for (const hub of ['kefir', 'buckwheat', 'cottage-cheese'])
        if (new RegExp(`"${hub}"`).test(tags)) newest(`/${hub}-recipes/`, d);
    }
  }
}

export default defineConfig({
  site: 'https://natalidiet.eu',
  output: 'static',
  trailingSlash: 'always',
  build: {
    inlineStylesheets: 'always',
  },
  integrations: [
    sitemap({
      filter: (page) =>
        !page.includes('/privacy-policy') &&
        !page.includes('/disclaimer') &&
        !page.includes('/thank-you'),
      serialize(item) {
        const d = lastmod.get(new URL(item.url).pathname);
        if (d) item.lastmod = d.toISOString();
        return item;
      },
    }),
  ],
});
