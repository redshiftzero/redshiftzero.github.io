+++
date = "2020-12-17"
title = "Getting started in Rust and WebAssembly"
slug = "webassembly"
categories = [ "Post", "Rust" ]
tags = [ "Rust", "WebAssembly" ]
+++

In my last post I described how I implemented the [`signal-protocol`](https://github.com/freedomofpress/signal-protocol) Python library, which provides Python bindings using [Pyo3](https://github.com/PyO3/PyO3) to an upstream maintained Rust cryptography crate implementing the Signal protocol. I created the the [`signal-protocol`](https://github.com/freedomofpress/signal-protocol) library in order to prototype end-to-end encrypted messaging between journalists and their sources through SecureDrop. In the SecureDrop ecosystem, journalists use a Python project, [`securedrop-client`](https://github.com/freedomofpress/securedrop-client), hence the need for the Python bindings, and sources use [Tor Browser](http://torproject.org/).

For the Tor Browser-based client for sources, I needed to either use another implementation of Signal in JavaScript (which does exist), or just write a crate that has the existing upstream cryptography crate as a dependency, and compile it all to WebAssembly. As you can probably tell from the title of this post, [I went with the latter approach](https://github.com/freedomofpress/securedrop-e2e/tree/main/securedrop-source). It's honestly pretty cool that I can use the same Rust crypto logic fairly easily for both endpoints, thanks to Pyo3 and WebAssembly.

In this brief post we'll cover:

* [an intro to WebAssembly]({{< relref "#wat" >}})
* [where `wasm-bindgen` and `wasm-pack` fit in]({{< relref "#wasmbindgen" >}})
* [useful crates you should know of, including `js_sys` and `web_sys`]({{< relref "#useful" >}})
* [helpful references to read more]({{< relref "#refs" >}})

# WebAssembly? {#wat}

WebAssembly is a binary-code format that runs in a stack-based virtual machine. It's supported in all modern browsers, and can also be run in other runtimes (e.g. see [WASI](https://wasi.dev/)) that are browser independent.

Why use WebAssembly? Two of the most common reasons are portability and performance. For computationally intensive tasks that need to run in a Browser, you might rewrite the expensive parts in a language that compiles to WebAssembly, leaving the rest of your JavaScript unmodified (similar to C extensions and Python). In the case of Rust compiled to WebAssembly, we also get to benefit from all the safety guarantees that Rust provides at compile time.

There are two main approaches to combining Rust and WebAssembly:

* writing a mix of JavaScript and Rust. Folks typically use `wasm-bindgen` and `wasm-pack` to make this easy and autogenerate a lot of the helper JavaScript code for your WebAssembly module. We'll cover this below.
* writing only Rust using a project like [Yew](https://github.com/yewstack/yew). Note that you're not sidestepping the use of JavaScript, it's just abstracted away from you so you don't need to write any JavaScript yourself. At the time of writing, using Web APIs (e.g. using `web-sys` to manipulate the DOM) does require JavaScript, although this may not always be the case[^1]. I haven't explored the Yew path myself, so we'll focus on the former path.

# `wasm-bindgen` and `wasm-pack` {#wasmbindgen}

`wasm-bindgen` is a handy tool wherein you can simply add the `#[wasm_bindgen]` attribute to structs and impl blocks to indicate that they should be exposed to JavaScript. For example, `SecureDropSourceSession` below is a Rust struct I wanted to make available as a JavaScript class:

```Rust
#[wasm_bindgen]
pub struct SecureDropSourceSession {
    store: InMemSignalProtocolStore,
    pub registration_id: u32,
}
```

It encapsulates a private member `InMemSignalProtocolStore` that methods in our impl block in Rust will use when performing crypto operations in our WebAssembly module.

Now I can provide methods (to JavaScript) on this struct using an impl block also with the `#[wasm_bindgen]` attribute[^2]:

```Rust
#[wasm_bindgen]
impl SecureDropSourceSession {
    pub fn new() -> Result<SecureDropSourceSession, JsValue> {
        let mut csprng = OsRng;
        let registration_id: u32 = csprng.gen();
        let identity_key = IdentityKeyPair::generate(&mut csprng);

        // This struct will hold our session, identity, prekey and sender key stores.
        InMemSignalProtocolStore::new(identity_key, registration_id)
            .map(|store| SecureDropSourceSession {
                store,
                registration_id,
            })
            .map_err(|e| e.to_string().into())
    }
```

The `Result<T, JsValue>` return type is a common pattern that `wasm-bindgen` will use to throw JavaScript exceptions when the `Err` variant is returned.

Once the WebAssembly module is compiled and loaded, I can now create `SecureDropSourceSession` objects (now that I've implemented `SecureDropSourceSession::new`) from JavaScript:

```JavaScript
var session = SecureDropSourceSession.new();
```

### Building

`wasm-pack` builds your project along with some autogenerated helper JS to a folder called `pkg`. This is useful if you use a bundler like Webpack since you can simply add the path to your WebAssembly package to your dependencies. This is also useful if you want to publish your WebAssembly package to `npm`. By publishing to `npm`, folks using the package will not need the Rust toolchain installed since you'll be publishing the built Wasm artifact.

You can also [go the route of not using a bundler](https://github.com/freedomofpress/securedrop-e2e#development), which you can read about in more detail [here](https://rustwasm.github.io/docs/wasm-bindgen/examples/without-a-bundler.html).

# Useful crates {#useful}

Other useful crates to know of are `js_sys` and `web_sys`:

`js_sys` lets you call JavaScript functions from your Rust code, such as [`escape()`](https://docs.rs/js-sys/0.3.46/js_sys/fn.escape.html).

`web_sys` provides Web APIs (through JavaScript). For example, you can manipulate the DOM or get access to the [WebCrypto API](https://docs.rs/web-sys/0.3.46/web_sys/struct.Window.html#impl-62).

For debugging, there's [`console_error_panic_hook`](https://github.com/rustwasm/console_error_panic_hook), which lets you [add a panic hook](https://github.com/freedomofpress/securedrop-e2e/blob/main/securedrop-source/src/lib.rs#L40) that passes panics through to the JavaScript console:

```rust
panic::set_hook(Box::new(console_error_panic_hook::hook));
```

# Referencecs {#refs}

This post was a very brief overview. There are great tutorials out there on Rust and WebAssembly, and the main references I found useful while learning enough to implement my project are here:

* [Rust and WebAssembly book](https://rustwasm.github.io/docs/book/) - an introduction to using Rust and WebAssembly together wherein you implement the Game of Life in the browser
* [MDN's intro to `wasm-bindgen` and `wasm-pack`](https://developer.mozilla.org/en-US/docs/WebAssembly/Rust_to_wasm)
* [Programming WebAssembly with Rust](https://www.amazon.com/Programming-WebAssembly-Rust-Development-Applications/dp/1680506366) - a short read covering both WebAssembly in the browser as well as WASI (if you want to run WebAssembly independent of web browsers)
* [the `wasm-bindgen` book](https://rustwasm.github.io/docs/wasm-bindgen/) - This is a nice reference text with the details of using `wasm-bindgen`.

Happy hacking!

[^1]: See the [Interface Types explainer](https://github.com/WebAssembly/interface-types/blob/master/proposals/interface-types/Explainer.md).
[^2]: Random number generation is using the [WebCrypto API's getRandomValues() method](https://github.com/rust-random/getrandom/blob/master/src/wasm-bindgen.rs#L93) under the hood via the `rand` and `getrandom` crates.
