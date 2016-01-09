from setuptools import setup

setup(
    name='c3speakers',
    version='1.0',
    url='https://github.com/keikoro/c3speakers',
    author='K Kollmann',
    author_email='code∆k.kollmann·moe',
    license='MIT',
    keywords='Chaos Communicaton Congress, CCC, C3, speakers',
    install_requires=['beautifulsoup4', 'requests', 'twitter'],
    tests_require=['pytest', 'requests']
)
