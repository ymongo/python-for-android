from pythonforandroid.python import GuestPythonRecipe
from pythonforandroid.patching import (
    is_darwin, is_api_gt, check_all, is_api_lt, is_ndk)


class Python2Recipe(GuestPythonRecipe):
    '''
    The python2's recipe.

    .. versionchanged:: 0.6.0
        Updated to version 2.7.15 and the build process has been changed in
        favour of the recently added class
        :class:`~pythonforandroid.python.GuestPythonRecipe`
    '''
    version = "2.7.15"
    url = 'https://www.python.org/ftp/python/{version}/Python-{version}.tgz'
    name = 'python2'

    depends = ['hostpython2']
    conflicts = ['python3crystax', 'python3', 'python2legacy']
    # opt_depends = ['openssl', 'sqlite3']

    patches = [
               # new 2.7.15 patches
               # ('patches/Python-2.7.15-fix-api-minor-than-21.patch',
               #  is_api_lt(21)), # todo: this should be tested
               'patches/fix-modules-initialization.patch',
               'patches/Python_{version}-ctypes-libffi-fix-configure.patch',
               'patches/ffi-config.sub-{version}.patch',
               'patches/fix-locale-{version}.patch',
               'patches/modules-locales-{version}.patch',
               'patches/fix-platform-{version}.patch',
               # migrated patches from 2.7.2
               'patches/fix-gethostbyaddr.patch',
               'patches/fix-filesystemdefaultencoding.patch',
               'patches/fix-termios.patch',
               'patches/custom-loader.patch',
               'patches/fix-remove-corefoundation.patch',
               'patches/fix-dynamic-lookup.patch',
               'patches/fix-dlfcn.patch',
               'patches/ctypes-find-library.patch',
               'patches/Python-{version}-ctypes-disable-wchar.patch',
               'patches/disable-modules.patch',
               'patches/verbose-compilation.patch',
               # migrated special patches from 2.7.2
               ('patches/fix-configure-darwin.patch', is_darwin),
               ('patches/fix-distutils-darwin.patch', is_darwin),
               ('patches/fix-ftime-removal.patch', is_api_gt(19)),
               ('patches/disable-openpty.patch', check_all(
                   is_api_lt(21), is_ndk('crystax')))
               ]

    configure_args = ('--host={android_host}',
                      '--build={android_build}',
                      '--enable-shared',
                      '--disable-ipv6',
                      '--disable-toolbox-glue',
                      '--disable-framework',
                      'ac_cv_file__dev_ptmx=yes',
                      'ac_cv_file__dev_ptc=no',
                      '--without-ensurepip',
                      'ac_cv_little_endian_double=yes',

                      # why python3 works without it?
                      'ac_cv_header_langinfo_h=no',

                      '--prefix={prefix}',
                      '--exec-prefix={exec_prefix}')


recipe = Python2Recipe()
