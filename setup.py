from setuptools import setup

setup(
    name="abacura",
    description="Multi-session MUD client written in Python with Textual library",
    python_requires='>3.10',
    version="0.0.9",
    packages=["abacura", "abacura.mud", "abacura.plugins.events", "abacura.plugins.aliases", "abacura.plugins", "abacura.plugins.commands", "abacura.mud.options", "abacura.widgets"],
    license="Proprietary",
    classifiers=[
        'License :: Other/Proprietary License',
    ],

    include_package_data=True,
    package_data={
        'abacura': ['*.css'],
    },
    install_requires=[
        "asynctelnet~=0.2.5",
        "click==8.1.3",
        "textual~=0.28.0",
        "tomlkit==0.11.8",
        "serum==5.1.0"
        ],

    entry_points="""
        [console_scripts]
        abacura=abacura.abacura:main
    """,
)

