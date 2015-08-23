"""
SQLAlchemy-JSONAPI
------------------

JSON API Mixin for SQLAlchemy that aims to meet the full JSON API spec as
published at http://jsonapi.org/format.

Full documentation is available at:

https://github.com/coltonprovias/sqlalchemy-jsonapi
"""

from setuptools import setup

setup(name='SQLAlchemy-JSONAPI',
      version='1.0.0',
      url='http://github.com/coltonprovias/sqlalchemy-jsonapi',
      license='MIT',
      author='Colton J. Provias',
      author_email='cj@coltonprovias.com',
      description='JSONAPI Mixin for SQLAlchemy',
      long_description=__doc__,
      packages=['sqlalchemy_jsonapi'],
      zip_safe=False,
      include_package_data=True,
      platforms='any',
      install_requires=['SQLAlchemy', 'inflection'],
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Web Environment',
            'Framework :: Flask',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Topic :: Software Development :: Libraries :: Python Modules'
      ])
