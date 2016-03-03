import os
from setuptools import setup, Command

class cleanup(Command):
    """Get rid of unneeded files after running setup.py."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        os.system("rm -rfv ./build ./dist ./*.pyc ./*.tgz ./*.egg-info")

setup(
    name='c3speakers',
    version='1.0',
    url='https://github.com/keikoro/c3speakers',
    author='K Kollmann',
    author_email='code∆k.kollmann·moe',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License'
    ],
    keywords='Chaos Communicaton Congress, CCC, C3, speakers',
    install_requires=['beautifulsoup4', 'requests', 'twitter'],
    tests_require=['pytest', 'requests'],

    cmdclass = {
        'clean': cleanup
    }
)
