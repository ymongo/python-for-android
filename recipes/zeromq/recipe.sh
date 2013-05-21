#!/bin/bash

VERSION_zeromq=3.2.3
URL_zeromq=http://download.zeromq.org/zeromq-$VERSION_zeromq.tar.gz
DEPS_zeromq=(stlport)
MD5_zeromq=
BUILD_zeromq=$BUILD_PATH/zeromq/$(get_directory $URL_zeromq)
RECIPE_zeromq=$RECIPES_PATH/zeromq

function prebuild_zeromq() {
	true
}

function build_zeromq() {
	cd $BUILD_zeromq

	if [ -f src/.libs/zeromq.a ]; then
		return
	fi

	push_arm

	export CXXFLAGS="$CXXFLAGS -I$INCLUDE_stlport -Wno-long-long"
	export LDFLAGS="-L$LIB_stlport -lstlport_static"


	try ./configure --host=arm-linux-androideabi --enable-static --disable-shared --prefix=$INSTALL_PATH
	try cd src
	try make install
	bash

	pop_arm
}

function postbuild_zeromq() {
	true
}
