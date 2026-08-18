# Scripts

## Supported research publication tool

- `research_publish.py` — fail-closed, one-way projection from a local checkout of `sguzman/ai-research-reports` into Hugo posts. It never edits the source repository, publishes only canonical `ready` or `published` articles with `draft: false`, defaults to dry-run mode, and refuses to overwrite posts it does not manage.

Example:

```bash
python scripts/research_publish.py --source ../ai-research-reports --slug example-article
python scripts/research_publish.py --source ../ai-research-reports --slug example-article --write
```

## Legacy migration tooling

The following predate the current publication boundary and should be treated as legacy migration/cleanup utilities rather than trusted publishing automation:

- `ai_reports_sync.py`
- `ai_reports_publish.py`

In particular, legacy tooling may rewrite source metadata or infer publication state from the existence of blog files. That behavior is intentionally excluded from the new pipeline.

Do not wire legacy scripts into GitHub Actions. The existing Pages workflow should remain a build/deploy step for content that has already been deliberately committed to Marginalia.
