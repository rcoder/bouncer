import os
import setuptools
import sys

import bouncer

basedir = os.path.dirname(sys.argv[0])

def readfile(name):
  with open(os.path.join(basedir, name), 'rb') as fh:
    return fh.read()

readme = readfile('README')
deps = readfile('requirements.txt')

setuptools.setup(
  author='Lennon Day-Reynolds',
  author_email='lennon@urbanairship.com',
  name='bouncer',
  version=bouncer.VERSION,
  description=bouncer.DESC,
  long_description=readme,
  license='MIT',
  entry_points={'console_scripts':['bouncerd = bouncer:main']},
  packages=['bouncer'],
  include_package_data=True
)
