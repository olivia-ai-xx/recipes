---
name: meal-prep
description: On-demand weekly meal-prep assistant for this recipe site. Pulls this week's pinned recipes, proposes a cook order and asks how many servings each should make, builds a grocery list formatted for pasting into Apple Notes, and regenerates meal-prep-guide.html with a Sunday prep-ahead plan. Invoke via /meal-prep. Never runs automatically.
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

## Step 2 — Read recipe data

Pull ingredients and method for each pinned recipe from `all-recipes.html` (it already has every recipe's ingredients and method in one file — faster than opening each page in `recipe_htmls/` individually). Fall back to the individual `recipe_htmls/FILENAME.html` file if a recipe isn't in `all-recipes.html` yet (e.g. it was just added and the reference file hasn't been rebuilt — in that case, rebuild it first with `python3 scripts/build_all_recipes.py`).

Read this data now, before asking anything, so the cook-order proposal in Step 3 is based on the actual recipes rather than guesswork.

## Step 3 — Ask servings and propose a cook order

Never assume serving counts. In one message, ask for servings **and** propose a cook order together:

1. List the pinned recipes with their default `serves` value from `index.html` and ask how many servings each should make.
2. In the same message, work out and propose a suggested cook order for the week:
   - For each recipe, identify what will realistically be prepped ahead on Sunday (sauces, marinades, cut produce, broths, etc.) based on the ingredients/method read in Step 2.
   - Find each recipe's single most time-sensitive prepped item using real food-safety/shelf-life judgement — not one blanket duration. As a rough guide: a marinade sitting on raw meat is only food-safe ~2 days; dairy- or mayo-based sauces keep ~4-5 days; vinaigrette-style or acid-based sauces keep longer; dry spice/batter mixes keep for weeks; cut alliums and firm veg keep several days to a couple of weeks depending on type.
   - Recommend cooking the recipe whose prepped components are shortest-lived first, and the one with the most shelf-life headroom last.
   - State the order with a one-line reason per recipe so the user can sanity-check it, e.g. "1) X first — its marinade is only good ~2 days, 2) Y next — its prepped veg lasts ~3-4 days, 3) Z last — its sauce keeps ~4-5 days."

Wait for the reply before doing any quantity math or writing anything. If the user gives servings for only some recipes, ask about the rest rather than guessing. The user may also push back on the order, or say they don't want to prep certain components ahead at all (e.g. "I won't pre-slice the protein or pre-make the base this week") — treat that as a per-week override: move those specific items to that recipe's "Leave Until Cooking Day" list in Steps 6-7 instead of the Sunday prep cards, and re-check whether it changes the recipe's place in the cook order (a recipe with nothing perishable prepped ahead is less time-sensitive and can move later).

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
- **Leave until cooking day**: things that oxidize, wilt, or go soggy if cut early — avocado, delicate herbs like basil once chopped, lettuce for a crisp bite, anything breaded/crumbed, anything meant to be cooked from raw for texture. Also anything the user opted out of prepping ahead this week (see Step 3).
- Use actual culinary judgement based on that recipe's ingredients — don't apply a fixed checklist blindly.

Be concrete, not vague, in every line item:

- **Chopping/peeling quantities**: always state how much. Whole/half units are already specific enough as-is (e.g. "½ red onion, sliced"). For anything else — garlic, ginger, herbs, etc. — give the actual gram weight or count from the scaled recipe rather than a vague descriptor (write "15g ginger, sliced", not "a thumb-sized piece of ginger").
- **Sauces/marinades**: never just say "make the bang bang sauce" — list the actual scaled ingredients and quantities that go into it, the same way they'd appear in a recipe's ingredient list, so the user isn't flipping back to the recipe page to prep it. Note which recipe each sauce/marinade belongs to.
- **Shelf life**: every prep-ahead item needs a "keeps for X in the fridge / airtight container" note, so the user knows how far in advance they can safely make it and how long it's good for once made. Use real food-safety judgement per item (a cut raw allium keeps longer than a dairy-based sauce; a marinating raw protein is generally good 1–2 days; a vinaigrette-style sauce keeps longer than a yoghurt-based one, etc.) — don't apply one blanket duration to everything.

Group prep-ahead items by task type rather than one flat list: vegetable/aromatic prep (split into **Chop & Peel** vs **Wash & Clean**), then **sauces & marinades**, then anything else that doesn't fit either (raw protein slicing, cooking noodles/rice ahead, etc.) as its own group. Only include a group if it actually has items in it that week — drop a group entirely rather than leaving it empty (e.g. if the user opted out of all protein/carb prep-ahead this week, there's no protein/carb prep group).

## Step 7 — Write meal-prep-guide.html

Overwrite `meal-prep-guide.html` at the repo root completely — it always reflects only the current week, never keep old versions or add a date-stamped copy. Reuse `index.html`'s visual system (`Inter` font, `--bg #f6f4f1`, `--card #fff`, `--text #22201d`, `--muted #6f6a63`, `--line #e9e3dc`, `--accent #c66b4e`, `--chip #f7efe8`, `--shadow 0 12px 30px rgba(43,33,24,.08)`, `--radius 22px`) so it looks like part of the same site. Keep the existing back-button link to `index.html` and the `🧊 Weekly Meal Prep` eyebrow tag from the current placeholder file — replace everything else. Structure, top to bottom:

1. **Header**: eyebrow, `<h1>Meal Prep Guide</h1>`, subtitle with the date and list of pinned recipes + confirmed servings.
2. **Suggested Cook Order card**: the order confirmed with the user in Step 3, as a numbered list — one row per recipe with a numbered badge, its name, and the one-line shelf-life reason for its position.
3. **Vegetable Prep card**: two labelled subsections, **Chop & Peel** first, then **Wash & Clean**. Each item is its own row with a checkbox, a bold quantity/description, and a note giving what it's for and its shelf life — never paragraph-style prose. Use a real `<input type="checkbox">` (styled with `accent-color: var(--accent)`) so the page works as a live checklist while cooking — checking an item should visually gray it out / strike it through via a CSS sibling selector, no JS required.
4. **Sauce & Marinade Prep card**: a responsive grid of boxes, one per sauce/marinade, each with: a title, a small "For: [Recipe Name]" tag, a checkable ingredient list (same checkbox treatment as above, one ingredient per line so it can be ticked off while measuring), an optional one-line method note, and a shelf-life line.
5. **Any other prep-ahead group** (e.g. protein slicing, cooking noodles/rice ahead) as its own card using the same box treatment as the sauce card — only if that group has items this week.
6. **Recipe Day-Of Guides card**: one `<details>`/`<summary>` per pinned recipe, collapsed by default (closed until the user clicks it — treat these like bookmarks, not always-visible sections). Use `summary::-webkit-details-marker { display: none; }` plus a custom toggle glyph. Inside each: a "Prep Ahead (Sunday)" list that references the cards above by name rather than repeating full ingredient lists, and a "Leave Until Cooking Day" list with full detail (including anything the user opted out of prepping ahead that week, called out explicitly, e.g. "not prepped ahead this week, by request").

## Step 8 — Review and push

Show the user the grocery list text and the rendered `meal-prep-guide.html` for review. Do not commit or push until they approve — same convention as the main recipe workflow in `CLAUDE.md`. Once approved, commit `meal-prep-guide.html` (and `all-recipes.html` if it was rebuilt in Step 2) and push to the current branch.
