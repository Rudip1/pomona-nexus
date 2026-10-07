# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Exists only to satisfy ament_cmake_python's ament_python_install_package()
# macro so launch files can `import pomona_navigation.launch_utils.*`. Package
# metadata lives in package.xml; install steps live in CMakeLists.txt.

from setuptools import setup

setup(
    name="pomona_navigation",
    version="0.1.0",
    packages=[
        "pomona_navigation",
        "pomona_navigation.launch_utils",
    ],
    install_requires=["setuptools"],
    zip_safe=True,
)
