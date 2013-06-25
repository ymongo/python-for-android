#!/bin/bash

VERSION_pyzmq=13.0.2
URL_pyzmq=https://pypi.python.org/packages/source/p/pyzmq/pyzmq-$VERSION_pyzmq.tar.gz
DEPS_pyzmq=(zeromq python)
MD5_pyzmq=
BUILD_pyzmq=$BUILD_PATH/pyzmq/$(get_directory $URL_pyzmq)
RECIPE_pyzmq=$RECIPES_PATH/pyzmq

function prebuild_pyzmq() {
	true
}

function build_pyzmq() {
	if [ -d "$BUILD_PATH/python-install/lib/python2.7/site-packages/pyzmq" ]; then
		return
	fi

	cd $BUILD_pyzmq

	push_arm

	export CFLAGS="$CFLAGS -I$INSTALL_PATH/include"
	export CXXFLAGS="$CXXFLAGS -I$INSTALL_PATH/include"
	export LDFLAGS="$LDFLAGS -L$INSTALL_PATH/lib"
	export LDSHARED="$LIBLINK"

	# fake try to be able to cythonize generated files
	echo <<END >setup.cfg
[global]
zmq_prefix = $BUILD_PATH/install/
have_sys_un_h = False
END

       $SHELL
	$BUILD_PATH/python-install/bin/python.host setup.py build_ext --zmq=$BUILD_PATH/install/

	try find build/lib.* -name "*.o" -exec $STRIP {} \;
	try $BUILD_PATH/python-install/bin/python.host setup.py install -O2

	try rm -rf $BUILD_PATH/python-install/lib/python*/site-packages/pyzmq/tools

	unset LDSHARED
	pop_arm
}

function postbuild_pyzmq() {
	true
}
