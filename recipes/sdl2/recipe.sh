#!/bin/bash

VERSION_sdl2=2.0.0
URL_sdl2=http://www.libsdl.org/release/SDL2-$VERSION_sdl2.tar.gz
MD5_sdl2=
DEPS_sdl2=()
BUILD_sdl2=$BUILD_PATH/sdl2/SDL2-$VERSION_sdl2
RECIPE_sdl2=$RECIPES_PATH/sdl2

function prebuild_sdl2() {
	true
}

function build_sdl2() {
	cd $SRC_PATH/jni
	ln -s $BUILD_sdl2 sdl2

	push_arm
	try ndk-build V=1 SDL2 application
	pop_arm

	try cp -a $SRC_PATH/obj/local/$ARCH/*.so $LIBS_PATH
}

function postbuild_sdl2() {
	true
}
