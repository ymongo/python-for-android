from pythonforandroid.recipe import TargetHostPythonRecipe


class Hostpython2Recipe(TargetHostPythonRecipe):
    '''
    The hostpython2's recipe.

    .. versionchanged:: 0.6.0
        Updated to version 2.7.15 and the build process has been changed in
        favour of the recently added class
        :class:`~pythonforandroid.recipe.TargetHostPythonRecipe`
    '''
    version = '2.7.15'
    name = 'hostpython2'
    conflicts = ['hostpython3', 'hostpython3crystax']


recipe = Hostpython2Recipe()
