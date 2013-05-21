#!/bin/bash

VERSION_stlport=
URL_stlport=
DEPS_stlport=()
MD5_stlport=
BUILD_stlport=$ANDROIDNDK/sources/cxx-stl/stlport/
RECIPE_stlport=$RECIPES_PATH/stlport

function prebuild_stlport() {
	export LIB_stlport=$BUILD_stlport/libs/$ARCH/
	export INCLUDE_stlport=$BUILD_stlport/stlport
}

function build_stlport() {
	true
}

function postbuild_stlport() {
	true
}

