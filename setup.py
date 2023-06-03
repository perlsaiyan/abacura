from setuptools import setup

setup(
    name="abacura",
    description="Multi-session MUD client written in Python with Textual library",
    version="0.0.1",
    packages=["abacura", "abacura.mud"],
    license="Proprietary",
    classifiers=[
        'License :: Other/Proprietary License',
    ],
    include_package_data=True,
    install_requires=["textual~=0.27.0","asynctelnet~=0.2.5"],
    entry_points="""
        [console_scripts]
        abacura=abacura.abacura:main
    """,
)

