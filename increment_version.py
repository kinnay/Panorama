
import toml


def find_jungle_version() -> str:
    data = toml.load("../jungle/pyproject.toml")
    return data["project"]["version"]


with open("pyproject.toml") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith("version = "):
        version = line.split('"')[1]
        parts = [int(part) for part in version.split(".")]
        parts[-1] += 1
        version = ".".join(str(part) for part in parts)
        print(version)
        line = f'version = "{version}"\n'
    elif "jungle-package == " in line:
        line = f'    "jungle-package == {find_jungle_version()}"\n'
    lines[i] = line


with open("pyproject.toml", "w") as f:
    f.writelines(lines)
