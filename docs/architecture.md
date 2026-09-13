# Architecture

The application is currently intentionally small:

- `main.py` creates the FastAPI application and defines the HTTP routes under `/api`.
- `dashboard/index.html` is a single-file web dashboard (no build step) served at `/`.
- Each named database is a Python dictionary held in memory (`Cache`) and written to `sdb/<name>.sdb`.

There is no separate database process or client library.

## Request flow

1. FastAPI receives a request.
2. The route looks up the named database's in-memory cache.
3. A write updates the dictionary and rewrites that database's file; a read returns from memory.
4. The route returns the result or a `404` error.
