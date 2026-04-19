import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const recipes = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/recipes' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    image: z.string().optional(),
    course: z.enum(['breakfast', 'lunch', 'dinner', 'snack']),
    cuisine: z.string().default('Eastern European'),
    prepTime: z.number(),
    cookTime: z.number(),
    totalTime: z.number(),
    servings: z.number().default(1),
    calories: z.number(),
    protein: z.number(),
    carbs: z.number(),
    fat: z.number(),
    fibre: z.number().optional(),
    tags: z.array(z.string()).default([]),
    category: z.string(),
    tip: z.string().optional(),
    publishDate: z.coerce.date(),
    ingredients: z.array(z.object({
      amount: z.string(),
      name: z.string(),
    })),
    steps: z.array(z.string()),
    featured: z.boolean().default(false),
  }),
});

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    metaTitle: z.string().optional(),
    metaDescription: z.string().optional(),
    category: z.string(),
    tags: z.array(z.string()).default([]),
    pillar: z.number().optional(),
    publishDate: z.coerce.date(),
    image: z.string().optional(),
    featured: z.boolean().default(false),
  }),
});

const mealPlans = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/meal-plans' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    days: z.number(),
    totalCalories: z.number().optional(),
    publishDate: z.coerce.date(),
    featured: z.boolean().default(false),
  }),
});

export const collections = { recipes, blog, 'meal-plans': mealPlans };
