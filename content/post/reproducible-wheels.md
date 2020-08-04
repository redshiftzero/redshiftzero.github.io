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

## How it works

I first selected the 100 most popular packages on PyPI in the past year plus any dependencies that are on FPF's [pip mirror](https://pypi.securedrop.org/simple/)[^1].

Then, I have a little [function](https://github.com/redshiftzero/reproduciblewheels/blob/main/check.py#L112-L161) that builds the wheel twice and then compares the SHA256 hash to determine if they are the same. The build command is:

```bash
python3 -m pip wheel <project_name> --no-binary :all: --no-cache-dir
```

Here `--no-binary :all:` is used to ensure that I download the source tarball and `--no-cache-dir` is used so that I don't inadvertently use a cached built artifact.

A [friendly bot](https://github.com/redshiftzero-bot) is running the above build function nightly for every monitored project, saving the results as [JSON](https://github.com/redshiftzero/reproduciblewheels/blob/main/site_data.json), and then [updating the static HTML](https://github.com/redshiftzero/reproduciblewheels/blob/main/check.py#L87-L109), which is deployed when it's committed to the `main` branch via GitHub pages. That's it!

If you find issues or think it should be tracking something else, just [open an issue](https://github.com/redshiftzero/reproduciblewheels).

[^1]: I should note here that from this set I excluded [a few (7)](https://github.com/redshiftzero/reproduciblewheels/blob/main/check.py#L31) projects that either required additional build requirements that I didn't have out of the box in the build environment or had some other build-time issue (for the interested, this is ticket [#2](https://github.com/redshiftzero/reproduciblewheels/issues/2) on the bugtracker).

[![reproduciblewheels](/img/reproduciblewheels.png)](https://reproduciblewheels.com)
