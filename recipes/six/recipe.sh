#!/bin/bash

VERSION_six=${VERSION_six:-1.7.2}
DEPS_six=()
URL_six=https://pypi.python.org/packages/source/s/six/six-1.7.2.tar.gz
MD5_six=4c26276583b01dfc73474cb32327af91
BUILD_six=$BUILD_PATH/six/$(get_directory $URL_six)
RECIPE_six=$RECIPES_PATH/six

# function called for preparing source code if needed
# (you can apply patch etc here.)
function prebuild_six() {
	true
}

# function called to build the source code
function build_six() {
	cd $BUILD_six
	push_arm
	try $HOSTPYTHON setup.py install -O2
	pop_arm
}

# function called after all the compile have been done
function postbuild_six() {
	true
}
