#!/usr/bin/env python3
"""Generate hero images for all blog posts. Run from project root."""
import subprocess, os, time, json
from pathlib import Path

SCRIPT = "/home/sergej/.claude/plugins/cache/banana-claude-marketplace/banana-claude/1.4.1/skills/banana/scripts/generate.py"
OUT_DIR = Path("/home/sergej/Downloads/natalidiet-astro/public/images/blog")
GEN_DIR = Path("/home/sergej/Documents/nanobanana_generated")
BLOG_DIR = Path("/home/sergej/Downloads/natalidiet-astro/src/content/blog")

# Shared style anchor — matches existing 4 food photos
STYLE = (
    "Shot on Canon EOS R5 with 50mm f/1.8 lens. "
    "Soft natural window light streaming from the left, warm morning kitchen atmosphere. "
    "Rustic Eastern European styling: aged oak board, folded grey linen napkin, "
    "hand-thrown ceramic vessel. Bon Appétit editorial food photography. "
    "Warm cream and terracotta tones, shallow depth of field."
)

POSTS = [
    ("healthy-borscht-recipe",
     f"Deep ruby-red Ukrainian borscht in a white ceramic bowl, steam wisps rising from the surface, "
     f"crowned with a swirl of Greek yogurt and a frond of fresh dill. A slice of dark rye bread rests beside "
     f"the bowl on an aged oak board. Wide shot from 45-degree angle, garnished with micro-herbs. {STYLE}"),

    ("healthy-green-borshch-sorrel-soup",
     f"Vibrant emerald-green sorrel soup (zeleny borshch) in a wide white ceramic bowl — "
     f"a halved soft-boiled egg floating in the center, scattered fresh sorrel leaves and dill sprigs. "
     f"Intense jewel-green broth catching morning light. Close crop from overhead slightly tilted. {STYLE}"),

    ("healthy-rassolnik-recipe",
     f"Pale golden chicken rassolnik soup in a cream ceramic bowl — barley grains visible, "
     f"thin pickled cucumber slivers, fresh parsley cluster at the edge, "
     f"a wooden ladle resting beside the bowl on linen. Wide 45-degree angle shot. {STYLE}"),

    ("healthy-hungarian-mushroom-soup",
     f"Dark, deeply savory Hungarian mushroom soup in a dark terracotta bowl — "
     f"thick sliced cremini and porcini mushrooms, a swirl of sour cream, fresh thyme sprig on top. "
     f"Moody amber light, dramatic shadows behind the bowl. 45-degree angle. {STYLE}"),

    ("healthy-slovak-kapustnica-recipe",
     f"Slovak kapustnica sauerkraut soup in an earthenware crock — pale tangy broth with "
     f"shredded fermented cabbage, sliced dried mushrooms, bay leaf visible. "
     f"Winter comfort food, steam wisps, dark wooden background. {STYLE}"),

    ("healthy-polish-zurek-recipe",
     f"Polish żurek white borscht served in a rustic bread bowl — creamy sour rye broth, "
     f"halved soft-boiled egg, sliced kielbasa sausage, fresh marjoram sprig. "
     f"The bread bowl sits on a linen cloth. 45-degree hero angle. {STYLE}"),

    ("healthy-eastern-european-soups",
     f"Three ceramic bowls of Eastern European soups arranged in a triangle — ruby-red borscht, "
     f"vibrant green sorrel soup, and pale golden rassolnik — each garnished with herbs, "
     f"on a worn linen tablecloth. Wide overhead shot. {STYLE}"),

    ("10-healthy-ukrainian-soups-weight-loss",
     f"Six small Ukrainian soup bowls arranged in two rows from overhead on a large aged oak table — "
     f"borscht, green borshch, rassolnik, kapustnyak, golden chicken soup, mushroom soup — "
     f"each with its own herb garnish. Grand editorial flat-lay. {STYLE}"),

    ("healthy-chicken-paprikash-recipe",
     f"Hungarian chicken paprikash — a tender chicken thigh glazed in deep-red paprika cream sauce, "
     f"served over golden buckwheat groats in a wide shallow white bowl. "
     f"Sauce glossy and rich, fresh dill sprinkled over. 45-degree close shot. {STYLE}"),

    ("healthy-hungarian-goulash-recipe",
     f"Hungarian beef goulash in a small cast iron pot — dark, deeply flavored stew with "
     f"tender beef cubes, softened bell pepper pieces, paprika-red broth. "
     f"Wooden ladle resting on the side, steam rising. Dramatic 45-degree angle. {STYLE}"),

    ("healthy-holubtsi-cabbage-rolls-recipe",
     f"Ukrainian holubtsi cabbage rolls — four plump rolls of tender savoy cabbage stuffed with "
     f"rice and ground turkey in tomato sauce, in a white oval baking dish. "
     f"Cross-section of one roll showing the filling. Overhead 45-degree. {STYLE}"),

    ("healthy-bigos-polish-hunters-stew",
     f"Polish bigos hunters stew in a deep clay pot — dark, smoky-looking stew of sauerkraut, "
     f"dried mushrooms, and lean pork. Rich mahogany color, bay leaf visible. "
     f"Rustic, masculine, deeply satisfying aesthetic. {STYLE}"),

    ("healthy-svieckova-czech-beef-cream-sauce",
     f"Czech svíčková — sliced roasted beef sirloin in pale golden cream sauce, "
     f"a lemon slice, small mound of cranberry relish, and one bread dumpling (knedlík) "
     f"on a white plate. Clean Central European plating. {STYLE}"),

    ("healthy-slovak-pork-tenderloin-recipe",
     f"Sliced Slovak pork tenderloin on a worn wooden board — perfectly cooked, golden-brown crust, "
     f"juicy pink interior revealed. Rosemary sprigs, roasted baby carrots and parsnips alongside. "
     f"Wide hero angle from slightly above. {STYLE}"),

    ("healthy-hungarian-stuffed-peppers-recipe",
     f"Hungarian töltött paprika — two large red and yellow bell peppers stuffed with rice and pork, "
     f"simmering in tomato broth in a white casserole dish. Rich tomato sauce pooling around the peppers. "
     f"Overhead 45-degree angle, abundant and colorful. {STYLE}"),

    ("healthy-eastern-european-main-dishes",
     f"A generous overhead spread of five Eastern European dishes on a large rustic table — "
     f"chicken paprikash, beef goulash in cast iron, cabbage rolls, sliced pork tenderloin, buckwheat bowl. "
     f"Grand editorial flat-lay, linen and ceramic vessels. {STYLE}"),

    ("healthy-syrniki-recipe",
     f"Golden Ukrainian syrniki cottage cheese pancakes — stack of three on a white plate, "
     f"dusted with powdered sugar, fresh strawberries and blueberries tumbling beside, "
     f"a small bowl of sour cream. Hero 45-degree close shot. {STYLE}"),

    ("healthy-deruny-ukrainian-potato-pancakes",
     f"Ukrainian deruny potato pancakes — four crispy golden-brown discs on a dark ceramic plate, "
     f"topped with a dollop of sour cream and a scatter of fresh chives. "
     f"Texture shot showing the crispy lacey edges. Close 45-degree angle. {STYLE}"),

    ("buckwheat-mushrooms-eastern-european-recipe",
     f"Buckwheat with wild mushrooms in a ceramic bowl — nutty toasted groats with sautéed porcini "
     f"and cremini mushrooms, caramelized onion, fresh dill. Earthy deep tones, rich texture. "
     f"45-degree hero angle. {STYLE}"),

    ("healthy-olivier-salad-recipe",
     f"Classic Olivier Russian salad in a white serving bowl — creamy potato salad with diced "
     f"egg, pickled cucumber, carrot, green peas, light mayonnaise. Fresh parsley garnish. "
     f"Clean elegant overhead slightly tilted. {STYLE}"),

    ("healthy-baked-varenyky-pierogi-recipe",
     f"Baked Ukrainian varenyky — six golden-crusted half-moon dumplings on a dark slate plate, "
     f"a small ramekin of sour cream for dipping, caramelized onion strands. "
     f"Close hero shot 45-degree angle. {STYLE}"),

    ("healthy-traditional-eastern-european-food",
     f"Overhead flat-lay of traditional Eastern European pantry ingredients — "
     f"raw beetroot, jar of sauerkraut, dark rye bread loaf, buckwheat in a small bowl, "
     f"kefir bottle, fresh dill bunch, sunflower seeds. Story of the pantry, rustic linen. {STYLE}"),

    ("healthy-substitutions-eastern-european-cooking",
     f"A clean editorial flat-lay of healthy ingredient swaps — Greek yogurt in a white bowl next to "
     f"a spoonful of sour cream, olive oil bottle beside a small lard piece, buckwheat flour next to "
     f"white flour. Minimal, informative, bright natural light on white marble. {STYLE}"),

    ("healthy-ukrainian-recipes",
     f"A vibrant spread of iconic Ukrainian dishes on a table draped in blue and yellow linen — "
     f"borscht bowl, plate of varenyky, stack of syrniki, deruny potato pancakes, kefir glass. "
     f"Overhead wide editorial flat-lay, celebratory abundance. {STYLE}"),

    ("healthy-hungarian-recipes",
     f"Hungarian food spread on a warm-toned table — chicken paprikash in cast iron, "
     f"paprika goulash in ceramic bowl, stuffed peppers in dish, paprika powder in wooden spoon. "
     f"Rich reds and warm amber tones dominate. Wide overhead editorial. {STYLE}"),

    ("healthy-polish-recipes",
     f"Polish cuisine spread — plate of pierogi with sour cream, bowl of bigos stew, "
     f"żurek bread bowl, fresh horseradish on the side. White and red linen accent cloth. "
     f"Wide overhead editorial flat-lay. {STYLE}"),

    ("healthy-romanian-recipes",
     f"Romanian food spread — sarmale cabbage rolls in a clay pot, golden mămăligă (polenta) wedge, "
     f"grilled mici sausages, small jar of pickled vegetables. Transylvanian rustic aesthetic. {STYLE}"),

    ("healthy-slovak-czech-recipes",
     f"Slovak and Czech food spread — a bowl of bryndzové halušky (sheep cheese potato dumplings), "
     f"plate of svíčková sliced beef with cream sauce, knedlíky bread dumplings, glass of kefir. "
     f"Cozy Central European kitchen aesthetic. {STYLE}"),

    ("healthy-eastern-european-recipes-by-country",
     f"Grand overhead editorial flat-lay — dishes from six Eastern European countries arranged "
     f"on a large rustic table: Ukrainian borscht, Hungarian paprikash, Polish pierogi, "
     f"Romanian sarmale, Czech svíčková, Slovak halušky. Each dish with a small flag-colored napkin. {STYLE}"),

    ("central-european-diet-to-lose-weight",
     f"A perfectly balanced nutritionist's plate from overhead — golden buckwheat on one side, "
     f"grilled chicken breast, roasted rainbow vegetables, a small glass of kefir beside the plate. "
     f"Clean white background, tape measure loosely beside the plate. Bright editorial. {STYLE}"),

    ("eastern-european-diet-vs-mediterranean-diet",
     f"Two elegantly styled plates side by side — left plate: Ukrainian borscht bowl with buckwheat, "
     f"right plate: Greek salad with grilled fish and olive oil bottle. Both on the same oak board. "
     f"Comparison editorial, equal lighting on both sides. {STYLE}"),

    ("how-to-lose-weight-eating-ukrainian-food",
     f"Hands cradling a steaming bowl of Ukrainian borscht — close intimate shot from above, "
     f"warm ruby-red soup reflecting kitchen window light. Cozy, personal, inviting. "
     f"Shallow depth of field, bokeh kitchen background. {STYLE}"),

    ("eastern-european-meal-prep-for-the-week",
     f"Overhead flat-lay of four glass meal prep containers neatly arranged on a kitchen counter — "
     f"borscht in one, chicken paprikash in another, buckwheat in third, salad in fourth. "
     f"Organized, clean, practical. Labels in cursive pen. {STYLE}"),

    ("7-day-eastern-european-weight-loss-meal-plan",
     f"Seven small ceramic bowls and plates arranged in a row on a long linen-covered table — "
     f"each representing a day of Eastern European meals: borscht, syrniki, paprikash, "
     f"varenyky, buckwheat bowl, goulash, sorrel soup. Abundance and variety. Wide overhead. {STYLE}"),
]

APIKEY = subprocess.check_output(
    "grep 'GOOGLE_AI_API_KEY' ~/.bashrc | head -1 | cut -d= -f2", shell=True
).decode().strip().strip('"').strip("'")

total = len(POSTS)
success = 0
failed = []

for i, (slug, prompt) in enumerate(POSTS):
    out_webp = OUT_DIR / f"{slug}.webp"
    if out_webp.exists():
        print(f"[{i+1}/{total}] SKIP (exists): {slug}")
        success += 1
        continue

    print(f"\n[{i+1}/{total}] Generating: {slug}")

    result = subprocess.run(
        ["python3", SCRIPT, "--api-key", APIKEY, "--aspect-ratio", "16:9",
         "--resolution", "2K", "--prompt", prompt],
        capture_output=True, text=True, timeout=120
    )

    try:
        data = json.loads(result.stdout)
        png_path = Path(data["path"])
        if png_path.exists():
            # Convert to webp
            subprocess.run(["cwebp", "-q", "82", str(png_path), "-o", str(out_webp)],
                           capture_output=True)
            print(f"  ✓ Saved: {out_webp.name} ({out_webp.stat().st_size // 1024}KB)")
            success += 1
        else:
            print(f"  ✗ PNG not found at {png_path}")
            failed.append(slug)
    except Exception as e:
        print(f"  ✗ Error: {e}\n  stdout: {result.stdout[:200]}\n  stderr: {result.stderr[:200]}")
        failed.append(slug)

    # Respect rate limit — ~4s between requests
    if i < total - 1:
        time.sleep(4)

print(f"\n{'='*50}")
print(f"Done: {success}/{total} generated")
if failed:
    print(f"Failed: {failed}")
