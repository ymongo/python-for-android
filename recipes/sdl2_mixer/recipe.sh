#!/bin/bash

VERSION_sdl2_mixer=2.0.0
URL_sdl2_mixer=http://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-$VERSION_sdl2_mixer.tar.gz
MD5_sdl2_mixer=
DEPS_sdl2_mixer=(sdl2)
BUILD_sdl2_mixer=$BUILD_PATH/sdl2_mixer/SDL2_mixer-$VERSION_sdl2_mixer
RECIPE_sdl2_mixer=$RECIPES_PATH/sdl2_mixer

function prebuild_sdl2_mixer() {
	true
}

function build_sdl2_mixer() {
	cd $SRC_PATH/jni
	ln -s $BUILD_sdl2_mixer sdl2_mixer

	push_arm
	try ndk-build V=1 SDL2_mixer \
		SUPPORT_MOD_MODPLUG=false \
		SUPPORT_MOD_MIKMOD=false \
		SUPPORT_MP3_SMPEG=false
	pop_arm

	try cp -a $SRC_PATH/obj/local/$ARCH/*.so $LIBS_PATH
}

function postbuild_sdl2_mixer() {
	true
}
