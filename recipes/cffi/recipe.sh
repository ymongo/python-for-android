#!/bin/bash

VERSION_cffi=${VERSION_cffi:-0.8.2}
DEPS_cffi=(pycparser)
URL_cffi=https://pypi.python.org/packages/source/c/cffi/cffi-0.8.2.tar.gz
MD5_cffi=37fc88c62f40d04e8a18192433f951ec
BUILD_cffi=$BUILD_PATH/cffi/$(get_directory $URL_cffi)
RECIPE_cffi=$RECIPES_PATH/cffi

function prebuild_cffi() {
	true
}

function build_cffi() {
	cd $BUILD_cffi

	#try cp -f $BUILD_hostpython/build/lib.linux-x86_64-2.7/_io.so $BUILD_PATH/python-install/lib/python2.7/lib-dynload/_io.so
	#try cp -f $BUILD_hostpython/build/lib.linux-x86_64-2.7/unicodedata.so $BUILD_PATH/python-install/lib/python2.7/lib-dynload/unicodedata.so

	push_arm

	export LDFLAGS="$LDFLAGS -L$LIBS_PATH -L$BUILD_hostpython/Modules/_ctypes/libffi/src"
	export CFLAGS="$CFLAGS -I$BUILD_cffi/c -I$BUILD_hostpython/Modules/_ctypes/libffi_arm_wince"
	#export EXTRA_CFLAGS="--host linux-armv"

	try $HOSTPYTHON setup.py build
	try $HOSTPYTHON setup.py install -O2

	pop_arm
}

function postbuild_cffi() {
	true
}
