from pythonforandroid.recipe import TargetPythonRecipe, Recipe
from pythonforandroid.toolchain import shprint, current_directory, info
from pythonforandroid.patching import (is_darwin, is_api_gt,
                                       check_all, is_api_lt, is_ndk)
from pythonforandroid.logger import (logger, Err_Fore)
from pythonforandroid.util import ensure_dir
from os.path import exists, join, realpath
from os import environ
import sh


# Here we set data for python's optional libraries, any optional future library
# should be referenced into variable `libs_info` and maybe in `versioned_libs`.
# Perhaps some additional operations had to be performed in functions:
#     - set_libs_flags: if the path for library/includes is in some location
#                       defined dynamically by some function.
#     - do_python_build: if python has some specific argument to enable
#                        external library support.

# versioned_libs is a list with versioned libraries
versioned_libs = ['openssl']

# libs_info is a dict where his keys are the optional recipes,
# each value of libs_info is a dict:
#    - includes: list of includes (should be relative paths
#                which point to the includes).
#    - lib_links: list of ldflags needed to link python with the library.
#    - lib_path: relative path pointing to the library location,
#                (if is set to None, the library's build dir will be taken).
libs_info = {
    'openssl': {
        'includes': ['include', join('include', 'openssl')],
        'lib_links': ['-lcrypto', '-lssl'],
        'lib_path': None,
    },
    'sqlite3': {
        'includes': [''],
        'lib_links': ['-lsqlite3'],
        'lib_path': None,
    },
    'libffi': {
        'includes': ['include'],
        'lib_links': ['-lffi'],
        'lib_path': '.libs',
    },
    'libexpat': {
        'includes': ['lib'],
        'lib_links': ['-lexpat'],
        'lib_path': join('expat', 'lib', '.libs'),
    },
}


class Python3Recipe(TargetPythonRecipe):
    version = '3.7.0'
    url = 'https://www.python.org/ftp/python/{version}/Python-{version}.tgz'
    name = 'python3'

    depends = ['hostpython3']
    conflicts = ['python3crystax', 'python2']
    opt_depends = ['libffi', 'libexpat', 'openssl', 'sqlite3']
    # TODO: More patches maybe be needed, but with those
    # two we successfully build and run a simple app
    patches = ['patches/python-{version}-libs.patch'.format(version=version),
               'patches/fix-termios.patch']

    def set_libs_flags(self, env, arch=None):
        # Takes an env as argument and adds cflags/ldflags
        # based on libs_info and versioned_libs.
        env['OPENSSL_BUILD'] = '/path-to-openssl'
        env['SQLITE3_INC_DIR'] = '/path-to-sqlite3-includes'
        env['SQLITE3_LIB_DIR'] = '/path-to-sqlite3-library'

        for lib in self.opt_depends:
            if lib in self.ctx.recipe_build_order:
                logger.info(
                    ''.join((Err_Fore.MAGENTA, '-> Activating flags for ', lib,
                             Err_Fore.RESET)))
                r = Recipe.get_recipe(lib, self.ctx)
                b = r.get_build_dir(arch.arch)

                # Sets or modifies include/library base paths,
                # this should point to build directory, and some
                # libs has special build directories...so...
                # here we deal with it.
                inc_dir = b
                lib_dir = b
                if lib == 'sqlite3':
                    lib_dir = r.get_lib_dir(arch)
                elif lib == 'libffi':
                    inc_dir = join(inc_dir, r.get_host(arch))
                    lib_dir = join(lib_dir, r.get_host(arch))
                elif lib == 'libexpat':
                    inc_dir = join(b, 'expat')

                # It establishes the include's flags taking into
                # account the information provided in libs_info.
                if libs_info[lib]['includes']:
                    includes = [
                        join(inc_dir, p) for p in libs_info[lib]['includes']]
                else:
                    includes = [inc_dir]
                i_flags = ' -I' + ' -I'.join(includes)

                # It establishes the linking's flags taking into
                # account the information provided in libs_info.
                if libs_info[lib]['lib_path']:
                    lib_dir = join(lib_dir, libs_info[lib]['lib_path'])
                if lib not in versioned_libs:
                    l_flags = ' -L' + lib_dir + ' ' + ' '.join(
                        libs_info[lib]['lib_links'])
                else:
                    l_flags = ' -L' + lib_dir + ' ' + ' '.join(
                        [i + r.version for i in libs_info[lib]['lib_links']])

                # Inserts or appends to env.
                f = 'CPPFLAGS'
                env[f] = env[f] + i_flags if f in env else i_flags
                f = 'LDFLAGS'
                env[f] = env[f] + l_flags if f in env else l_flags

                # Sets special python compilation flags for some libs.
                # The openssl and sqlite env variables are set
                # via patch: patches/python-3.7.0-libs.patch
                if lib == 'openssl':
                    env['OPENSSL_BUILD'] = b
                    env['OPENSSL_VERSION'] = r.version
                elif lib == 'sqlite3':
                    env['SQLITE3_INC_DIR'] = inc_dir
                    env['SQLITE3_LIB_DIR'] = lib_dir
                elif lib == 'libffi':
                    env['LIBFFI_CFLAGS'] = env['CFLAGS'] + i_flags
                    env['LIBFFI_LIBS'] = l_flags
        return env

    def build_arch(self, arch):
        recipe_build_dir = self.get_build_dir(arch.arch)
        
        # Create a subdirectory to actually perform the build
        build_dir = join(recipe_build_dir, 'android-build')
        ensure_dir(build_dir)

        # TODO: Get these dynamically, like bpo-30386 does
        sys_prefix = '/usr/local'
        sys_exec_prefix = '/usr/local'

        # Skipping "Ensure that nl_langinfo is broken" from the original bpo-30386

        with current_directory(build_dir):
            env = environ.copy()

            # TODO: Get this information from p4a's arch system
            android_host = 'arm-linux-androideabi'
            android_build = sh.Command(join(recipe_build_dir, 'config.guess'))().stdout.strip().decode('utf-8')
            platform_dir = join(self.ctx.ndk_dir, 'platforms', 'android-21', 'arch-arm')
            toolchain = '{android_host}-4.9'.format(android_host=android_host)
            toolchain = join(self.ctx.ndk_dir, 'toolchains', toolchain, 'prebuilt', 'linux-x86_64')
            CC = '{clang} -target {target} -gcc-toolchain {toolchain}'.format(
                clang=join(self.ctx.ndk_dir, 'toolchains', 'llvm', 'prebuilt', 'linux-x86_64', 'bin', 'clang'),
                target='armv7-none-linux-androideabi',
                toolchain=toolchain)

            AR = join(toolchain, 'bin', android_host) + '-ar'
            LD = join(toolchain, 'bin', android_host) + '-ld'
            RANLIB = join(toolchain, 'bin', android_host) + '-ranlib'
            READELF = join(toolchain, 'bin', android_host) + '-readelf'
            STRIP = join(toolchain, 'bin', android_host) + '-strip --strip-debug --strip-unneeded'

            env['CC'] = CC
            env['AR'] = AR
            env['LD'] = LD
            env['RANLIB'] = RANLIB
            env['READELF'] = READELF
            env['STRIP'] = STRIP

            ndk_flags = '--sysroot={ndk_sysroot} -D__ANDROID_API__=21 -isystem {ndk_android_host}'.format(
                ndk_sysroot=join(self.ctx.ndk_dir, 'sysroot'),
                ndk_android_host=join(self.ctx.ndk_dir, 'sysroot', 'usr', 'include', android_host))
            sysroot = join(self.ctx.ndk_dir, 'platforms', 'android-21', 'arch-arm')
            env['CFLAGS'] = env.get('CFLAGS', '') + ' ' + ndk_flags
            env['CPPFLAGS'] = env.get('CPPFLAGS', '') + ' ' + ndk_flags
            env['LDFLAGS'] = env.get('LDFLAGS', '') + ' --sysroot={} -L{}'.format(sysroot, join(sysroot, 'usr', 'lib'))

            # Manually add the libs directory, and copy some object
            # files to the current directory otherwise they aren't
            # picked up. This seems necessary because the --sysroot
            # setting in LDFLAGS is overridden by the other flags.
            # TODO: Work out why this doesn't happen in the original
            # bpo-30386 Makefile system.
            logger.warning('Doing some hacky stuff to link properly')
            lib_dir = join(sysroot, 'usr', 'lib')
            env['LDFLAGS'] += ' -L{}'.format(lib_dir)
            shprint(sh.cp, join(lib_dir, 'crtbegin_so.o'), './')
            shprint(sh.cp, join(lib_dir, 'crtend_so.o'), './')

            env['SYSROOT'] = sysroot

            # TODO: All the env variables should be moved
            # into method: get_recipe_env (all above included)
            env = self.set_libs_flags(env, arch)

            # Arguments for python configure
            # TODO: move ac_xx_ arguments to config.site
            configure_args = [
                '--host={android_host}',
                '--build={android_build}',
                '--enable-shared',
                '--disable-ipv6',
                '--without-ensurepip',
                '--prefix={prefix}',
                '--exec-prefix={exec_prefix}',
                'ac_cv_file__dev_ptmx=yes',
                'ac_cv_file__dev_ptc=no',
                'ac_cv_little_endian_double=yes'
                ]
            if 'libffi' in self.ctx.recipe_build_order:
                configure_args.append('--with-system-ffi')
            if 'libexpat' in self.ctx.recipe_build_order:
                configure_args.append('--with-system-expat')

            if not exists('config.status'):
                shprint(sh.Command(join(recipe_build_dir, 'configure')),
                        *(' '.join(configure_args).format(
                            android_host=android_host,
                            android_build=android_build,
                            prefix=sys_prefix,
                            exec_prefix=sys_exec_prefix)).split(' '), _env=env)

            if not exists('python'):
                shprint(sh.make, 'all', _env=env)

            # TODO: Look into passing the path to pyconfig.h in a
            # better way, although this is probably acceptable
            sh.cp('pyconfig.h', join(recipe_build_dir, 'Include'))

    def include_root(self, arch_name):
        return join(self.get_build_dir(arch_name),
                    'Include')

    def link_root(self, arch_name):
        return join(self.get_build_dir(arch_name),
                    'android-build')
            
recipe = Python3Recipe()
