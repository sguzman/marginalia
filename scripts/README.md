# Scripts

## Supported research publication tool

`research_publish.py` is the fail-closed, one-way projection from a checkout of `sguzman/ai-research-reports` into **build-derived** Hugo research content.

The canonical repository remains the only editorial source of truth. Marginalia does not commit generated research copies as ordinary source content. During the site build, the workflow checks out the canonical corpus, removes the migration-era `content/posts` mirror from the ephemeral workspace, and materializes only publication-gated packages beneath `content/research/`.

A package is eligible only when all of the following are true:

- canonical `status` is `ready` or `published`;
- `draft: false`;
- `editorial_profile` is one of the approved profile classes;
- the package has an article-local `CHANGELOG.md`;
- `editorial.duplicate_review.status` is `reviewed` or `not-applicable`;
- local assets stay beneath the package's canonical `assets/` directory and exist;
- publishable source contains no unsupported Mermaid/unfenced diagram source or broken fence structure.

Untouched legacy `published` metadata is therefore not sufficient by itself to put an article on the site.

Examples for local inspection:

```bash
python scripts/research_publish.py --source ../ai-research-reports --slug example-article
python scripts/research_publish.py --source ../ai-research-reports --slug example-article --write
python scripts/research_publish.py --source ../ai-research-reports --all --write
```

`--all --write` resets `content/research/` before projection so an article removed from the publication gate cannot survive as stale generated output. The generated directory is ignored by Git and is intended to exist only locally or inside the Pages build workspace.

The GitHub Pages workflow also quarantines the historical `content/posts/` mirror from the build. Those files remain in repository history for provenance, but they are not deployed. If the publication gate yields zero articles, the homepage renders an **Articles coming soon** state.

## Legacy migration tooling

The following predate the current publication boundary and should be treated as legacy migration/cleanup utilities rather than trusted publishing automation:

- `ai_reports_sync.py`
- `ai_reports_publish.py`

In particular, legacy tooling may rewrite source metadata or infer publication state from the existence of blog files. That behavior is intentionally excluded from the current pipeline.

Do not wire legacy scripts into GitHub Actions. The Pages workflow builds only the build-derived research projection plus non-legacy site infrastructure.
