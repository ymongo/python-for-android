#!/bin/bash

VERSION_libcrypt=0.03
URL_libcrypt=http://sourceforge.net/projects/libcrypt/files/libcrypt/$VERSION_libcrypt/crypt_${VERSION_libcrypt/./_}.zip
DEPS_libcrypt=()
BUILD_libcrypt=$BUILD_PATH/libcrypt/$(get_directory $URL_libcrypt)
RECIPE_libcrypt=$RECIPES_PATH/libcrypt

function prebuild_libcrypt() {
	sed -i "s/-mpentium //" $BUILD_PATH/libcrypt/makefile
	try rm  $BUILD_PATH/libcrypt/crypt_0_03
	if [ ! -d $BUILD_libcrypt ]
	then
		mkdir $BUILD_libcrypt
		cp $BUILD_PATH/libcrypt/* $BUILD_libcrypt
	fi
	true
}

function build_libcrypt() {
	cd $BUILD_libcrypt

	if [ -f libcrypt.a ]; then
		return
	fi

	push_arm

	try make

	pop_arm
}

function postbuild_libcrypt() {
	true
}
