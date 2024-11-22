from setuptools import setup, find_packages

setup(
    name="piframe",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'update-frame = piframe.app.update_frame:update_frame',
        ],
    },
    description="Digital Raspberry Pi Zero W e-ink AI picture frame.",
)
