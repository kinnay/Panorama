
set -e

deptry .
mypy .

VERSION=$(python3 increment_version.py)
python3 -m build
twine upload \
    dist/panorama_tools-$VERSION.tar.gz \
    dist/panorama_tools-$VERSION-py3-none-any.whl
git add pyproject.toml
git commit -m "Increment version number"
git push
