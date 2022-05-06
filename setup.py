import setuptools
import os
import stat


with open('README.md', 'r') as f:
    long_description = f.read()


with open('requirements.txt','r') as f:
    requirements = [x.strip() for x in f.readlines()]


def find_executable(path):
    executable = stat.S_IEXEC | stat.S_IXGRP | \
                 stat.S_IXOTH | (not stat.S_ISLNK)

    res = []
    for dp, dn, filenames in os.walk(path):
        if '.git/' in dp:
            continue

        for f in filenames:
            if not (os.stat(os.path.join(dp,f)).st_mode & executable):
                continue

            res += [os.path.join(dp,f)]

    return res


setuptools.setup(
    name='celery-utils',
    version='0.1',
    author='Evgenii Sovetkin',
    author_email='e.sovetkin@fz-juelich.de',
    description='Tools to work with celery tasks and store results in remote storage',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='git@github.com:esovetkin/celery-utils',
    packages=setuptools.find_packages(),
    package_data={'configs': ['Dockerfile']},
    include_package_data=True,
    scripts=find_executable('scripts/'),
    install_requires=requirements)
