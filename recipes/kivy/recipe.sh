#!/bin/bash

VERSION_kivy=${VERSION_kivy:-stable}
URL_kivy=https://github.com/kivy/kivy/zipball/$VERSION_kivy/kivy-$VERSION_kivy.zip
DEPS_kivy=(pyjnius android)
DEPS_OPTIONAL_kivy=(pygame sdl2)
MD5_kivy=
BUILD_kivy=$BUILD_PATH/kivy/$(get_directory $URL_kivy)
RECIPE_kivy=$RECIPES_PATH/kivy

function prebuild_kivy() {
	true
}

function build_kivy() {
	if [ -d "$BUILD_PATH/python-install/lib/python2.7/site-packages/kivy" ]; then
		return
	fi

	cd $BUILD_kivy

	push_arm

	export LDFLAGS="$LDFLAGS -L$LIBS_PATH"
	export LDSHARED="$LIBLINK"

	# sdl2 activated ?
	if [ "X$BUILD_sdl2" != "X" ]; then
		debug "Active flags for SDL2"
		export USE_SDL2=1
		export CFLAGS="$CFLAGS -I$BUILD_sdl2/include/"
		export LDFLAGS="$LDFLAGS -L$BUILD_sdl2/"
	fi
	if [ "X$BUILD_sdl2_image" != "X" ]; then
		debug "Active flags for SDL2_image"
		export CFLAGS="$CFLAGS -I$BUILD_sdl2_image/"
		export LDFLAGS="$LDFLAGS -L$BUILD_sdl2_image/"
	fi
	if [ "X$BUILD_sdl2_ttf" != "X" ]; then
		debug "Active flags for SDL2_ttf"
		export CFLAGS="$CFLAGS -I$BUILD_sdl2_ttf/"
		export LDFLAGS="$LDFLAGS -L$BUILD_sdl2_ttf/"
	fi
	if [ "X$BUILD_sdl2_mixer" != "X" ]; then
		debug "Active flags for SDL2_mixer"
		export CFLAGS="$CFLAGS -I$BUILD_sdl2_mixer/"
		export LDFLAGS="$LDFLAGS -L$BUILD_sdl2_mixer/"
	fi

	# fake try to be able to cythonize generated files
	$BUILD_PATH/python-install/bin/python.host setup.py build_ext
	try find . -iname '*.pyx' -exec cython {} \;
	try $BUILD_PATH/python-install/bin/python.host setup.py build_ext -v
	try find build/lib.* -name "*.o" -exec $STRIP {} \;
	try $BUILD_PATH/python-install/bin/python.host setup.py install -O2

	try rm -rf $BUILD_PATH/python-install/lib/python*/site-packages/kivy/tools

	unset LDSHARED
	pop_arm
}

function postbuild_kivy() {
	true
}
