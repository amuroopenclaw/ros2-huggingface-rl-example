from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'amr_rl_navigation'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include all launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Include all world files
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
        # Include all URDF files
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
    ],
    install_requires=['setuptools', 'gymnasium', 'stable-baselines3', 'huggingface_hub'],
    zip_safe=True,
    maintainer='Amuro Dev Agent',
    maintainer_email='amuro@openclaw.dev',
    description='ROS 2 package for AMR navigation using Hugging Face Reinforcement Learning',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'test_env = amr_rl_navigation.test_env:main',
            'train_agent = amr_rl_navigation.train_agent:main',
            'evaluate_agent = amr_rl_navigation.evaluate_agent:main',
        ],
    },
)
