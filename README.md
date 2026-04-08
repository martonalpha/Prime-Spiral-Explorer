# Prime Spiral Explorer

Prime Spiral Explorer is a self-contained 3D visualization of prime numbers and semiprimes. It renders several mathematical views in a single static HTML page, so the result can be published directly with GitHub Pages and shared as a public portfolio project.

## What it includes

- 3D helix view for prime and semiprime structure
- Ulam-inspired 3D tower and validation analytics
- Fibonacci sphere, clustering, modulo, zeta, and vector views
- Static output in `docs/index.html` for easy hosting

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

The script generates the public site into `docs/index.html` and opens it in the browser.

## Publish on GitHub Pages

1. Create a new public repository, for example `prime-spiral-explorer`.
2. Run:

```powershell
git init
git add .
git commit -m "Initial publish"
git branch -M main
git remote add origin https://github.com/<your-username>/prime-spiral-explorer.git
git push -u origin main
```

3. In GitHub, open `Settings -> Pages`.
4. Set the source to `Deploy from a branch`.
5. Select branch `main` and folder `/docs`.
6. Save. GitHub will publish `docs/index.html` as the site entry point.

## SEO notes

- The generated page includes a descriptive title, meta description, Open Graph tags, robots meta, and visible explanatory copy above and below the visualization.
- Static explanatory text is important here, because the interactive Plotly chart alone is weak SEO content.
- For stronger SEO later, add a custom domain and a real preview image for Open Graph sharing.

## Project structure

- `main.py`: generates the visualization and the publishable HTML site
- `docs/index.html`: public static site output
- `docs/robots.txt`: basic crawl allowance for static hosting
- `requirements.txt`: Python dependencies
