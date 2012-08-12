.PHONY: all

all:
	-rm -rf ../../../dist/javawrapper
	cd ../../.. && ./distribute.sh -d 'javawrapper' -m 'kivy'
	cp -a javawrapper ../../../dist/javawrapper/src/org/
	cd ../../../dist/javawrapper/ && ./build.py \
		--package org.pythonandroid.test \
		--name TestJavaWrapper --version 1 \
		--private ../../src/tests/javawrapper/python \
		--permission VIBRATE \
		debug installd 
	adb logcat
