+++
date = "2020-08-01"
title = "Tracking which wheels can be reproducibly built"
slug = "reproducible-wheels"
categories = [ "Post" ]
tags = [ "Python", "wheels", "reproducible builds" ]
+++

Being able to [reproducibly build](https://reproducible-builds.org/) binary artifacts means that users, developers, and others can agree that the shipped artifact was correctly built from the source code (that one can inspect), and no intentional or unintentional malicious code was introduced during the build process.

One hiccup we've encountered in SecureDrop development is that not all Python wheels can be built reproducibly. We ship multiple (Python) projects in debian packages, with Python dependencies included in those packages as wheels. In order for our debian packages to be reproducible, we need that wheel build process to also be reproducible. That wheel process _is_ reproducible (as of [pip wheel 0.27.0](https://wheel.readthedocs.io/en/latest/news.html) - see [relevant issue](https://github.com/pypa/wheel/issues/143)) if you set `SOURCE_DATE_EPOCH` to be a constant value. However, there are still [sources](https://github.com/pypa/wheel/issues/248) of [nondeterminism](https://github.com/pypa/pip/issues/6505) for some projects.

For our purposes, this has resulted in our building the wheels (once), saving those wheels on a pip mirror, and then using those wheels at debian package build time. A few times, we've asked "wait, which wheels can't be reproducibly built again?". So I made a little tracker on [https://reproduciblewheels.com/](https://reproduciblewheels.com/) for convenience.

If you find issues or think it should be tracking something different, just [open an issue](https://github.com/redshiftzero/reproduciblewheels).

[![reproduciblewheels](/img/reproduciblewheels.png)](https://reproduciblewheels.com)
