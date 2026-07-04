// Deterministic humanizer safety net, run before every build.
// The n8n generation prompt asks the LLM to avoid AI-slop, but an LLM never
// obeys 100%. This script enforces the MECHANICAL rules that can be applied
// safely without judgement, so a slip never reaches the live site:
//   - straighten curly quotes / apostrophes
//   - thin prose em dashes to commas
//   - drop filler intensifiers (genuinely/deeply/truly/really/simply)
//   - normalise en-US spellings to en-GB (flavor -> flavour, etc.)
//
// Safety: frontmatter is handled key-by-key. title/metaTitle keep their em
// dashes (legit name separators) and only get spelling fixes; double-quotes are
// never straightened inside frontmatter (would break YAML). Idempotent — an
// already-clean file is left byte-identical, so this never churns good content.
//
// It does NOT touch subjective patterns (superlatives, rule-of-three, hype,
// empty sections) — those are the generation prompt's job. Runs as `prebuild`.

import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const ROOT = new URL('../src/content/', import.meta.url).pathname;
const DIRS = ['recipes', 'blog', 'meal-plans'];

// en-US -> en-GB, whole word, case-preserving. Deliberately conservative:
// skips ambiguous ones (meter/liter/practice/yogurt) to avoid false positives.
const SPELLING = [
  ['flavor', 'flavour'], ['flavors', 'flavours'], ['flavored', 'flavoured'],
  ['flavorful', 'flavourful'], ['flavoring', 'flavouring'],
  ['savor', 'savour'], ['savory', 'savoury'], ['savored', 'savoured'],
  ['color', 'colour'], ['colors', 'colours'], ['colored', 'coloured'], ['colorful', 'colourful'],
  ['fiber', 'fibre'], ['fibers', 'fibres'],
  ['favorite', 'favourite'], ['favorites', 'favourites'],
  ['energize', 'energise'], ['energized', 'energised'], ['energizing', 'energising'],
  ['caramelize', 'caramelise'], ['caramelized', 'caramelised'], ['caramelizing', 'caramelising'],
  ['realize', 'realise'], ['realized', 'realised'], ['realizing', 'realising'],
  ['organize', 'organise'], ['organized', 'organised'], ['organizing', 'organising'],
  ['neighbor', 'neighbour'], ['neighbors', 'neighbours'],
];
const SPELL_RES = SPELLING.map(([us, gb]) => [new RegExp(`\\b${us}\\b`, 'gi'), gb]);

function applyCase(sample, repl) {
  if (sample[0] === sample[0].toUpperCase()) return repl[0].toUpperCase() + repl.slice(1);
  return repl;
}
function fixSpelling(s) {
  for (const [re, gb] of SPELL_RES) s = s.replace(re, (m) => applyCase(m, gb));
  return s;
}
function thinEmDash(s) {
  return s.replace(/ — /g, ', ').replace(/(\w)—(\w)/g, '$1, $2');
}
function dropIntensifiers(s) {
  return s.replace(/\b(genuinely|deeply|truly|really|simply) /gi, '').replace(/ {2,}/g, ' ');
}

let filesChanged = 0;

for (const dir of DIRS) {
  const full = join(ROOT, dir);
  let entries;
  try { entries = await readdir(full); } catch { continue; }
  for (const file of entries) {
    if (!file.endsWith('.md')) continue;
    const path = join(full, file);
    const orig = await readFile(path, 'utf8');

    // Split frontmatter from body.
    let fm = '', body = orig;
    if (orig.startsWith('---\n')) {
      const end = orig.indexOf('\n---', 4);
      if (end !== -1) {
        const close = orig.indexOf('\n', end + 1);
        fm = orig.slice(0, close + 1);
        body = orig.slice(close + 1);
      }
    }

    // Frontmatter: straighten apostrophes only (never double-quotes: YAML-safe).
    fm = fm.replace(/[‘’]/g, "'");
    fm = fm.split('\n').map((line) => {
      const m = line.match(/^(\s*)(title|metaTitle|description|metaDescription|tip|excerpt|q|a):(\s.*)$/);
      if (!m) return line;
      const key = m[2];
      let v = m[3];
      v = fixSpelling(v);
      if (key !== 'title' && key !== 'metaTitle') {            // keep title dashes/intensifiers
        v = dropIntensifiers(thinEmDash(v));
      }
      return `${m[1]}${key}:${v}`;
    }).join('\n');

    // Body: full mechanical pass.
    body = body
      .replace(/[‘’]/g, "'").replace(/[“”]/g, '"')
      .replace(/ — /g, ', ').replace(/(\w)—(\w)/g, '$1, $2');
    body = dropIntensifiers(body);
    body = fixSpelling(body);

    const out = fm + body;
    if (out !== orig) { await writeFile(path, out); filesChanged++; }
  }
}

console.log(filesChanged ? `normalize-content: cleaned ${filesChanged} file(s)` : 'normalize-content: all clean');
