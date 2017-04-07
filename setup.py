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

# XXX: deryck (2016 April 6) __version__ is defined twice.
# __version__ is defined here and in sqlalchemy_jsonapi.__version__
# but we can't import it since __init__ imports literally everything.
# The constants and serializer files depend on enum34 which has to be
# conditionally installed. Once we stop supporting Python 2.7,
# this version string can also be imported as sqlalchemy_jsonapi.__version__.
__version__ = '4.0.9'

setup(name='SQLAlchemy-JSONAPI',
      version=__version__,
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
