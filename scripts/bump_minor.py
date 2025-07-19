import re
import pathlib
import toml

pyproject = pathlib.Path('pyproject.toml')
data = toml.load(pyproject)
version = data['project']['version']
major, minor, patch = map(int, version.split('.'))
minor += 1
patch = 0
new_version = f"{major}.{minor}.{patch}"

data['project']['version'] = new_version
pyproject.write_text(toml.dumps(data))

init_path = pathlib.Path('promptify_ai/__init__.py')
content = init_path.read_text()
content = re.sub(r'__version__ = "[0-9.]+"', f'__version__ = "{new_version}"', content)
init_path.write_text(content)

print(new_version)
