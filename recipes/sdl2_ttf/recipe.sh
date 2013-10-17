#!/bin/bash

VERSION_sdl2_ttf=2.0.12
URL_sdl2_ttf=http://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-$VERSION_sdl2_ttf.tar.gz
MD5_sdl2_ttf=
DEPS_sdl2_ttf=(sdl2)
BUILD_sdl2_ttf=$BUILD_PATH/sdl2_ttf/SDL2_ttf-$VERSION_sdl2_ttf
RECIPE_sdl2_ttf=$RECIPES_PATH/SDL2_ttf

function prebuild_sdl2_ttf() {
	true
}

function build_sdl2_ttf() {
	cd $SRC_PATH/jni
	ln -s $BUILD_sdl2_ttf sdl2_ttf

	push_arm
	try ndk-build V=1 SDL2_ttf
	pop_arm

	try cp -a $SRC_PATH/obj/local/$ARCH/*.so $LIBS_PATH
}

function postbuild_sdl2_ttf() {
	true
}
