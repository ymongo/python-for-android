#!/bin/bash

VERSION_libsodium=${VERSION_libsodium:-0.5.0}
URL_libsodium=https://download.libsodium.org/libsodium/releases/libsodium-$VERSION_libsodium.tar.gz
DEPS_libsodium=(kivy)
MD5_libsodium=6e61dbde3a6b06b898a0e18ca27ab161
BUILD_libsodium=$BUILD_PATH/libsodium/$(get_directory $URL_libsodium)
RECIPE_libsodium=$RECIPES_PATH/libsodium

function prebuild_libsodium() {
	true
}

function shouldbuild_libsodium() {
	if [ -f "$BUILD_libsodium/lib/libsodium.a" ]; then
		DO_BUILD=0
	fi
}

function build_libsodium() {
	cd $BUILD_libsodium
	#read -p "try to build, Press enter to continue (smurfy)..."
	push_arm

	try ./configure --build=i686-pc-linux-gnu --host=arm-linux-eabi --prefix=$BUILD_libsodium/build/
	try make install

	pop_arm
}

function postbuild_libsodium() {
	true
}
