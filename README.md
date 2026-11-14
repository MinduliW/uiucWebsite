# SSA-Lab @ UIUC — GitHub Pages static site

This is a static mirror of your Wix content.

## Deploy
1. Create a new GitHub repository.
2. Upload the files in this folder.
3. Settings → Pages → Deploy from a branch → `main` → `/ (root)`.

## Swap content
- Edit `index.html` to update text.
- Replace image URLs with local images if you prefer bundling assets.

## Illinois look and feel
Every page (`index.html`, `about.html`, `news.html`, `people.html`, `research.html`, `teaching.html`, `publications.html`, `contact.html`) uses the [Illinois Web Toolkit v3](https://builder3.toolkit.illinois.edu/) loaded from
`cdn.toolkit.illinois.edu` for the campus header, footer, fonts, colours, buttons and cards.
Lab-specific layout lives in `site.css`; behaviour (rotating tagline, debris video loops) in `site.js`.
The header and footer markup is repeated in each page, so a menu or footer change must be made in all eight files.
`styles.css` and `script.js` are only used by the older `indexold.html`.

## Publications: automatic updates from Google Scholar
`publications.html` is rebuilt from `data/publications.json` by `scripts/update_publications.py`.
A GitHub Actions workflow (`.github/workflows/update-publications.yml`) runs it every Monday, and on demand
from the Actions tab ("Run workflow"). It reads the Scholar profile, adds papers that are not yet in the JSON,
rewrites the list between the `PUBLICATIONS:START` / `PUBLICATIONS:END` markers, and commits the result.

- **One-time setup:** repository Settings → Actions → General → Workflow permissions → "Read and write permissions".
- **If Google blocks the run** (it sometimes refuses requests from GitHub's servers), create a key at serpapi.com and
  save it as a repository secret named `SERPAPI_KEY`; the script then goes through SerpAPI instead.
- **Fixing an entry:** edit `data/publications.json`. Change `category` (`preprint`, `journal`, `conference`, `other`),
  point `url` at the publisher, set a `badge` such as `"Accepted"`, or set `"hidden": true` to keep it off the page.
  Existing entries are never overwritten, so edits stick; this also means a preprint that later appears in a journal
  must be updated by hand.
- **Do not edit the list inside `publications.html` directly**; it is overwritten on the next run.
- Run locally with `python3 scripts/update_publications.py` (add `--no-fetch` to only re-render).
