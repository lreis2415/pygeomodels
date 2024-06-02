#!/usr/bin/env bash
#
#    This file is aimed for reCompile and reInstall pygeomodels for debugging on Linux/Unix platform.
#
#    pygeomodels is distributed for Research and/or Education only,
#    any commercial purpose will be FORBIDDEN.
#    pygeomodels is an open-source project,
#    but WITHOUT ANY WARRANTY; WITHOUT even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#    See the GNU General Public License for more details.
#

# This script accepts one optional argument, i.e., the executable of python

# Set default executable of python
pythonexec=${1:-python}

cd "$PWD" || exit
rm -r dist
rm -r build
$pythonexec -m pip install tox
$pythonexec -m pip install wheel
$pythonexec setup.py bdist_wheel
cd dist || { echo "Cannot find dist directory! Reinstall pygeomodels failed!"; exit 1; }
if $pythonexec -c "import pygeomodels" &> /dev/null; then
    echo 'pygeomodels has been installed, and will be uninstalled first.'
    $pythonexec -m pip install pygeomodels
else
    echo 'pygeomodels will be firstly installed.'
fi
for i in $(find . -name '*.whl'); do $pythonexec -m pip install "$i" --upgrade --force-reinstall; done
