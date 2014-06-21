#!/bin/bash

VERSION_pycparser=${VERSION_pycparser:-2.10}
DEPS_pycparser=(kivy)
URL_pycparser=https://pypi.python.org/packages/source/p/pycparser/pycparser-2.10.tar.gz
MD5_pycparser=d87aed98c8a9f386aa56d365fe4d515f
BUILD_pycparser=$BUILD_PATH/pycparser/$(get_directory $URL_pycparser)
RECIPE_pycparser=$RECIPES_PATH/pycparser

# function called for preparing source code if needed
# (you can apply patch etc here.)
function prebuild_pycparser() {
	true
}

# function called to build the source code
function build_pycparser() {
	cd $BUILD_pycparser
	push_arm
	try $HOSTPYTHON setup.py install -O2
	pop_arm
}

# function called after all the compile have been done
function postbuild_pycparser() {
	true
}
