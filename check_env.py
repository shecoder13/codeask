"""Environment check: imports key libraries and verifies SQLite FTS5 + sqlite-vec."""
import importlib
import sqlite3
import sys

print(f"python {sys.version.split()[0]}")
ok = True

for mod in ["typer", "rich", "pydantic", "httpx", "anthropic",
            "fastembed", "sqlite_vec", "yaml"]:
    try:
        importlib.import_module(mod)
        print(f"  ok   {mod}")
    except Exception as e:
        ok = False
        print(f"  FAIL {mod}: {e}")

try:
    import sqlite_vec
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    db.execute("CREATE VIRTUAL TABLE t USING fts5(body)")
    print(f"  ok   sqlite {sqlite3.sqlite_version}, FTS5, sqlite-vec {db.execute('select vec_version()').fetchone()[0]}")
except Exception as e:
    ok = False
    print(f"  FAIL sqlite FTS5/sqlite-vec: {e}")

print("ENV OK" if ok else "ENV HAS PROBLEMS")
sys.exit(0 if ok else 1)
