#!/bin/bash

VERSION_sdl2_image=2.0.0
URL_sdl2_image=http://www.libsdl.org/projects/SDL_image/release/SDL2_image-$VERSION_sdl2_image.tar.gz
MD5_sdl2_image=
DEPS_sdl2_image=(sdl2)
BUILD_sdl2_image=$BUILD_PATH/sdl2_image/SDL2_image-$VERSION_sdl2_image
RECIPE_sdl2_image=$RECIPES_PATH/sdl2_image

function prebuild_sdl2_image() {
	true
}

function build_sdl2_image() {
	cd $SRC_PATH/jni
	ln -s $BUILD_sdl2_image sdl2_image

	push_arm
	try ndk-build V=1 SDL2_image SUPPORT_WEBP=false
	pop_arm

	try cp -a $SRC_PATH/obj/local/$ARCH/*.so $LIBS_PATH
}

function postbuild_sdl2_image() {
	true
}
