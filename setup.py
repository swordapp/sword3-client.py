from setuptools import setup, find_packages

setup(
    name="sword3client",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'sword3common',
    ],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="http://cottagelabs.com/",
    author="Cottage Labs",
    author_email="richard@cottagelabs.com",
    description="SWORDv3 Client Library",
    license="Apache2",
    classifiers=[],
    extras_require={
        'docs': ['Sphinx', 'sphinx-autodoc-annotation'],
        'test': ['nose'],
    },
)
