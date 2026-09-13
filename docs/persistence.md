# Persistence

Each database is stored as a JSON file `sdb/<name>.sdb`, relative to the process working directory.

On startup every `sdb/*.sdb` file is loaded into memory. If there are none, a `default` database is created with:

```python
{"default": "default"}
```

An old single-database `.sdb` file in the working directory is moved to `sdb/default.sdb` on startup.

Each write changes the in-memory dictionary and writes the complete dictionary of that database back to disk.

## Current constraints

- The files are local to the machine running the server.
- Requests use the complete dictionary rather than a database engine.
- Multi-process access is not coordinated; run a single server process.
