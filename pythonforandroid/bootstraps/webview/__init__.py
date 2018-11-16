from pythonforandroid.toolchain import Bootstrap, current_directory, info, info_main, shprint
from pythonforandroid.util import ensure_dir
from os.path import join
import sh


class WebViewBootstrap(Bootstrap):
    name = 'webview'

    recipe_depends = ['genericndkbuild',
                      ('python2', 'python2legacy', 'python3', 'python3crystax')]

    def run_distribute(self):
        info_main('# Creating Android project from build and {} bootstrap'.format(
            self.name))

        shprint(sh.rm, '-rf', self.dist_dir)
        shprint(sh.cp, '-r', self.build_dir, self.dist_dir)
        with current_directory(self.dist_dir):
            with open('local.properties', 'w') as fileh:
                fileh.write('sdk.dir={}'.format(self.ctx.sdk_dir))

        arch = self.ctx.archs[0]
        if len(self.ctx.archs) > 1:
            raise ValueError('built for more than one arch, but bootstrap cannot handle that yet')
        info('Bootstrap running with arch {}'.format(arch))

        with current_directory(self.dist_dir):
            info('Copying python distribution')

            python_bundle_dir = join('_python_bundle', '_python_bundle')
            if 'python2legacy' in self.ctx.recipe_build_order:
                # a special case with its own packaging location
                python_bundle_dir = 'private'
                # And also must had an install directory, make sure of that
                self.ctx.python_recipe.create_python_install(self.dist_dir)

            self.distribute_libs(arch, [self.ctx.get_libs_dir(arch.arch)])
            self.distribute_aars(arch)
            self.distribute_javaclasses(self.ctx.javaclass_dir)

            ensure_dir(python_bundle_dir)
            site_packages_dir = self.ctx.python_recipe.create_python_bundle(
                join(self.dist_dir, python_bundle_dir), arch)

        self.strip_libraries(arch)
        self.fry_eggs(site_packages_dir)
        super(WebViewBootstrap, self).run_distribute()


bootstrap = WebViewBootstrap()
