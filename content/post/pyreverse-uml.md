+++
date = "2019-11-25"
title = "Using pyreverse to generate UML class diagrams"
slug = "pyreverse-uml"
categories = [ "Post", "Software Development"]
tags = [ "UML", "object oriented", "python" ]
+++

Recently I wanted to generate UML (Unified Modeling Language) diagrams of the structure of an existing codebase for the purpose of having an architecture discussion.

I was wondering if there was a tool to generate UML diagrams in Python to save me some manual work.

Enter [`pyreverse`](https://pypi.org/project/pyreverse/): it comes installed with `pylint` which is a very common development dependency in Python. `pyreverse` enables you to point to the code you want UML diagrams of, here in my example I was generating a diagram of a project called [`securedrop-export`](https://github.com/freedomofpress/securedrop-export):

```bash
pyreverse securedrop_export/
```

This produces in the same directory a graphviz file called `classes.dot`.

Then, provided you have graphviz (which provides the `dot` command) installed:

```bash
dot -Tpng classes.dot -o securedrop_export.png
```

Which produces the following:

![securedrop-export](/img/securedrop_export.png)

Here `ExportStatus` is an `Enum` and `TimeoutException` is a custom exception (in red).
