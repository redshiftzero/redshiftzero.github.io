---
layout: post
title: "Lucy Parsons Labs and SecureDrop"
date: June 10, 2016 
author: redshiftzero 
keywords: ""
description: ""
---

Motivation
----------

After two years of FOIA battles at Lucy Parsons Labs, we wanted to find
another way to get information about government actions. Enabling
anonymous whistleblowers to drop us documents seemed like another promising
avenue. We also wanted to provide freelance journalists as well as 
journalists without access to a SecureDrop
instance at their newsroom a way to interact with sources anonymously 
through SecureDrop and a way to work with documents we receive through
our instance. Here we will describe at a high level how SecureDrop works. 

SecureDrop in a Nutshell
------------------------

SecureDrop is a anonymous whistleblowing submission systems that is designed to
minimize source information. Documents are stored encrypted on the server and
only the journalists or administrators are able to decrypt them. All
connections come through the Tor Anonymity network such that an adversary
observing the network only sees an individual connecting to Tor.  

# Both journalists and sources connect through Tor in order to minimize metadata. 

{: .post-image}
![SecureDrop Without
Admin](https://redshiftzero.github.io/assets/securedrop/securedrop_simple_without_admin_sm.png)

# Even the administrators login through Tor.  

{: .post-image}
![SecureDrop With
Admin](https://redshiftzero.github.io/assets/securedrop/securedrop_simple_with_admin_sm.png)

# A source can login to SecureDrop's source interface and submit documents.

{: .post-image}
![SecureDrop Leak
1](https://redshiftzero.github.io/assets/securedrop/securedrop_leak1_sm.png)

# The source documents are stored encrypted on the SecureDrop server.

{: .post-image}
![SecureDrop Leak
2](https://redshiftzero.github.io/assets/securedrop/securedrop_leak2_sm.png)

# The journalist downloads the encrypted documents from the SecureDrop server. 

{: .post-image}
![SecureDrop Leak
3](https://redshiftzero.github.io/assets/securedrop/securedrop_leak3_sm.png)

# The journalist transfers, decrypts and views the document on an airgapped machine.

{: .post-image}
![SecureDrop Leak
4](https://redshiftzero.github.io/assets/securedrop/securedrop_leak4_sm.png)

At this point, the journalist can read through the messages and documents and
work with them for publication. They can use the [Metadata Anonymization
Toolkit](https://mat.boum.org/)
on [Tails](https://tails.boum.org) to strip metadata off the documents and transfer them to their regular
workstation. 

Our Instance
------------

The landing page for our SecureDrop instance can be found at
[https://lucyparsonslabs.com/securedrop](https://lucyparsonslabs.com/securedrop).
 

