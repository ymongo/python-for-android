
from pythonforandroid.recipe import TargetPythonRecipe, Recipe
from pythonforandroid.toolchain import shprint, current_directory, info
from pythonforandroid.patching import (is_linux, is_darwin, is_api_gt,
                                       check_all, is_api_lt, is_ndk)
from os.path import exists, join, realpath
import sh


class Python2Recipe(TargetPythonRecipe):
    version = "2.7.12"
    url = 'http://python.org/ftp/python/{version}/Python-{version}.tgz'
    name = 'python2'

    depends = ['hostpython2']
    conflicts = ['python3crystax', 'python3']
    opt_depends = ['openssl', 'libffi', 'sqlite3']

    patches = [  # APPLY NEW 2.7.12 PATCHES
               'patches/Python-{version}-xcompile.patch',
               'patches/Python_{version}-ctypes-libffi-fix-configure.patch',
               'patches/ffi-config.sub-{version}.patch',
               'patches/fix-locale-{version}.patch',
               'patches/modules-locales-{version}.patch',
               'patches/fix-platform-{version}.patch',

               # APPLY OLD WORKING 2.7.2 PATCHES
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

               # SPECIAL PATCHES
               ('patches/fix-configure-darwin.patch', is_darwin),
               ('patches/fix-distutils-darwin.patch', is_darwin),
               ('patches/fix-ftime-removal.patch', is_api_gt(19)),
               ('patches/disable-openpty.patch', check_all(is_api_lt(21), is_ndk('crystax')))

               ]

    from_crystax = False

    def prebuild_arch(self, arch):
        super(Python2Recipe, self).prebuild_arch(arch)

    def build_arch(self, arch):
        if not exists(join(self.get_build_dir(arch.arch), 'libpython2.7.so')):
            self.do_python_build(arch)

        if not exists(self.ctx.get_python_install_dir()):
            shprint(sh.cp, '-a', join(self.get_build_dir(arch.arch), 'python-install'),
                    self.ctx.get_python_install_dir())

        info('Copying hostpython binary to targetpython folder')
        shprint(sh.cp, self.ctx.hostpython,
                join(self.ctx.get_python_install_dir(), 'bin', 'python.host'))
        self.ctx.hostpython = join(self.ctx.get_python_install_dir(), 'bin', 'python.host')

        if not exists(join(self.ctx.get_libs_dir(arch.arch), 'libpython2.7.so')):
            shprint(sh.cp, join(self.get_build_dir(arch.arch), 'libpython2.7.so'),
                    self.ctx.get_libs_dir(arch.arch))

    def do_python_build(self, arch):
        shprint(sh.cp, self.ctx.hostpython, self.get_build_dir(arch.arch))
        shprint(sh.cp, self.ctx.hostpgen, join(self.get_build_dir(arch.arch), 'Parser'))
        hostpython = join(self.get_build_dir(arch.arch), 'hostpython')

        with current_directory(self.get_build_dir(arch.arch)):
            hostpython_recipe = Recipe.get_recipe('hostpython2', self.ctx)
            shprint(sh.cp, join(hostpython_recipe.get_recipe_dir(), 'Setup'), 'Modules')
            with open('config.site', 'w') as config_site:
                config_site.write('''
    ac_cv_file__dev_ptmx=no
    ac_cv_file__dev_ptc=no
    ac_cv_have_long_long_format=yes
                ''')

            env = arch.get_env()

            env['RFS'] = "{0}/platforms/android-{1}/arch-arm".format(self.ctx.ndk_dir, self.ctx.android_api)
            env['CONFIG_SITE'] = join(self.get_build_dir(arch.arch), 'config.site')
            env['HOSTARCH'] = 'arm-linux-androideabi'
            env['BUILDARCH'] = shprint(sh.gcc, '-dumpmachine').stdout.split('\n')[0]
            env['CFLAGS'] = ' '.join([env['CFLAGS'],
                                      '-g0', '-Os', '-s', '-I{0}/usr/include'.format(env['RFS']),
                                      '-fdata-sections', '-ffunction-sections',
                                      ])
            env['LDFLAGS'] = ' '.join([env['LDFLAGS'],
                                      '-L{0}/usr/lib'.format(env['RFS']), '-L{0}lib'.format(env['RFS'])])
            env['OPENSSL_BUILD'] = '/path-to-openssl'
            env['SQLITE3_INC_DIR'] = '/path-to-sqlite3-includes'
            env['SQLITE3_LIB_DIR'] = '/path-to-sqlite3-library'

            # TODO: need to add a should_build that checks if optional
            # dependencies have changed (possibly in a generic way)
            if 'openssl' in self.ctx.recipe_build_order:
                info("Activate flags for ssl")
                r = Recipe.get_recipe('openssl', self.ctx)
                b = r.get_build_dir(arch.arch)

                i = ' -I' + join(b, 'include') + ' -I' +\
                    join(b, 'include', 'openssl')
                l = ' -L' + b + ' -lcrypto' + r.version +\
                    ' -lssl' + r.version
                f = 'CPPFLAGS'
                env[f] = env[f] + i if f in env else i
                f = 'LDFLAGS'
                env[f] = env[f] + l if f in env else l
                env['OPENSSL_BUILD'] = b
                env['OPENSSL_VERSION'] = r.version

            if 'sqlite3' in self.ctx.recipe_build_order:
                info("Activate flags for sqlite3")
                r = Recipe.get_recipe('sqlite3', self.ctx)

                i = ' -I' + r.get_build_dir(arch.arch)
                l = ' -L' + r.get_lib_dir(arch) + ' -lsqlite3'
                # Insert or append to env
                f = 'CPPFLAGS'
                env[f] = env[f] + i if f in env else i
                f = 'LDFLAGS'
                env[f] = env[f] + l if f in env else l
                env['SQLITE3_INC_DIR'] = r.get_build_dir(arch.arch)
                env['SQLITE3_LIB_DIR'] = r.get_lib_dir(arch)

            if 'libffi' in self.ctx.recipe_build_order:
                info("Activate flags for ffi")
                r = Recipe.get_recipe('libffi', self.ctx)
                i = ' -I' + join(r.get_build_dir(arch.arch),
                                 r.get_host(arch), 'include')
                l = ' -L' + join(r.get_build_dir(arch.arch),
                                 r.get_host(arch), '.libs') + ' -lffi'
                f = 'CPPFLAGS'
                env[f] = env[f] + i if f in env else i
                f = 'LDFLAGS'
                env[f] = env[f] + l if f in env else l
                env['LIBFFI_CFLAGS'] = env['CFLAGS'] + i
                env['LIBFFI_LIBS'] = l

            env['CFLAGS'] = ' '.join([env['CFLAGS'], '-Wformat'])

            configure = sh.Command('./configure')
            # AND: OFLAG isn't actually set, should it be?
            shprint(configure,
                    'CROSS_COMPILE_TARGET=yes',
                    '--host={}'.format(env['HOSTARCH']),
                    '--build={}'.format(env['BUILDARCH']),
                    # 'OPT={}'.format(env['OFLAG']),
                    '--prefix={}'.format(realpath('./python-install')),
                    '--enable-shared',
                    '--with-system-ffi',
                    '--disable-ipv6',
                    # '--disable-toolbox-glue',
                    # '--disable-framework',
                    _env=env
                    )

            print('Make compile ...')
            shprint(sh.make, '-j5',
                    'CROSS_COMPILE_TARGET=yes',
                    'INSTSONAME=libpython2.7.so',
                    _env=env
                    )

            print('Make install ...')
            shprint(sh.make, '-j5', 'install',
                    'CROSS_COMPILE_TARGET=yes',
                    'INSTSONAME=libpython2.7.so',
                    _env=env
                    )

            if is_darwin():
                shprint(sh.cp, join(self.get_recipe_dir(), 'patches', '_scproxy.py'),
                        join('python-install', 'Lib'))
                shprint(sh.cp, join(self.get_recipe_dir(), 'patches', '_scproxy.py'),
                        join('python-install', 'lib', 'python2.7'))

            # REDUCE PYTHON
            for dir_name in ('test', join('json', 'tests'), 'lib-tk',
                             join('sqlite3', 'test'), join('unittest, test'),
                             join('lib2to3', 'tests'), join('bsddb', 'tests'),
                             join('distutils', 'tests'), join('email', 'test'),
                             'curses'):
                shprint(sh.rm, '-rf', join(self.ctx.build_dir, 'python-install',
                                           'lib', 'python2.7', dir_name))


recipe = Python2Recipe()
