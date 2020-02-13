from setuptools import setup


setup(
    name='podctl',
    versioning='dev',
    setup_requires='setupmeta',
    install_requires=['cli2', 'pygments'],
    extras_require=dict(
        test=[
            'freezegun',
            'pytest',
            'pytest-cov',
        ],
    ),
    author='James Pic',
    author_email='jamespic@gmail.com',
    url='https://yourlabs.io/oss/podctl',
    include_package_data=True,
    license='MIT',
    keywords='cli',
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'podctl = podctl.console_script:console_script',
        ],
    },
)
