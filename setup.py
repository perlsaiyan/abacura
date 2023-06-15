from setuptools import setup, find_packages

setup(
    name="abacura_kallisti",
    description="Abacura extensions for Legends of Kallisti",
    python_requires='>3.10',
    version="0.0.1",
    packages=find_packages(),
    license="Proprietary",
    classifiers=[
        'License :: Other/Proprietary License',
    ],

    include_package_data=True,
    package_data={
        'abacura': ['*.css'],
    },
    install_requires=[
        "textual~=0.27.0",
        ],
)

