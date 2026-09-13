# API reference

The server exposes a small HTTP API through FastAPI under `/api`. The web dashboard is served at `/`.

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

Every key-value route takes an optional `db` parameter naming the database. It defaults to `default`.

### PUT `/api/db`

Stores or updates a key-value pair.

Parameters:

- `key` - The key to store.
- `value` - The value associated with the key.
- `db` - Database name (optional, default `default`).

### GET `/api/db`

Retrieves the value associated with `key`. Returns `404` if the key does not exist.

### DELETE `/api/db`

Deletes `key`. Returns `404` if the key does not exist.

## Databases

Database names are 1-64 characters: letters, digits, `_` or `-`.

| Method | Route | Description |
| --- | --- | --- |
| GET | `/api/dbs` | List database names. |
| GET | `/api/dbs/{name}` | Return all key-value pairs of a database. |
| POST | `/api/dbs/{name}` | Create an empty database. `409` if it exists. |
| PATCH | `/api/dbs/{name}?new_name=...` | Rename a database. `409` if `new_name` exists. |
| DELETE | `/api/dbs/{name}` | Delete a database and its file. |
