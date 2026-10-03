# Deployment — Financial Intelligence Copilot

The service runs on **GCP Cloud Run** (`financial-copilot-api`, region `asia-south1`), deployed by GitHub Actions.

> **A push to `main` rebuilds and redeploys production.** `.github/workflows/deploy.yml` has no path filter, so a docs-only merge also redeploys. Work on a branch and merge only when you intend to release.

## Pipeline

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `.github/workflows/ci.yml` | every push and pull request | Python 3.11, `pip install -r requirements-dev.txt`, `pytest -m "not integration" -q` |
| `.github/workflows/deploy.yml` | push to `main`, or manual `workflow_dispatch` | downloads the index, builds and pushes the image, deploys to Cloud Run |

Deploy steps, in order:

1. Download release asset `chroma_db_linux.zip` from release `v0.1.0-data` and unzip it into `data/` (the prebuilt ChromaDB index is baked into the image).
2. Authenticate to Google Cloud with `GCP_SA_KEY`.
3. Build the image and push it to Artifact Registry: `asia-south1-docker.pkg.dev/<GCP_PROJECT_ID>/ml-apis/financial-copilot-api:<git sha>`.
4. `gcloud run deploy financial-copilot-api` with: 2Gi memory, 1 CPU, min 0 / max 2 instances, `--allow-unauthenticated`, env var `OPENROUTER_API_KEY`.

## GitHub secrets (Settings → Secrets and variables → Actions)

| Secret | Used for |
|--------|----------|
| `GCP_SA_KEY` | service-account JSON for Google Cloud authentication |
| `GCP_PROJECT_ID` | project that owns Artifact Registry and Cloud Run |
| `OPENROUTER_API_KEY` | passed to the container as an environment variable |

`GITHUB_TOKEN` is provided by GitHub automatically (used to download the release asset). Never commit values; the local env file is gitignored.

## Updating the search index

The index is not built in CI. It is a release asset.

1. Add or change PDFs in `data/raw_pdfs/` (see [DATA_SOURCES.md](DATA_SOURCES.md)).
2. Rebuild locally: `python scripts/build_index.py`.
3. Zip `data/chroma_db` as `chroma_db_linux.zip` (the archive must unzip to `data/chroma_db/`) and upload it to release `v0.1.0-data`, replacing the old asset.
4. Trigger a deploy (push to `main` or run the workflow manually).

## Run the container locally

```bash
docker compose up --build   # needs a local env file (copy .env.example); serves on http://localhost:8080
```

`docker-compose.yml` maps `${PORT:-8080}`, loads the env file, mounts `data/raw_pdfs` and `data/chroma_db`, and health-checks `/health`. The image listens on `$PORT` (default 8080), which is also how Cloud Run injects its port.

## Verify a deployment

```bash
curl https://financial-copilot-api-242711953247.asia-south1.run.app/health
```

Expect `"status": "ok"` and a non-zero `chunk_count`. The UI is at `/app`.

## Roll back

List revisions, then send all traffic to a previous one:

```bash
gcloud run revisions list --service financial-copilot-api --region asia-south1
gcloud run services update-traffic financial-copilot-api --region asia-south1 --to-revisions <REVISION>=100
```
