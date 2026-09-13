import json
import os
import re
from pathlib import Path
from fastapi import APIRouter, FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from threading import Lock

class Cache:
    def __init__(self):
        self.filename = None
        self.db = None
        self.lock = Lock()


def insert(key: str, value: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(status_code=404, detail=f"Database file {cache.filename} could not be opened and loaded")
        cache.db[key] = value
    return value


def select(key: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(status_code=404, detail=f"Database file {cache.filename} could not be opened and loaded")
        val = cache.db.get(key, None)
    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    return val


def remove(key: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(status_code=404, detail=f"Database file {cache.filename} could not be opened and loaded")
        if key not in cache.db:
            raise HTTPException(status_code=404, detail=f"No value set for key {key}")
        del cache.db[key]


def load(filename: str, cache: Cache):
    with cache.lock:
        db_file = filename
        if not os.path.isfile(db_file):
            with open(db_file, "wb") as f:
                json_dumps = json.dumps({"default": "default"}).encode()
                f.write(json_dumps)
            cache.db = {"default": "default"}
        else:
            with open(filename, "rb") as f:
                binary_text = f.read()
                json_text = binary_text.decode()
                cache.db = json.loads(json_text)
        cache.filename = filename


def flush(cache: Cache):
    with cache.lock:
        if cache.db is None:
            return
        with open(cache.filename, "wb+") as f:
            json_dumps = json.dumps(cache.db).encode()
            f.write(json_dumps)


# Each named database lives in its own file: sdb/<name>.sdb
data_dir = "sdb"
name_pattern = re.compile(r"[A-Za-z0-9_-]{1,64}")
caches: dict[str, Cache] = {}
registry_lock = Lock()


def db_path(name: str):
    return os.path.join(data_dir, f"{name}.sdb")


def check_name(name: str):
    if not name_pattern.fullmatch(name):
        raise HTTPException(status_code=422, detail="Database name must be 1-64 letters, digits, '_' or '-'")


def get_cache(name: str):
    cache = caches.get(name)
    if cache is None:
        raise HTTPException(status_code=404, detail=f"Database {name} not found")
    return cache


os.makedirs(data_dir, exist_ok=True)
if os.path.isfile(".sdb") and not os.path.exists(db_path("default")):
    os.replace(".sdb", db_path("default"))  # migrate the old single-database file
for filename in sorted(os.listdir(data_dir)):
    name = filename.removesuffix(".sdb")
    if filename.endswith(".sdb") and name_pattern.fullmatch(name):
        caches[name] = Cache()
        load(db_path(name), caches[name])
if not caches:
    caches["default"] = Cache()
    load(db_path("default"), caches["default"])

app = FastAPI()
api = APIRouter(prefix="/api")
dashboard_file = Path(__file__).parent / "dashboard" / "index.html"


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(dashboard_file)


@api.put("/db")
def put(key: str, value: str, db: str = "default"):
    cache = get_cache(db)
    insert(key, value, cache)
    flush(cache)
    return value


@api.get("/db")
def get(key: str, db: str = "default"):
    return select(key, get_cache(db))


@api.delete("/db")
def delete(key: str, db: str = "default"):
    cache = get_cache(db)
    remove(key, cache)
    flush(cache)


@api.get("/dbs")
def list_dbs():
    return sorted(caches)


@api.get("/dbs/{name}")
def get_db(name: str):
    cache = get_cache(name)
    with cache.lock:
        if cache.db is None:
            raise HTTPException(status_code=404, detail=f"Database {name} not found")
        return dict(cache.db)


@api.post("/dbs/{name}", status_code=201)
def create_db(name: str):
    check_name(name)
    with registry_lock:
        if name in caches:
            raise HTTPException(status_code=409, detail=f"Database {name} already exists")
        cache = Cache()
        cache.filename = db_path(name)
        cache.db = {}
        flush(cache)
        caches[name] = cache
    return name


@api.patch("/dbs/{name}")
def rename_db(name: str, new_name: str):
    check_name(new_name)
    with registry_lock:
        cache = get_cache(name)
        if new_name in caches:
            raise HTTPException(status_code=409, detail=f"Database {new_name} already exists")
        with cache.lock:
            os.replace(cache.filename, db_path(new_name))
            cache.filename = db_path(new_name)
        caches[new_name] = caches.pop(name)
    return new_name


@api.delete("/dbs/{name}")
def delete_db(name: str):
    with registry_lock:
        cache = get_cache(name)
        with cache.lock:
            os.remove(cache.filename)
            cache.db = None
        del caches[name]


app.include_router(api)
