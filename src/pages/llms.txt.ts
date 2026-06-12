import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

const SITE = 'https://natalidiet.eu';

export const GET: APIRoute = async () => {
  const recipes = (await getCollection('recipes')).sort(
    (a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf()
  );
  const posts = (await getCollection('blog'))
    .filter(p => !p.data.noIndex)
    .sort((a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf());
  const plans = await getCollection('meal-plans');

  const lines = [
    '# Natali Diet',
    '',
    '> Eastern and Central European recipes adapted for healthy eating and weight loss. Every recipe is calorie-counted with full macros (protein, carbs, fat, fibre). Written by Natali, recipe developer and healthy eating author.',
    '',
    'Traditional dishes from Ukraine, Poland, Hungary, Slovakia, Czechia, Romania, Bulgaria and Belarus, made lighter: Greek yogurt instead of sour cream, baking instead of frying, lean proteins, fermented foods (kefir, sauerkraut, żurek). All nutrition values are per-serving estimates.',
    '',
    '## Recipes',
    '',
    ...recipes.map(r =>
      `- [${r.data.title}](${SITE}/recipes/${r.id}/): ${r.data.calories} kcal, ${r.data.protein}g protein, ${r.data.course}. ${r.data.description}`
    ),
    '',
    '## Guides & Articles',
    '',
    ...posts.map(p =>
      `- [${p.data.title}](${SITE}/blog/${p.id}/): ${p.data.description}`
    ),
    '',
    '## Meal Plans',
    '',
    ...plans.map(m =>
      `- [${m.data.title}](${SITE}/meal-plans/${m.id}/): ${m.data.description}`
    ),
    '',
    '## Ingredient Hubs',
    '',
    `- [Kefir recipes](${SITE}/kefir-recipes/): probiotic fermented dairy — soups, dressings, breakfasts`,
    `- [Buckwheat recipes](${SITE}/buckwheat-recipes/): gluten-free Eastern European staple grain`,
    `- [Cottage cheese recipes](${SITE}/cottage-cheese-recipes/): high-protein tvaroh dishes`,
    '',
    '## About',
    '',
    `- [About Natali](${SITE}/about/): author background and approach`,
    `- [Contact](${SITE}/contact/)`,
    '',
    'Nutrition values are estimates for general guidance, not medical advice.',
    '',
  ];

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
