from pythonforandroid.recipe import TargetHostPythonRecipe


class Hostpython3Recipe(TargetHostPythonRecipe):
    '''
    The hostpython3's recipe.

    .. versionchanged:: 0.6.0
        Refactored into  the new class
        :class:`~pythonforandroid.recipe.TargetHostPythonRecipe`
    '''
    version = '3.7.1'
    name = 'hostpython3'
    conflicts = ['hostpython2', 'hostpython3crystax']


recipe = Hostpython3Recipe()
