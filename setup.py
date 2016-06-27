"""
SQLAlchemy-JSONAPI
------------------

JSON API serializer for SQLAlchemy that aims to meet the full JSON API spec as
published at http://jsonapi.org/format.  Also includes Flask adapter.

Full documentation is available at:

https://sqlalchemy-jsonapi.readthedocs.org/

GitHub at https://github.com/coltonprovias/sqlalchemy-jsonapi
"""

from setuptools import setup
import sys

requirements = ['SQLAlchemy', 'inflection']

if sys.version_info[0] != 3 or sys.version_info[1] < 4:
      requirements.append('enum34')

setup(name='SQLAlchemy-JSONAPI',
      version='4.0.9',
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
      install_requires=requirements,
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
