#!/bin/bash

VERSION_hostpython=2.7.2
URL_hostpython=http://python.org/ftp/python/$VERSION_hostpython/Python-$VERSION_hostpython.tar.bz2
MD5_hostpython=ba7b2f11ffdbf195ee0d111b9455a5bd
BUILD_hostpython=$BUILD_PATH/hostpython/$(get_directory $URL_hostpython)
RECIPE_hostpython=$RECIPES_PATH/hostpython

export HOSTPYTHON_SITEPACKAGES="$BUILD_PATH/hostpython/site-packages"
export PYTHONPATH="$PYTHONPATH:$HOSTPYTHON_SITEPACKAGES/lib/python2.7:$HOSTPYTHON_SITEPACKAGES/lib/python2.7/site-packages"

function prebuild_hostpython() {
	cd $BUILD_hostpython
	try cp $RECIPE_hostpython/Setup Modules/Setup
}

function shouldbuild_hostpython() {
	cd $BUILD_hostpython
	if [ -f hostpython ]; then
		DO_BUILD=0
	fi
}

function build_hostpython() {
	# placeholder for building
	cd $BUILD_hostpython

    try ./configure
    try make -j5
    try mv Parser/pgen hostpgen

	if [ -f python.exe ]; then
		try mv python.exe hostpython
	elif [ -f python ]; then
		try mv python hostpython
	else
		error "Unable to found the python executable?"
		exit 1
	fi


	# install setuptools for easier port of python extension
	cd $BUILD_PATH
	if [ ! -f setuptools-5.1.tar.gz ]; then
		try wget "https://pypi.python.org/packages/source/s/setuptools/setuptools-5.1.tar.gz#md5=c26e47ce8d7b46bd354e68301f410fb8"
	fi
	tar xzf setuptools-5.1.tar.gz
	cd setuptools-5.1
	echo $BUILD_hostpython/hostpython setup.py install --prefix $HOSTPYTHON_SITEPACKAGES

	cp -a $BUILD_hostpython/build/lib.*/*.so $HOSTPYTHON_SITEPACKAGES/lib/python2.7
}

function postbuild_hostpython() {
	# placeholder for post build
	true
}
