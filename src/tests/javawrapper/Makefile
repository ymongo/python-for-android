.PHONY: all build clean tests

clean:
	-rm -rf ../../../dist/javawrapper;

build:
	cd ../../.. && ./distribute.sh -d 'javawrapper' -m 'kivy'
	cp -a javawrapper ../../../dist/javawrapper/src/org/

tests:
	cd ../../../dist/javawrapper/ && ./build.py \
		--package org.pythonandroid.test \
		--name TestJavaWrapper --version 1 \
		--private ../../src/tests/javawrapper/python \
		--permission VIBRATE \
		debug installd && adb logcat -c && adb logcat

all: clean build tests
