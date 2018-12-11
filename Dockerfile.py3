# Dockerfile with:
#   - Android build environment
#   - python-for-android dependencies
#
# Build with:
#     docker build --tag=p4apy3 .
#
# Run with:
#     docker run -it --rm p4apy3 /bin/sh -c '. venv/bin/activate && p4a apk --help'
#
# Or for interactive shell:
#     docker run -it --rm p4apy3
#
# Note:
#     Use 'docker run' without '--rm' flag for keeping the container and use
#     'docker commit <container hash> <new image>' to extend the original image

FROM python:3.7-stretch

ENV ANDROID_HOME="/opt/android"

RUN apt -y update -qq \
    && apt -y install -qq --no-install-recommends curl unzip \
    && apt -y autoremove \
    && apt -y clean


ENV ANDROID_NDK_HOME="${ANDROID_HOME}/android-ndk"
ENV ANDROID_NDK_VERSION="17c"
ENV ANDROID_NDK_HOME_V="${ANDROID_NDK_HOME}-r${ANDROID_NDK_VERSION}"

# get the latest version from https://developer.android.com/ndk/downloads/index.html
ENV ANDROID_NDK_ARCHIVE="android-ndk-r${ANDROID_NDK_VERSION}-linux-x86_64.zip"
ENV ANDROID_NDK_DL_URL="https://dl.google.com/android/repository/${ANDROID_NDK_ARCHIVE}"

# download and install Android NDK
RUN curl --location --progress-bar --insecure \
        "${ANDROID_NDK_DL_URL}" \
        --output "${ANDROID_NDK_ARCHIVE}" \
    && mkdir --parents "${ANDROID_NDK_HOME_V}" \
    && unzip -q "${ANDROID_NDK_ARCHIVE}" -d "${ANDROID_HOME}" \
    && ln -sfn "${ANDROID_NDK_HOME_V}" "${ANDROID_NDK_HOME}" \
    && rm -rf "${ANDROID_NDK_ARCHIVE}"


ENV ANDROID_SDK_HOME="${ANDROID_HOME}/android-sdk"

# get the latest version from https://developer.android.com/studio/index.html
ENV ANDROID_SDK_TOOLS_VERSION="3859397"
ENV ANDROID_SDK_TOOLS_ARCHIVE="sdk-tools-linux-${ANDROID_SDK_TOOLS_VERSION}.zip"
ENV ANDROID_SDK_TOOLS_DL_URL="https://dl.google.com/android/repository/${ANDROID_SDK_TOOLS_ARCHIVE}"

# download and install Android SDK
RUN curl --location --progress-bar --insecure \
        "${ANDROID_SDK_TOOLS_DL_URL}" \
        --output "${ANDROID_SDK_TOOLS_ARCHIVE}" \
    && mkdir --parents "${ANDROID_SDK_HOME}" \
    && unzip -q "${ANDROID_SDK_TOOLS_ARCHIVE}" -d "${ANDROID_SDK_HOME}" \
    && rm -rf "${ANDROID_SDK_TOOLS_ARCHIVE}"

# update Android SDK, install Android API, Build Tools...
RUN mkdir --parents "${ANDROID_SDK_HOME}/.android/" \
    && echo '### User Sources for Android SDK Manager' \
        > "${ANDROID_SDK_HOME}/.android/repositories.cfg"

# accept Android licenses (JDK necessary!)
RUN apt -y update -qq \
    && apt -y install -qq --no-install-recommends openjdk-8-jdk \
    && apt -y autoremove \
    && apt -y clean
RUN yes | "${ANDROID_SDK_HOME}/tools/bin/sdkmanager" --licenses > /dev/null

# download platforms, API, build tools
RUN "${ANDROID_SDK_HOME}/tools/bin/sdkmanager" "platforms;android-19" && \
    "${ANDROID_SDK_HOME}/tools/bin/sdkmanager" "platforms;android-27" && \
    "${ANDROID_SDK_HOME}/tools/bin/sdkmanager" "build-tools;26.0.2" && \
    chmod +x "${ANDROID_SDK_HOME}/tools/bin/avdmanager"


ENV USER="user"
ENV HOME_DIR="/home/${USER}"
ENV WORK_DIR="${HOME_DIR}" \
    PATH="${HOME_DIR}/.local/bin:${PATH}"

# install system dependencies
RUN apt -y update -qq \
    && apt -y install -qq --no-install-recommends \
        python3 virtualenv python3-pip wget lbzip2 patch sudo \
    && apt -y autoremove \
    && apt -y clean

# build dependencies
# https://buildozer.readthedocs.io/en/latest/installation.html#android-on-ubuntu-16-04-64bit
RUN dpkg --add-architecture i386 \
    && apt -y update -qq \
    && apt -y install -qq --no-install-recommends \
        build-essential ccache git python3 python3-dev \
        libncurses5:i386 libstdc++6:i386 libgtk2.0-0:i386 \
        libpangox-1.0-0:i386 libpangoxft-1.0-0:i386 libidn11:i386 \
        zip zlib1g-dev zlib1g:i386 \
    && apt -y autoremove \
    && apt -y clean

# specific recipes dependencies (e.g. libffi requires autoreconf binary)
RUN apt -y update -qq \
    && apt -y install -qq --no-install-recommends \
        libffi-dev autoconf automake cmake gettext libltdl-dev libtool pkg-config \
    && apt -y autoremove \
    && apt -y clean

# specific python-3.7 dependencies (e.g. libffi requires autoreconf binary)
#RUN apt -y update -qq \
#    && apt -y install -qq libreadline-gplv2-dev libncursesw5-dev libssl-dev \
#    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev zlib1g-dev openssl \
#    python3-setuptools \
#    && apt -y autoremove \
#    && apt -y clean

# Pull down Python 3.7, build, and install
#RUN mkdir /tmp/Python37 && cd /tmp/Python37 \
#    && wget https://www.python.org/ftp/python/3.7.1/Python-3.7.1.tar.xz \
#    && tar xvf Python-3.7.1.tar.xz \
#    && cd /tmp/Python37/Python-3.7.1 \
#    && ./configure \
#    && sudo make altinstall


# prepare non root env
RUN useradd --create-home --shell /bin/bash ${USER}

# with sudo access and no password
RUN usermod -append --groups sudo ${USER}
RUN echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers


RUN pip3 install --upgrade cython==0.28.6

WORKDIR ${WORK_DIR}
COPY . ${WORK_DIR}

# user needs ownership/write access to these directories
RUN chown --recursive ${USER} ${WORK_DIR} ${ANDROID_SDK_HOME}
USER ${USER}

# install python-for-android from current branch
RUN virtualenv --python=python3 venv \
    && . venv/bin/activate \
    && pip3 install -e .
