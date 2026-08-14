---
name: meal-prep
description: On-demand weekly meal-prep assistant for this recipe site. Pulls this week's pinned recipes, asks how many servings each should make, builds a grocery list formatted for pasting into Apple Notes, and regenerates meal-prep-guide.html with a Sunday prep-ahead plan. Invoke via /meal-prep. Never runs automatically.
---

This skill only runs when the user explicitly invokes `/meal-prep`. Never run any part of it proactively or on a schedule.

## Step 1 — Get this week's pinned recipes

The site's "pinned this week" list lives in a published Google Sheet CSV, the same one `index.html` reads client-side:

```
https://docs.google.com/spreadsheets/d/e/2PACX-1vQfwQp96tJdcpTwgRxY-z8AbNH6IVQ3toQisDCWAy-7AFx0yaERVwfsCHpv1zKKLTjN6RrFQGzw4Kxr/pub?gid=1218956679&single=true&output=csv
```

Try to fetch it (WebFetch, or `curl` via Bash). **This can fail** — in some sandboxed environments `docs.google.com` is blocked at the network egress layer (`EGRESS_BLOCKED` or a proxy 403). If the fetch fails for any reason, don't retry blindly — just ask the user to open the Pin tab and paste in the current list of pinned recipe titles or filenames, then continue with what they give you.

Each row is a recipe page URL — take the filename (the part after the last `/`) and match it against the `file` field in `recipes` array in `index.html`, or against the filenames in `all-recipes.html`, to get each pinned recipe's title.

If nothing is pinned, tell the user and stop — there's nothing to build a plan for.

## Step 2 — Ask servings for each pinned recipe

Never assume serving counts. List the pinned recipes with their default `serves` value from `index.html`, and ask in one plain message, e.g.:

> This week you've got **Marry Me Chicken** (default 2 serves), **Korean Beef Rice Bowls** (default 2 serves), and **No Bean Chili** (default 6 serves) pinned. How many servings do you want each one to make?

Wait for the reply before doing any quantity math. If the user gives a number for only some recipes, ask about the rest rather than guessing.

## Step 3 — Read recipe data

Pull ingredients and method for each pinned recipe from `all-recipes.html` (it already has every recipe's ingredients and method in one file — faster than opening each page in `recipe_htmls/` individually). Fall back to the individual `recipe_htmls/FILENAME.html` file if a recipe isn't in `all-recipes.html` yet (e.g. it was just added and the reference file hasn't been rebuilt — in that case, rebuild it first with `python3 scripts/build_all_recipes.py`).

## Step 4 — Scale ingredients to the confirmed servings

For each recipe, scale every ingredient quantity from the recipe's base `serves` to the servings the user just confirmed (same scaling approach as the main recipe-generation workflow in `CLAUDE.md`: multiply by target/base ratio, round to clean numbers — nearest 5g/ml for weights/volumes, whole units for items like eggs or cloves). Leave non-quantified ingredients (e.g. "Salt", "Pepper to taste") as-is.

## Step 5 — Build the grocery list

Aggregate the scaled ingredients across *all* pinned recipes into one deduplicated list:

- Combine the same ingredient across recipes by summing quantities when units match (e.g. two recipes both needing chicken thighs → one combined line).
- **Exclude only salt, pepper, and oil** — include everything else, even things some people keep stocked (garlic, onion, stock, spices, sauces), since the user wants to check what needs restocking.
- Group into aisles: **Produce**, **Meat & Seafood**, **Dairy & Chilled**, **Pantry & Sauces**, **Herbs & Spices**.

Output the list as **plain text** (no markdown bold/headers) directly in chat, formatted to be copy-pasted straight into an Apple Notes note called "Weekly Groceries", replacing its previous contents. Example shape:

```
WEEKLY GROCERIES — [date]

PRODUCE
- 2 red onions
- 400g cherry tomatoes

MEAT & SEAFOOD
- 900g chicken thighs

DAIRY & CHILLED
- 250ml light cream

PANTRY & SAUCES
- 2 tbsp gochujang

HERBS & SPICES
- 1 bunch coriander
```

Tell the user this block is ready to select-all and paste over last week's note.

## Step 6 — Build the meal-prep-ahead plan

For each pinned recipe, read its method and ingredients and reason about what's actually safe and sensible to prep on Sunday versus what should wait:

- **Prep ahead (Sunday)**: things like peeling garlic, chopping onions/carrots/peppers that hold up in the fridge, mixing dry spice blends, making sauces/marinades that improve or hold fine for a few days, marinating proteins that benefit from time, washing+drying sturdy greens.
- **Leave until cooking day**: things that oxidize, wilt, or go soggy if cut early — avocado, delicate herbs like basil once chopped, lettuce for a crisp bite, anything breaded/crumbed, anything meant to be cooked from raw for texture.
- Use actual culinary judgement based on that recipe's ingredients — don't apply a fixed checklist blindly.

Also build one **consolidated Sunday checklist** across all pinned recipes (e.g. one "peel all garlic" line instead of repeating per recipe, one combined "chop all onions" line, etc.).

## Step 7 — Write meal-prep-guide.html

Overwrite `meal-prep-guide.html` at the repo root completely — it always reflects only the current week, never keep old versions or add a date-stamped copy. Reuse `index.html`'s visual system (`Inter` font, `--bg #f6f4f1`, `--card #fff`, `--text #22201d`, `--muted #6f6a63`, `--line #e9e3dc`, `--accent #c66b4e`, `--chip #f7efe8`, `--shadow 0 12px 30px rgba(43,33,24,.08)`, `--radius 22px`) so it looks like part of the same site. Keep the existing back-button link to `index.html` and the `🧊 Weekly Meal Prep` eyebrow tag from the current placeholder file — replace everything else. Structure:

1. Header: eyebrow, `<h1>Meal Prep Guide</h1>`, subtitle with the date and list of pinned recipes + confirmed servings.
2. A "Sunday Prep Checklist" card with the consolidated checklist from Step 6.
3. One card per pinned recipe: title, servings, "Prep Ahead" list, "Leave Until Cooking Day" list, and "Sauces & Marinades to Premix" list if applicable.

## Step 8 — Review and push

Show the user the grocery list text and the rendered `meal-prep-guide.html` for review. Do not commit or push until they approve — same convention as the main recipe workflow in `CLAUDE.md`. Once approved, commit `meal-prep-guide.html` (and `all-recipes.html` if it was rebuilt in Step 3) and push to the current branch.
