"""Build the browser exercise catalog using only the Python standard library."""
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent


def read_inside(root, name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise ValueError(f'Invalid exercise path: {name}')
    target = (root / name).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes exercise directory: {name}')
    return target.read_text(encoding='utf-8')


def catalog(exercises_dir):
    result, seen = [], set()
    for manifest in sorted(exercises_dir.glob('*/exercise.json')):
        item = json.loads(manifest.read_text(encoding='utf-8'))
        required = {'id', 'number', 'title', 'summary', 'target', 'duration',
                    'source', 'readonly', 'files'}
        if required - item.keys():
            raise ValueError(f'{manifest}: missing fields {sorted(required - item.keys())}')
        if not isinstance(item['id'], str) or not item['id'] or item['id'] in seen:
            raise ValueError(f'{manifest}: empty or duplicate exercise ID')
        seen.add(item['id'])
        if item['duration'] not in (60, 75, 90, 120):
            raise ValueError(f'{manifest}: duration must be 60, 75, 90, or 120')
        names = item['files']
        if not isinstance(names, list) or len(names) != len(set(names)):
            raise ValueError(f'{manifest}: files must be a list of unique paths')
        if item['source'] not in names or not set(item['readonly']) <= set(names):
            raise ValueError(f'{manifest}: source/read-only paths must be listed in files')
        if item['source'] in item['readonly']:
            raise ValueError(f'{manifest}: learner source must be editable')
        if 'tests/__init__.py' not in names:
            raise ValueError(f'{manifest}: tests/__init__.py is required')
        item['files'] = {name: read_inside(manifest.parent, name) for name in names}
        item['spec'] = read_inside(manifest.parent, 'README.md')
        result.append(item)
    if not result:
        raise ValueError('No exercise manifests found')
    return sorted(result, key=lambda item: item['number'])


def build(root=ROOT):
    items = catalog(root / 'exercises')
    destination = root / 'web' / 'exercises.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return items


if __name__ == '__main__':
    items = build()
    print(f'Built {len(items)} exercises into web/exercises.json')
