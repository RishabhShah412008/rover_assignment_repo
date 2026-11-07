from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'rover_nav'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share/', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rishbish',
    maintainer_email='rishbish@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': ['drive_node = rover_nav.drive_node:main',
                            'odom_node = rover_nav.odom_node:main',
                            'navigator_node = rover_nav.navigator_node:main',
                            'mission_client = rover_nav.mission_client:main'
        ],
    },
)
