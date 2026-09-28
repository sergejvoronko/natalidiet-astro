// Auto-normalize public/images before every build.
// The n8n recipe generator outputs `<slug>.webp`, but the bytes are often a
// PNG/JPEG mislabeled as WebP, full-res (1024px+, 1-3MB). This guard makes the
// manual cwebp step unnecessary: any .webp that is actually PNG/JPEG, too wide,
// or oversized is re-encoded to real WebP IN PLACE (same filename).
//
// Scope is deliberately narrow and safe:
//   - Only touches files with a .webp extension (the format the site references).
//   - Never renames, never deletes, never converts .png/.jpg (logo.png etc. stay).
//   - Idempotent: a real, in-bounds .webp is left byte-identical (no re-compress,
//     no generation loss) so good images don't decay across builds.
//
// Runs as `prebuild`, so it executes locally AND on the Cloudflare Pages build.

import { readdir, stat, rename, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import sharp from 'sharp';

const DIR = new URL('../public/images/', import.meta.url).pathname;
const MANIFEST = new URL('../src/data/image-widths.json', import.meta.url).pathname;
const MAX_WIDTH = 1600;        // recipes never display wider than this
const MAX_BYTES = 400 * 1024;  // recompress anything heavier
const QUALITY = 80;
// Smaller copies for srcset. Cards and the recipe hero display at ~350px, so
// without these every card downloaded the full 1400-1600px original.
const VARIANT_WIDTHS = [400, 800];
const isVariant = f => /-(400|800)\.webp$/i.test(f);

let fixed = 0;

for (const file of await readdir(DIR)) {
  if (!file.toLowerCase().endsWith('.webp') || isVariant(file)) continue;

  const path = join(DIR, file);
  const { size } = await stat(path);

  let meta;
  try {
    meta = await sharp(path).metadata();
  } catch {
    console.warn(`  ! unreadable, skipped: ${file}`);
    continue;
  }

  const mislabeled = meta.format !== 'webp'; // PNG/JPEG bytes in a .webp file
  const tooWide = (meta.width ?? 0) > MAX_WIDTH;
  const tooBig = size > MAX_BYTES;
  if (!mislabeled && !tooWide && !tooBig) continue;

  const tmpPath = `${path}.tmp`;
  const pipeline = sharp(path);
  if (tooWide) pipeline.resize({ width: MAX_WIDTH, withoutEnlargement: true });
  await pipeline.webp({ quality: QUALITY }).toFile(tmpPath);
  await rename(tmpPath, path);

  const after = (await stat(path)).size;
  const why = mislabeled ? `${meta.format}-as-webp` : tooWide ? `${meta.width}px` : 'oversized';
  console.log(`  ✓ ${file}  (${why})  ${(size / 1024 | 0)}KB -> ${(after / 1024 | 0)}KB`);
  fixed++;
}

console.log(fixed ? `normalize-images: fixed ${fixed} file(s)` : 'normalize-images: all clean');

// Responsive variants. Generated here rather than committed, so every image the
// generator adds gets them on the next build. A variant is (re)made when it is
// missing or older than its original, and never wider than the original.
// The manifest records each original's real width for the srcset descriptor.
const widths = {};
let made = 0;
for (const file of await readdir(DIR)) {
  if (!file.toLowerCase().endsWith('.webp') || isVariant(file)) continue;
  const path = join(DIR, file);
  let meta;
  try { meta = await sharp(path).metadata(); } catch { continue; }
  if (!meta.width) continue;
  widths[`/images/${file}`] = meta.width;
  const srcTime = (await stat(path)).mtimeMs;
  for (const w of VARIANT_WIDTHS) {
    if (w >= meta.width) continue;
    const out = join(DIR, file.replace(/\.webp$/i, `-${w}.webp`));
    const fresh = await stat(out).then(s => s.mtimeMs >= srcTime, () => false);
    if (fresh) continue;
    await sharp(path).resize({ width: w }).webp({ quality: QUALITY }).toFile(out);
    made++;
  }
}
await mkdir(new URL('../src/data/', import.meta.url).pathname, { recursive: true });
await writeFile(MANIFEST, JSON.stringify(widths, null, 1) + '\n');
console.log(`normalize-images: ${made} variant(s) generated, ${Object.keys(widths).length} images in manifest`);
