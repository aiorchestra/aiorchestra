Release process
===============

Run tests on target brunch
--------------------------

Steps::

    tox -epep8
    tox -epy35
    tox -esphinx-docs


Decleare package version
------------------------

In setup.py bump version to the next::

    version='X.X.X'  to version='X.X.Y'

Cut off stable branch
---------------------

Steps::

    git checkout -b vX.X.X-stable
    git push origin vX.X.X-stable


Create GitHub tag
-----------------

Steps::

    Releases ---> Draft New Release
    Name: AIOrchestra version X.X.X stable release


Collect changes from previous version
-------------------------------------

Steps::

    git log --oneline --decorate


Build distribution package
--------------------------

Steps::

    python setup.py bdist_wheel


Check install capability for the whell
--------------------------------------

Steps::

    virtualenv .test_venv
    source .test_venv/bin/activate
    pip install dist/aiorchestra-X.X.X-py2.py3-none-any.whl


Submit release to PYPI
----------------------

Steps::

    python setup.py bdist_wheel register
    python setup.py bdist_wheel upload


Modify plugin dependencies
--------------------------

In each AIOrchestra plugin bump version of aiorchestra lib to a new version.

