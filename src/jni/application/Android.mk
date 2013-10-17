LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE := application

LOCAL_CFLAGS := $(foreach D, $(APP_SUBDIRS), -I$(LOCAL_PATH)/$(D)) \
				-I$(LOCAL_PATH)/../SDL2/include \
				-I$(LOCAL_PATH)/../SDL2_mixer \
				-I$(LOCAL_PATH)/../SDL2_image \
				-I$(LOCAL_PATH)/../SDL2_ttf \
				-I$(LOCAL_PATH)/../intl \
				-I$(LOCAL_PATH)/.. \
				-I$(LOCAL_PATH)/../../../build/python-install/include/python2.7


LOCAL_CFLAGS += $(APPLICATION_ADDITIONAL_CFLAGS)

#Change C++ file extension as appropriate
LOCAL_CPP_EXTENSION := .cpp

LOCAL_SRC_FILES := ../sdl2/src/main/android/SDL_android_main.c src/start.c
LOCAL_SHARED_LIBRARIES := SDL2
LOCAL_STATIC_LIBRARIES := jpeg png
LOCAL_LDLIBS := -lpython2.7 -lGLESv1_CM -ldl -llog -lz
LOCAL_LDFLAGS += -L$(LOCAL_PATH)/../../../build/python-install/lib

include $(BUILD_SHARED_LIBRARY)
