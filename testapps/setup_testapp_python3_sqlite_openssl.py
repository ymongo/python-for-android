
from distutils.core import setup
from setuptools import find_packages

options = {'apk': {'requirements': 'libffi,openssl,sqlite3,requests,peewee,sdl2,pyjnius,kivy,python3',
                   'android-api': 27,
                   'ndk-api': 21,
                   'dist-name': 'bdisttest_python3_sqlite_openssl_googlendk',
                   'ndk-version': '10.3.2',
                   'arch': 'armeabi-v7a',
                   # Todo: Fix permissions, only one of those works, and both
                   # should be enabled (same issue for the equivalent python2 test)
                   # 'permission': 'VIBRATE',
                   'permission': 'INTERNET',
                   }}

package_data = {'': ['*.py',
                     '*.png']
                }

packages = find_packages()
print('packages are', packages)

setup(
    name='testapp_python3_sqlite_openssl_googlendk',
    version='1.1',
    description='p4a setup.py test',
    author='Alexander Taylor',
    author_email='alexanderjohntaylor@gmail.com',
    packages=find_packages(),
    options=options,
    package_data={'testapp_sqlite_openssl': ['*.py', '*.png']}
)
