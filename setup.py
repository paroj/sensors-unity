#!/usr/bin/env python3

from distutils.core import setup
from DistUtilsExtra.command import build_i18n, build_extra

DEST="share/sensors-unity/"

class my_build_i18n(build_i18n.build_i18n):
    def run(self):
        build_i18n.build_i18n.run(self)
        
        df = self.distribution.data_files
        
        self.distribution.data_files = [(d.replace("share/locale/", DEST+"locale/"), s) for d, s in df]

setup(
      cmdclass = {"build": build_extra.build_extra,
                  "build_i18n": my_build_i18n},
      name = "sensors-unity",
      version = "16.09",
      description = "A simple sensors GUI for the Unity Desktop",
      author = "Pavel Rojtberg",
      author_email = "pavel@rojtberg.net",
      url = "http://www.rojtberg.net/",
      license = "GNU GPL v3",
      data_files = [("share/applications/", ["sensors-unity.desktop"]),
                    (DEST, ["window.ui", "sensors-gui.py"])
                    (DEST+"/sensors/", ["sensors.py"])])
