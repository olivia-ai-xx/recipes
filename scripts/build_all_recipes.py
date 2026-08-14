#!/usr/bin/env python3
"""Builds recipe_htmls_all-recipes.html (a single combined reference file)
from every recipe page in recipe_htmls/. Regenerate after adding a recipe:
    python3 build_all_recipes.py
"""
import os
import glob
import html
from bs4 import BeautifulSoup

# Run from the repo root: python3 scripts/build_all_recipes.py
RECIPE_DIR = "recipe_htmls"
OUTPUT_FILE = "all-recipes.html"


def text(el):
    return el.get_text(strip=True) if el else ""


def parse_recipe(path):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    title = text(soup.find("h1")) or os.path.basename(path)

    eyebrow = text(soup.find("div", class_="eyebrow"))

    source_a = soup.find("a", class_="source-link")
    source_url = source_a["href"].strip() if source_a and source_a.has_attr("href") else ""

    stats = {}
    for stat in soup.find_all("div", class_="stat"):
        label = text(stat.find("div", class_="label"))
        value = text(stat.find("div", class_="value"))
        if label:
            stats[label] = value

    # Ingredients panel: sequence of section-title + ul pairs
    ingredients_sections = []
    ing_panel = soup.find("section", class_="ingredients")
    if ing_panel:
        body = ing_panel.find("div", class_="panel-body")
        if body:
            current_title = "Ingredients"
            current_items = []
            for child in body.find_all(["div", "ul"], recursive=False):
                if "section-title" in (child.get("class") or []):
                    if current_items:
                        ingredients_sections.append((current_title, current_items))
                    current_title = text(child)
                    current_items = []
                elif child.name == "ul":
                    current_items = [text(li) for li in child.find_all("li")]
            if current_items:
                ingredients_sections.append((current_title, current_items))

    # Method panel: ordered list of steps
    steps = []
    method_panel = soup.find("section", class_="method")
    if method_panel:
        ol = method_panel.find("ol")
        if ol:
            steps = [text(li) for li in ol.find_all("li")]

    # Macros
    macros = {}
    macro_grid = soup.find("div", class_="macro-grid")
    if macro_grid:
        for macro in macro_grid.find_all("div", class_="macro"):
            num = text(macro.find("span", class_="num"))
            lab = text(macro.find("span", class_="lab"))
            if lab:
                macros[lab] = num

    macro_subtitle = ""
    note_cards = soup.find_all("div", class_="note-card")
    notes = []
    for card in note_cards:
        h3 = text(card.find("h3"))
        if h3.lower() == "estimated macros":
            p = card.find("p")
            macro_subtitle = text(p)
        elif h3.lower() == "notes":
            ul = card.find("ul")
            if ul:
                notes = [text(li) for li in ul.find_all("li")]

    return {
        "filename": os.path.basename(path),
        "title": title,
        "protein_tag": eyebrow,
        "source_url": source_url,
        "servings": stats.get("Servings", ""),
        "time": stats.get("Time", ""),
        "main_ingredients": stats.get("Main Ingredients", ""),
        "calories_stat": stats.get("Calories", ""),
        "ingredients_sections": ingredients_sections,
        "steps": steps,
        "macros": macros,
        "macro_subtitle": macro_subtitle,
        "notes": notes,
    }


def render_recipe_html(r):
    parts = []
    anchor = os.path.splitext(r["filename"])[0]
    parts.append(f'<section class="recipe" id="{html.escape(anchor)}">')
    parts.append(f'  <h2>{html.escape(r["title"])}</h2>')
    meta_bits = []
    if r["protein_tag"]:
        meta_bits.append(html.escape(r["protein_tag"]))
    meta_bits.append(f'File: recipe_htmls/{html.escape(r["filename"])}')
    if r["source_url"]:
        meta_bits.append(f'Source: <a href="{html.escape(r["source_url"])}">{html.escape(r["source_url"])}</a>')
    parts.append(f'  <p class="meta">{" &middot; ".join(meta_bits)}</p>')

    parts.append('  <ul class="stats">')
    if r["servings"]:
        parts.append(f'    <li><strong>Servings:</strong> {html.escape(r["servings"])}</li>')
    if r["time"]:
        parts.append(f'    <li><strong>Time:</strong> {html.escape(r["time"])}</li>')
    if r["main_ingredients"]:
        parts.append(f'    <li><strong>Main Ingredients:</strong> {html.escape(r["main_ingredients"])}</li>')
    if r["calories_stat"]:
        parts.append(f'    <li><strong>Calories:</strong> {html.escape(r["calories_stat"])}</li>')
    parts.append('  </ul>')

    if r["macros"]:
        macro_bits = [f'{html.escape(v)} {html.escape(k)}' for k, v in r["macros"].items()]
        parts.append(f'  <p class="macros"><strong>Macros ({html.escape(r["macro_subtitle"])}):</strong> {" &middot; ".join(macro_bits)}</p>')

    parts.append('  <h3>Ingredients</h3>')
    for section_title, items in r["ingredients_sections"]:
        if section_title and section_title != "Ingredients":
            parts.append(f'  <p class="section-label">{html.escape(section_title)}</p>')
        parts.append('  <ul class="ingredients">')
        for item in items:
            parts.append(f'    <li>{html.escape(item)}</li>')
        parts.append('  </ul>')

    parts.append('  <h3>Method</h3>')
    parts.append('  <ol class="method">')
    for step in r["steps"]:
        parts.append(f'    <li>{html.escape(step)}</li>')
    parts.append('  </ol>')

    if r["notes"]:
        parts.append('  <h3>Notes</h3>')
        parts.append('  <ul class="notes">')
        for note in r["notes"]:
            parts.append(f'    <li>{html.escape(note)}</li>')
        parts.append('  </ul>')

    parts.append('</section>')
    return "\n".join(parts)


def main():
    files = sorted(glob.glob(os.path.join(RECIPE_DIR, "*.html")))
    recipes = [parse_recipe(f) for f in files]
    recipes.sort(key=lambda r: r["title"].lower())

    toc_items = "\n".join(
        f'    <li><a href="#{html.escape(os.path.splitext(r["filename"])[0])}">{html.escape(r["title"])}</a></li>'
        for r in recipes
    )
    body_sections = "\n\n".join(render_recipe_html(r) for r in recipes)

    output = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>All Recipes — Combined Reference</title>
<style>
  body {{ font-family: sans-serif; max-width: 900px; margin: 0 auto; padding: 24px; line-height: 1.5; color: #222; }}
  h1 {{ margin-bottom: 4px; }}
  .subtitle {{ color: #666; margin-bottom: 24px; }}
  nav.toc {{ background: #f6f6f6; border-radius: 8px; padding: 16px 24px; margin-bottom: 40px; columns: 2; }}
  nav.toc li {{ margin-bottom: 4px; }}
  section.recipe {{ border-top: 2px solid #ddd; padding-top: 24px; margin-top: 32px; }}
  section.recipe h2 {{ margin-bottom: 4px; }}
  p.meta {{ color: #777; font-size: 14px; margin-bottom: 12px; }}
  ul.stats {{ list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 16px; font-size: 14px; margin-bottom: 12px; }}
  p.macros {{ font-size: 14px; margin-bottom: 16px; }}
  h3 {{ margin: 16px 0 6px; font-size: 16px; }}
  p.section-label {{ font-weight: 600; margin: 10px 0 2px; font-size: 13px; text-transform: uppercase; color: #555; }}
  ul.ingredients, ul.notes {{ margin: 0 0 8px; padding-left: 20px; }}
  ol.method {{ padding-left: 20px; }}
  ol.method li {{ margin-bottom: 6px; }}
</style>
</head>
<body>
<h1>All Recipes — Combined Reference</h1>
<p class="subtitle">Auto-generated from every file in recipe_htmls/. Regenerate with scripts/build_all_recipes.py after adding a new recipe. {len(recipes)} recipes.</p>

<nav class="toc">
<ul>
{toc_items}
</ul>
</nav>

{body_sections}

</body>
</html>
"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Wrote {OUTPUT_FILE} with {len(recipes)} recipes")


if __name__ == "__main__":
    main()
