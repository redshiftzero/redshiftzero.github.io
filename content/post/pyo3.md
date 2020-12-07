+++
date = "2020-12-06"
title = "Creating Python extensions in Rust using PyO3"
slug = "pyo3"
categories = [ "Post", "Rust" ]
tags = [ "Rust", "pyo3" ]
+++

This post describes how I approached writing a Python extension in Rust. The post covers:

* [why one would even want to do this 🙃]({{< relref "#why" >}})
* [the approaches for calling Rust code from Python]({{< relref "#approaches" >}})
* [an overview of how to create a Python module in Rust using PyO3]({{< relref "#pyo3" >}})
* [some tricky parts, e.g. inheritance]({{< relref "#tricky" >}})
* [building and distributing wheels]({{< relref "#building" >}})

Let's get started.

# First, why do this at all? {#why}

There are two main reasons:

1. To use Rust libraries that already exist, e.g. cryptography libraries.
2. To do computationally intensive work that will be too slow in Python. Other approaches if this is the main motivation are using a C extension (e.g. as [numpy](https://github.com/numpy/numpy) does) or using projects like Cython or numba.

For my use case, I had the first reason, I wanted to prototype something using a Rust crate that implemented a cryptographic protocol.

# Approaches {#approaches}

There are multiple approaches for calling compiled Rust code from Python, including [`ctypes`](https://docs.python.org/3/library/ctypes.html), `cffi` and `PyO3`. Here we'll cover the two most popular: `cffi` (considered easier to use than `ctypes`) and `PyO3`.

### cffi

You can use `extern` keyword to allow other languages to call Rust functions.

For example this `add` function is marked as a public external function using the `pub extern` keywords. The [`#[no_mangle]` attribute](https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html#calling-rust-functions-from-other-languages) just tells the compiler to preserve the readable function name.

```rust
#[no_mangle]
pub extern fn add(n: i32, m: i32) -> i32 {
    n + m
}
```

One you compile the above, one can then use Python's [`cffi`](https://cffi.readthedocs.io/en/latest/) library to call the `add` function. First one must build the library using the [`cdylib` crate type](https://doc.rust-lang.org/reference/linkage.html) to produce a dynamic library.

Then, one can load this dynamic library and call the external Rust functions:

```py
ffi = cffi.FFI()
ffi.cdef("""
    int add(int, int);
""")
adder = ffi.dlopen(location)

assert adder.add(2, 2) == 4
```

You can see this example in full on GitHub [here](https://github.com/redshiftzero/rust-python-examples#cffi). Read more about Rust FFI [here](https://doc.rust-lang.org/nomicon/ffi.html) and if you do take the FFI path, you might want to check out the [milksnake](https://github.com/getsentry/milksnake) project for building and distributing wheels.

### PyO3

PyO3 is a very cool project that allows one to define a Python module entirely in Rust. The above example in PyO3 would be:

```rust
#[pyfunction]
pub fn add(n: i32, m: i32) -> i32 {
    n + m
}
```

And to define the actual Python module:

```rust
#[pymodule]
pub fn adder(py: Python, module: &PyModule) -> PyResult<()> {
    module.add_wrapped(wrap_pyfunction!(add))?;
    Ok(())
}
```

This means that now from the Python interpreter we can just do:

```py
>>> import adder
>>> adder.add(2, 3)
5
```

As we can see, the PyO3 approach is very straightforward. You simply add attributes to structs and functions in Rust to indicate that they should be exposed to Python, and then you write a Rust function to indicate what the top-level functions and classes are for that module.

There are also similarly easy-to-use build tools (via `setuptools-rust` and `maturin`) to handle the packaging and build process. You can see this example packaged using `setuptools-rust` on GitHub [here](https://github.com/redshiftzero/rust-python-examples#pyo3_basic).

In the rest of this post, I'll explain more about using PyO3.

## Creating Python Modules with PyO3 {#pyo3}

The most important attributes to know are:

* `#[pyclass]`: to expose a Rust struct as a Python class
* `#[pyfunction]`: to expose a Rust function as a Python function
* `#[pymethods]`: to expose the methods defined in an `impl` block of a struct with the `#[pyclass]` attribute as methods on the corresponding Python class
* `#[pymodule]`: to expose a collection of structs or functions as a Python module

Using these attributes, PyO3 macros will do all the FFI work for you.

Functions and methods exposed to Python must have return values that are either native Rust types (that can be converted to `PyObject` via the [`ToPyObject` trait](https://docs.rs/pyo3/0.12.4/pyo3/conversion/trait.ToPyObject.html)) or Python object types (e.g. `PyDict` not `dict`). See the list of conversions [here](https://pyo3.rs/master/conversions/tables.html#mapping-of-rust-types-to-python-types).

Functions that can fail should return `PyResult`, which is a type alias for `Result<T, PyErr>`. If the Err variant is returned, an exception will be raised on the Python side. Note that you can also create [custom exception types](https://pyo3.rs/master/exception.html).

### Classes and methods

Let's create an example class, using `#[pyclass]` and `#[pymethods]`:

```rust
#[pyclass]
pub struct Animal {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    age: u8,
    hours_since_last_fed: u8,
}

#[pymethods]
impl Animal {
    #[new]
    fn new(name: String, age: u8, hours_since_last_fed: u8) -> Self {
        Animal{ name, age, hours_since_last_fed }
    }

    fn feed(&mut self) {
        self.hours_since_last_fed = 0;
    }
}
```

The `#[new]` attribute is used for your object constructor and initialization logic in Python (equivalent of Python `__new__()`).

In Python, you'd call `doris = Animal('Doris', 2, 0)` to use this.

The `#[pyo3(get)]` attribute lets one read `doris.name` as member attributes. If you want to set attributes also, you can use `#[pyo3(get, set)]` (which could replace the `Animal::feed()` method if we wanted to).

We can add this class to a new module as follows:

```rust
#[pymodule]
pub fn adder(py: Python, module: &PyModule) -> PyResult<()> {
    module.add_class::<Animal>()?;
    Ok(())
}
```

## Some trickier parts of PyO3 {#tricky}

The above parts can cover simple projects. Two more advanced topics we'll cover are inheritance, and magic methods.

### Inheritance

What if we want to make a subclasses, say, a `Lion`, that inherits from `Animal`? Here's how we do it:

```rust
#[pyclass(subclass)]
pub struct Animal {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    age: u8,
    hours_since_last_fed: u8,
}

#[pymethods]
impl Animal {
    #[new]
    fn new(name: String, age: u8, hours_since_last_fed: u8) -> Self {
        Animal{ name, age, hours_since_last_fed }
    }

    fn feed(&mut self) {
        self.hours_since_last_fed = 0;
    }
}

#[pyclass(extends=Animal)]
pub struct Lion {
    #[pyo3(get)]
    favorite_meat: String,
}

#[pymethods]
impl Lion {
    #[new]
    fn new(name: String, age: u8, hours_since_last_fed: u8, favorite_meat: String) -> PyResult<(Self, Animal)> {
        Ok((Lion{ favorite_meat }, Animal{ name, age, hours_since_last_fed }))
    }

    fn roar(&self) -> String {
        "ROAR!!!!".to_string()
    }
}
```

The `#[pyclass]` annotations indicate the parent (`#[pyclass(subclass)]`) and child (`#[pyclass(extends=Parent)]`) classes. The tuple syntax in the return value of the child is a little "trick" intended for ergonomics: you return `PyResult<(Child, Parent)>` or `(Child, Parent)`. PyO3 will then run `Into<PyClassInitializer>` on the child, where [PyClassInitializer](https://docs.rs/pyo3/0.12.4/pyo3/pyclass_init/struct.PyClassInitializer.html) is PyO3's pyclass initializer.

### Magic methods

One might be surprised to find that implementing magic methods doesn't work in a `#[pymethods]` impl block. It turns out that you can implement Python "magic" methods like `__repr__` and `__richcmp__` using the `PyObjectProtocol` trait and the `#[pyproto]` attribute in a separate `impl` block. For example, to add a nice string representation for `Animal`:

```rust
#[pyproto]
impl PyObjectProtocol for Animal {
    fn __str__(&self) -> PyResult<String> {
        Ok(String::from(format!(
            "Animal: {}",
            self.name,
        )))
    }
}
```

See some additional examples [here](https://github.com/freedomofpress/signal-protocol/blob/0c9c5d76e1876fa2be311430943ca8a3e3ae1f19/src/fingerprint.rs#L52-L61) and [here](https://github.com/freedomofpress/signal-protocol/blob/0c9c5d76e1876fa2be311430943ca8a3e3ae1f19/src/curve.rs#L124-L133).

## Distributing wheels {#building}

We want to build and distribute wheels that do not require the rust toolchain to be installed on target systems. Fortunately, with `setuptools-rust` and `maturin`, that's pretty simple. For `setuptools-rust` our `setup.py` for the `zoo` example would be:

```py
import sys
from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name="zoo",
    version="0.0.1",
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Rust",
    ],
    packages=["zoo"],
    rust_extensions=[RustExtension("zoo.zoo", "Cargo.toml", binding=Binding.PyO3)],
    setup_requires=["setuptools-rust>=0.10.1", "wheel"],
    zip_safe=False,  # Rust extensions are not zip safe
)
```

See the full project [here](https://github.com/redshiftzero/rust-python-examples#pyo3_inherit).

Locally, if we're on macOS, to build macOS wheels:

```
python3 setup.py sdist bdist_wheel
```

To build manylinux wheels we can follow [the procedure described in the setuptools-rust project](https://github.com/PyO3/setuptools-rust#binary-wheels-on-linux). First we fetch the Python Packaging Authority manylinux image:

```
docker pull quay.io/pypa/manylinux2014_x86_64
```

Then using the default `build-wheels.sh` script provided by `setuptools-rust`:

```
docker run --rm -v `pwd`:/io quay.io/pypa/manylinux2014_x86_64 /io/build-wheels.sh
```

This leaves us with built wheels in `dist/` ready for upload to PyPI. And we should just upload the manylinux wheels built by the script as PyPI does not support wheels with platform tags like `linux_x86_64` (these are also produced by the above wheel build command but can be discarded).

# Fin

I hope you're convinced that writing Rust extensions with PyO3 is approachable. To read more check out the [PyO3 guide](https://pyo3.rs/). If you want to see a larger example, you can check out the library I wrote using PyO3 [here](https://github.com/freedomofpress/signal-protocol) and install in Python 3.7+, via `pip install signal-protocol` 😊 .
