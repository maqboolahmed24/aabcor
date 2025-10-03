How to enable auto-builds (GitHub Actions)

This folder contains a reusable GitHub Actions workflow template to auto-build the landing page CSS and regenerate the Open Graph image on pushes/PRs.

Files
- gh-workflows/landingpage-build.yml - copy this file to the root of your landing page repo at .github/workflows/landingpage-build.yml.

Steps
1) In your landing page repo, create the folder .github/workflows if it doesn’t exist.
2) Copy gh-workflows/landingpage-build.yml to .github/workflows/landingpage-build.yml.
3) If your landing page is not at repo root, edit working-directory and the paths globs accordingly.
4) Commit and push. The workflow will install Node deps, build dist/styles.css, and (optionally) regenerate og.png.

Notes
- The workflow commits built assets back on push to keep static hosts simple. Remove the git-auto-commit step if you prefer artifact-only builds.
- GITHUB_TOKEN needs contents: write on your repo (default for most setups).
