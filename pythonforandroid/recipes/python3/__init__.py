from pythonforandroid.recipe import TargetPythonRecipe


class Python3Recipe(TargetPythonRecipe):
    '''
    The python3's recipe.

    .. warning:: The support for libraries is temporary disabled. It will be
        enabled in a near future.

    .. versionchanged:: 0.6.0
        Refactored into class
        :class:`~pythonforandroid.recipe.TargetPythonRecipe`
    '''

    version = '3.7.1'
    url = 'https://www.python.org/ftp/python/{version}/Python-{version}.tgz'
    name = 'python3'

    depends = ['hostpython3']
    conflicts = ['python3crystax', 'python2']

    # This recipe can be built only against API 21+
    MIN_NDK_API = 21

    configure_args = (
        '--host={android_host}',
        '--build={android_build}',
        '--enable-shared',
        '--disable-ipv6',
        'ac_cv_file__dev_ptmx=yes',
        'ac_cv_file__dev_ptc=no',
        '--without-ensurepip',
        'ac_cv_little_endian_double=yes',
        '--prefix={prefix}',
        '--exec-prefix={exec_prefix}')


recipe = Python3Recipe()
