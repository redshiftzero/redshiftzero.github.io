+++
date = "2020-07-31"
title = "Using HTTPS Everywhere rules for SecureDrop onion names"
slug = "securedrop-httpse"
categories = [ "Post" ]
tags = [ "SecureDrop", "tor", "naming" ]
+++

A fun small project I worked on earlier this year was creating an HTTPS Everywhere custom ruleset channel for the SecureDrop project. HTTPS Everywhere is a popular browser extension maintained by EFF that rewrites HTTP URLs to HTTPS when possible. A set of rules is used to determine how URLs should be rewritten. HTTPS Everywhere is included in Tor Browser to reduce the impact of malicious exit nodes.

This is relevant for SecureDrop, because each news organization advertises an onion URL that corresponds to the web application ("source interface") where a source should upload documents. These URLs are not human readable: an example URL v2 onion services is `yyhws9optuwiwsns.onion`. With v3 onion services, they are even longer: `l5satjgud6gucryazcyvyvhuxhr74u6ygigiuyixe3a6ysis67ororad.onion`.

The HTTPS Everywhere folks [suggested](https://github.com/freedomofpress/securedrop/issues/3668) that we could use the [custom ruleset functionality](https://github.com/EFForg/https-everywhere/blob/master/docs/en_US/ruleset-update-channels.md) in HTTPS Everywhere to create a list of rules rewriting human-readable names to the onion URLs for SecureDrop source interface. This can be scoped to a namespace such that this custom ruleset can only rewrite URLs that end in e.g. `securedrop.tor.onion`.

Here's a little gif showing the rewriting:

![ayy Leak docs to LPL](/img/onion_redirect.gif)

We created a ruleset channel with organizations that opted-in, allowing them to rewrite e.g. `lucyparsonslabs.securedrop.tor.onion` to the underlying onion URL. Check [the repository](https://github.com/freedomofpress/securedrop-https-everywhere-ruleset) out if you're curious to see the logic we use to maintain and update the rules. Our ruleset channel was included in stable Tor Browser beginning with [the 9.5 release](https://blog.torproject.org/new-release-tor-browser-95).
