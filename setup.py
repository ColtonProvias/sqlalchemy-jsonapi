"""
SQLAlchemy-JSONAPI
-------------

JSONAPI Mixin for SQLAlchemy
"""

from setuptools import setup


setup(name='SQLAlchemy-JSONAPI',
      version='0.1',
      uri='http://github.com/coltonprovias/sqlalchemy-jsonapi',
      license='MIT',
      author='Colton J. Provias',
      author_email='cj@coltonprovias.com',
      description='JSONAPI Mixin for SQLAlchemy',
      long_description=__doc__,
      py_modules=['sqlalchemy_jsonapi'],
      zip_safe=False,
      include_package_data=True,
      platforms='any',
      install_requires=['SQLAlchemy'],
      classifiers=['Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                   'Topic :: Software Development :: Libraries :: Python'
                   ' Modules'])
