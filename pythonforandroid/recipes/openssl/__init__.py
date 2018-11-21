import time
from os.path import join
from functools import partial

from pythonforandroid.toolchain import Recipe, shprint, current_directory
import sh


class OpenSSLRecipe(Recipe):
    '''
    The OpenSSL libraries for python-for-android. This recipe will generate the
    following libraries as shared libraries (*.so):

        - crypto
        - ssl

    The generated openssl libraries are versioned, where the version is the
    recipe attribute :attr:`version` e.g.: ``libcrypto1.1.so``,
    ``libssl1.1.so``...so...to link your recipe with the openssl libs,
    remember to add the version at the end, e.g.:
    ``-lcrypto1.1 -lssl1.1``. Or better, you could do it dynamically
    using the methods: :meth:`include_flags` and :meth:`link_flags`.

    .. warning:: This recipe is very sensitive because is used for our core
        recipes, the python recipes. The used API should match with the one
        used in our python build, otherwise we will be unable to build the
        _ssl.so python module.

    .. versionchanged:: 0.6.0

        - The gcc compiler has been deprecated in favour of clang and libraries
          updated to version 1.1.1 (LTS - supported until 11th September 2023)
        - Added two new methods to make easier to link with openssl:
          :meth:`include_flags` and :meth:`link_flags`
        - subclassed versioned_url
        - Adapted method :meth:`select_build_arch` to API 21+

    '''

    version = '1.1'
    '''the major minor version used to link our recipes'''

    url_version = '1.1.1'
    '''the version used to download our libraries'''

    url = 'https://www.openssl.org/source/openssl-{url_version}.tar.gz'

    @property
    def versioned_url(self):
        if self.url is None:
            return None
        return self.url.format(url_version=self.url_version)

    def include_flags(self, arch):
        '''Returns a string with the include folders'''
        openssl_includes = join(self.get_build_dir(arch.arch), 'include')
        return ' -I' + openssl_includes + \
               ' -I' + join(openssl_includes, 'internal') + \
               ' -I' + join(openssl_includes, 'openssl')

    def link_flags(self, arch):
        '''Returns a string with the right link flags to compile against the
        openssl libraries'''
        build_dir = self.get_build_dir(arch.arch)
        return ' -L' + build_dir + \
               ' -lcrypto{version} -lssl{version}'.format(version=self.version)

    def should_build(self, arch):
        return not self.has_libs(arch, 'libssl' + self.version + '.so',
                                 'libcrypto' + self.version + '.so')

    def check_symbol(self, env, sofile, symbol):
        nm = env.get('NM', 'nm')
        syms = sh.sh('-c', "{} -gp {} | cut -d' ' -f3".format(
                nm, sofile), _env=env).splitlines()
        if symbol in syms:
            return True
        print('{} missing symbol {}; rebuilding'.format(sofile, symbol))
        return False

    def get_recipe_env(self, arch=None, with_flags_in_cc=True, clang=True):
        env = super(OpenSSLRecipe, self).get_recipe_env(
            arch, with_flags_in_cc=True, clang=True)
        env['OPENSSL_VERSION'] = self.version
        env['MAKE'] = 'make'  # This removes the '-j5', which isn't safe
        env['ANDROID_NDK'] = self.ctx.ndk_dir
        return env

    def select_build_arch(self, arch):
        aname = arch.arch
        if 'arm64' in aname:
            return 'linux-aarch64'
        if 'v7a' in aname:
            return 'android-arm'
        if 'arm' in aname:
            return 'android'
        if 'x86' in aname:
            return 'android-x86'
        return 'linux-armv4'

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            # sh fails with code 255 trying to execute ./Configure
            # so instead we manually run perl passing in Configure
            perl = sh.Command('perl')
            buildarch = self.select_build_arch(arch)
            shprint(perl, 'Configure', 'shared', 'no-dso', 'no-asm', buildarch,
                    '-D__ANDROID_API__={}'.format(self.ctx.ndk_api),
                    _env=env)
            self.apply_patch('disable-sover.patch', arch.arch)

            check_crypto = partial(self.check_symbol, env, 'libcrypto' + self.version + '.so')
            while True:
                shprint(sh.make, 'build_libs', _env=env)
                if all(map(check_crypto, ('MD5_Transform', 'MD4_Init'))):
                    break
                time.sleep(3)
                shprint(sh.make, 'clean', _env=env)

            self.install_libs(arch, 'libssl' + self.version + '.so',
                              'libcrypto' + self.version + '.so')


recipe = OpenSSLRecipe()
