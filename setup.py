from distutils.core import setup

from catkin_pkg.python_setup import generate_distutils_setup


setup_args = generate_distutils_setup(
    packages=[
        "smart_warehouse_robot",
        "smart_warehouse_robot.common",
        "smart_warehouse_robot.services",
        "smart_warehouse_robot.nodes",
    ],
    package_dir={"": "src"},
)

setup(**setup_args)
