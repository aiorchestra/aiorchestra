Release process
===============

Run tests on target brunch
--------------------------

tox -epep8
tox -epy35


Decleare package version
------------------------

In setup.py bump version to the next::

    version='X.X.X'  to version='X.X.Y'

Cut off stable branch
---------------------

git checkout -b vX.X.X-stable
git push origin vX.X.X-stable


Create GitHub tag
-----------------

Releases ---> Draft New Release

Name: AIOrchestra version X.X.X stable release


Collect changes from previous version
-------------------------------------

    git log --oneline --decorate


Build distribution package
--------------------------

    python setup.py bdist_wheel


Check install capability for the whell
--------------------------------------

    virtualenv .test_venv
    source .test_venv/bin/activate
    pip install dist/aiorchestra-X.X.X-py2.py3-none-any.whl


Submit release to PYPI
----------------------

    python setup.py bdist_wheel register
    python setup.py bdist_wheel upload


Modify plugin dependencies
--------------------------

In each AIOrchestra plugin bump version of aiorchestra lib to a new version.

