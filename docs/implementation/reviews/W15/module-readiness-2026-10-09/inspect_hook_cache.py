"""Read only the standard pre-commit cache's installed public hook metadata."""
import json
from pathlib import Path
import sqlite3

CACHE = Path.home() / '.cache/pre-commit'
EXPECTED = (
    ('https://github.com/pre-commit/pre-commit-hooks', 'v5.0.0'),
    ('https://github.com/psf/black', '26.5.1'),
    ('https://github.com/PyCQA/isort', '7.0.0'),
    ('https://github.com/pre-commit/mirrors-mypy', 'v1.19.0'),
    ('https://github.com/Yelp/detect-secrets', 'v1.5.0'),
)

if __name__ == '__main__':
    con = sqlite3.connect((CACHE / 'db.db').as_uri() + '?mode=ro', uri=True)
    try:
        rows = con.execute('SELECT repo, ref, path FROM repos').fetchall()
    finally:
        con.close()
    result = []
    for name, revision in EXPECTED:
        matches = []
        for repo, ref, raw_path in rows:
            if ref == revision and (repo == name or repo.startswith(name + ':')):
                path = Path(raw_path)
                if path.resolve().is_relative_to(CACHE.resolve()):
                    env = path / 'py_env-python3'
                    state = [p.name for p in env.glob('.install_state*') if p.is_file()]
                    matches.append(dict(directory=path.name, environment=env.name,
                                        installed=bool(state), state_markers=state,
                                        additional_dependencies=repo[len(name):]))
        result.append(dict(public_hook=name.rsplit('/', 1)[-1], revision=revision, matches=matches))
    print(json.dumps(dict(standard_cache=str(CACHE), hooks=result,
                         cache_written=False, source_written=False), indent=2))
