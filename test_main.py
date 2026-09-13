"""Smoke test for the API. Run with: uv run python test_main.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(tempfile.mkdtemp())  # main.py stores data relative to the working directory

from fastapi.testclient import TestClient
from main import app

c = TestClient(app)

assert "seriousdb" in c.get("/").text
assert c.get("/api/dbs").json() == ["default"]
assert c.put("/api/db", params={"key": "a", "value": "1"}).json() == "1"
assert c.get("/api/db", params={"key": "a"}).json() == "1"

assert c.post("/api/dbs/users").status_code == 201
assert c.post("/api/dbs/users").status_code == 409
assert c.post("/api/dbs/..%2Fescape").status_code in (404, 422)
c.put("/api/db", params={"db": "users", "key": "alice", "value": "admin"})
assert c.get("/api/dbs/users").json() == {"alice": "admin"}

assert c.patch("/api/dbs/users", params={"new_name": "people"}).json() == "people"
assert c.get("/api/dbs").json() == ["default", "people"]
assert os.path.isfile("sdb/people.sdb") and not os.path.exists("sdb/users.sdb")

assert c.delete("/api/db", params={"db": "people", "key": "alice"}).status_code == 200
assert c.get("/api/db", params={"db": "people", "key": "alice"}).status_code == 404

assert c.delete("/api/dbs/people").status_code == 200
assert c.get("/api/dbs").json() == ["default"]
assert not os.path.exists("sdb/people.sdb")

print("ok")
