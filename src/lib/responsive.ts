import fs from 'node:fs';
import path from 'node:path';

// srcset for images in public/images, using the -400/-800 variants and the
// width manifest that scripts/normalize-images.mjs writes during prebuild.
// Anything missing (dev server without prebuild, an image outside /images/, a
// non-WebP file) falls back to no srcset, so the page still shows the original.

let widths: Record<string, number> | null = null;
function manifest(): Record<string, number> {
  if (widths) return widths;
  try {
    widths = JSON.parse(fs.readFileSync(path.resolve('src/data/image-widths.json'), 'utf8'));
  } catch {
    widths = {};
  }
  return widths!;
}

export function srcsetFor(src?: string): string | undefined {
  if (!src || !src.startsWith('/images/') || !src.toLowerCase().endsWith('.webp')) return undefined;
  const full = manifest()[src];
  if (!full) return undefined;
  const base = src.slice(0, -5);
  const parts: string[] = [];
  for (const w of [400, 800]) {
    if (w < full && fs.existsSync(path.resolve('public', `${base.slice(1)}-${w}.webp`))) {
      parts.push(`${base}-${w}.webp ${w}w`);
    }
  }
  if (!parts.length) return undefined;
  parts.push(`${src} ${full}w`);
  return parts.join(', ');
}
