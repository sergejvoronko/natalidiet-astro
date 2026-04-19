// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://natalidiet.eu',
  output: 'static',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/privacy') === false || true,
    }),
  ],
});
