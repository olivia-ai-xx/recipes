# Recipe Website – Claude Code Instructions

This project is a recipe website hosted on GitHub Pages. When asked to generate a new recipe HTML file, follow every rule in this document exactly.

-----

## Site Structure

```
/
├── index.html               ← Homepage (recipes array lives here)
├── RECIPE_TEMPLATE.html     ← Master template — read this before every recipe
└── recipe_htmls/
    └── recipe-name.html     ← Individual recipe pages
```

- Back button on all recipe pages links to: `../index.html`
- Source link always points to the original recipe URL
- All recipe HTML files go in: `recipe_htmls/`

-----

## Workflow — Follow This Order Every Time

### 1. Fetch the recipe

- If given a URL, fetch the recipe from it.
- If the site is inaccessible, ask the user to paste the recipe text.

### 2. Determine the base serving size

- If the recipe explicitly states how many it serves, use that number.
- If not, estimate a sensible yield based on the ingredients and portion sizes.

### 3. Ask the user how many servings they want

Always confirm before generating. Example:

> “This recipe yields 4 serves. How many would you like it to yield?”

### 4. Scale all ingredient quantities

Scale all ingredients up or down to match the confirmed serving size.

### 5. Apply healthy ingredient swaps (silently)

Make these substitutions automatically without flagging them, unless the calorie difference is significant:

|Original                     |Swap                                                |
|-----------------------------|----------------------------------------------------|
|Coconut milk                 |Lite coconut milk                                   |
|Heavy cream / thickened cream|Light cream (e.g. Elmlea Single Light or equivalent)|

Add a note in the Notes card if the swap meaningfully changes the dish’s texture or flavour.

### 6. Calculate calories and macros yourself

- Use **Woolworths Australia** ingredient nutritional data.
- **Ignore any calories or macros stated in the original recipe** — do not use them even as a reference.
- Scale to the confirmed serving size.
- Round calories to the nearest 5 kcal; protein/carbs/fat to the nearest gram.

### 7. Check for duplicate recipe name

- List the files in `recipe_htmls/` and compare the new recipe’s name against existing filenames.
- If a file with the same name (or very similar name) already exists, flag it to the user before proceeding:

> “A recipe called ‘Butter Chicken’ (`butter-chicken.html`) already exists. Do you want to overwrite it, save this as a variation (e.g. `butter-chicken-2.html`), or cancel?”
- Only proceed once the user has confirmed.

### 8. Generate the HTML file

- Base the file **exactly** on `RECIPE_TEMPLATE.html` — read it first with the Read tool.
- Do not deviate from the template’s layout, CSS, or structure.
- Save the file to `recipe_htmls/FILENAME.html`.

### 9. Output the index.html entry

After the file, always output the line to add to the recipes array in `index.html`:

```js
{ title: "TITLE", file: "FILENAME.html", protein: "PROTEIN", time: "TIME", serves: X, cals: XXX,
  ingredients: ["INGREDIENT", "INGREDIENT", ...] },
```

### 10. Show the final recipe and get approval before pushing

- Render/display the final recipe HTML to the user for review.
- **Do not commit or push to GitHub until the user explicitly approves.**
- Wait for the user to confirm before proceeding with any git operations.

-----

## Template Rules

Read `RECIPE_TEMPLATE.html` before generating every recipe. Key structural rules:

- **Hero section**: eyebrow protein tag · recipe title · source link · 4 stat boxes (Servings, Time, Main Ingredients, Calories)
- **Two-panel layout**: Ingredients panel (left) · Recipe/Method panel (right)
- **Footer**: two cards — Estimated Macros and Notes
- **Macro card subtitle**: `Per serving, based on X serves. Estimated using Woolworths AU ingredients.`
- Ingredient sections within the panel are grouped with `<div class="section-title">` headings (e.g. Marinade, Sauce, To Serve)

-----

## Protein Tags

Use exactly one protein tag per recipe. Pick the best match.

|Emoji|Tag label       |`protein` value for index|
|-----|----------------|-------------------------|
|🍗    |Chicken         |`chicken`                |
|🥩    |Beef            |`beef`                   |
|🐷    |Pork            |`pork`                   |
|🐑    |Lamb            |`lamb`                   |
|🐟    |Seafood         |`seafood`                |
|🥦    |Vegetarian      |`vegetarian`             |
|🌱    |Vegan           |`vegan`                  |
|🥚    |Egg             |`egg`                    |
|🫘    |Tofu            |`tofu`                   |
|🦃    |Turkey          |`turkey`                 |
|♻️    |Leftover Chicken|`leftover-chicken`       |

-----

## Ingredients Array (for index.html search)

The `ingredients` array powers ingredient-based search on the homepage. Rules:

**Include** main/hero ingredients: the protein, fresh produce, dairy, specialty sauces, carbs, and fresh herbs.

Examples: `chicken thighs`, `mango`, `avocado`, `halloumi`, `udon noodles`, `jasmine rice`, `coconut milk`, `sun-dried tomatoes`, `coriander`, `basil`, `dill`

**Exclude** pantry staples assumed to be on hand year-round:
salt · pepper · spices · dried herbs · soy sauce · fish sauce · olive oil · butter · flour · sugar · vinegar · garlic · onion · stock

The goal: surface recipes based on fresh or specialty ingredients someone has on hand, not common pantry items.

-----

## File Naming Convention

Use lowercase kebab-case matching the recipe title.

Examples:

- Butter Chicken → `butter-chicken.html`
- Thai Basil Pork → `thai-basil-pork.html`
- Mango Prawn Salad → `mango-prawn-salad.html`

-----

## Checklist Before Saving

- [ ] Checked `recipe_htmls/` for an existing file with the same or similar name
- [ ] Read `RECIPE_TEMPLATE.html` first
- [ ] Confirmed serving size with user
- [ ] All ingredients scaled to confirmed serving size
- [ ] Healthy swaps applied
- [ ] Macros calculated from Woolworths AU data (not from original recipe)
- [ ] Correct protein tag and emoji
- [ ] Source link points to original URL
- [ ] Back button links to `../index.html`
- [ ] File saved to `recipe_htmls/`
- [ ] index.html entry outputted
- [ ] Final recipe shown to user and approval received before pushing to GitHub