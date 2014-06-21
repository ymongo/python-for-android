#!/bin/bash

VERSION_pynacl=${VERSION_pynacl:-0.2.3}
DEPS_pynacl=(libsodium)
URL_pynacl=https://pypi.python.org/packages/source/P/PyNaCl/PyNaCl-0.2.3.tar.gz
MD5_pynacl=eb78a000454e878ee77f574d3c90e344
BUILD_pynacl=$BUILD_PATH/pynacl/$(get_directory $URL_pynacl)
RECIPE_pynacl=$RECIPES_PATH/pynacl

function prebuild_pynacl() {
	true
}

function shouldbuild_pynacl() {
#	if [ -d "$SITEPACKAGES_PATH/libsodium" ]; then
#		DO_BUILD=0
#	fi
	true
}

function build_pynacl() {

	
	cd $BUILD_pynacl

#	export CC="$CC -I$BUILD_pynacl/_lib"
#	export LDFLAGS="$LDFLAGS -L$LIBS_PATH -L$BUILD_pynacl"
#
#	export EXTRA_CFLAGS="--host linux-armv"
#	try $HOSTPYTHON setup.py install -O2
	
	push_arm
	export SODIUM_INSTALL="system"

	export LDFLAGS="$LDFLAGS -L$LIBS_PATH -L$BUILD_hostpython/Modules/_ctypes/libffi/src"
	export CFLAGS="$CFLAGS -I$BUILD_cffi/c -I$BUILD_hostpython/Modules/_ctypes/libffi_arm_wince"
	export CFLAGS="$CFLAGS -I$BUILD_libsodium/build/include"
	export LDFLAGS="$LDFLAGS -L$BUILD_libsodium/build/lib"

	try $HOSTPYTHON setup.py build -f -v
	try $HOSTPYTHON setup.py install -O2 -f -v

	pop_arm
	return

	export CC="$CC -I$BUILD_libsodium/include -I/home/cryptoloft/Downloads/kivy-remote-shell/.buildozer/android/platform/python-for-android/build/hostpython/Python-2.7.2/Modules/_ctypes/libffi/build/lib/libffi-3.0.10rc0/include"
	export LDFLAGS="$LDFLAGS -L$LIBS_PATH -L$BUILD_libsodium/lib -L/home/cryptoloft/Downloads/kivy-remote-shell/.buildozer/android/platform/python-for-android/build/hostpython/Python-2.7.2/Modules/_ctypes/libffi/build/lib"
	
	read -p "try to build, Press enter to continue (smurfy)..."
	
	export PYTHONPATH=$BUILD_PATH/hostpython/Python-2.7.2/Lib/site-packages
        try $BUILD_PATH/hostpython/Python-2.7.2/hostpython setup.py install -O2 --root=$BUILD_PATH/python-install --install-lib=lib/python2.7/site-packages
	
	#try $HOSTPYTHON setup.py build_ext -v
#	try find build/lib.* -name "*.o" -exec $STRIP {} \;
	#try $HOSTPYTHON setup.py install -O2

#	try rm -rf $SITEPACKAGES/libsodium/test
	
	pop_arm
}

# function called after all the compile have been done
function postbuild_pynacl() {
	true
}
