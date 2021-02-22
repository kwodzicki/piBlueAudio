#!/usr/bin/env python
import os
from setuptools import setup, find_packages
from distutils.util import convert_path

pkg_name = "piBlueAudio"
pkg_desc = "Bluetooth pairing and audio for Raspbery Pi"
pkg_url  = "https://github.com/kwodzicki/piBlueAudio"

main_ns  = {}
ver_path = convert_path( os.path.join(pkg_name, "version.py") )
with open(ver_path) as ver_file:
  exec(ver_file.read(), main_ns)

setup(
  name                 = pkg_name,
  description          = pkg_desc,
  url                  = pkg_url,
  author               = "Kyle R. Wodzicki",
  author_email         = "krwodzicki@gmail.com",
  version              = main_ns['__version__'],
  packages             = find_packages(),
  install_requires     = [],
  scripts              = ['bin/piBlueAudio'],
  include_package_date = True,
  zip_safe             = False,
)
