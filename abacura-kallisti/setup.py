from setuptools import setup, find_packages

setup(
    name="abacura_kallisti",
    description="Abacura extensions for Legends of Kallisti",
    python_requires='>3.10',
    version="0.0.8",
    packages=find_packages(),
    license="Proprietary",
    classifiers=[
        'License :: Other/Proprietary License',
    ],

    include_package_data=True,
    package_data={
        'abacura_kallisti': ['css/*.css'],
    },
    install_requires=[
        "abacura~=0.0.15",
        "pillow",
        ],
)

