from setuptools import setup, find_packages


setup(
    name='django-modeldiff',
    version='0.2',
    description='Track changes when saving or deleting django model objects',
    long_description=open('README.md').read(),
    author='Manel Clos',
    author_email='tech@microdisseny.com',
    url='git@github.com:Microdisseny/modeldiff',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
