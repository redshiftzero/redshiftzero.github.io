+++
date = "2020-07-31"
title = "Protecting journalists from malware using QubesOS"
slug = "securedrop-qubes-workstation"
categories = [ "Post", "Software Development"]
tags = [ "SecureDrop", "qubes", "whistleblowing", "whitepaper" ]
+++

Earlier this year at USENIX Enigma, I presented some recent work towards rearchitecting the SecureDrop journalist experience.

In SecureDrop we currently use an airgapped workstation for viewing documents to reduce the impact of malware present in malicious documents. This presents challenges in terms of maintenance, usability, and even security (i.e. airgaps don't receive automatic updates).

The basic idea of the rearchitecture of the journalist experience is to replace SecureDrop's multi-machine airgap with a single machine using Qubes (Xen) for compartmentalization. This enables journalists to work with source materials in a secure environment, while still protecting them in the event of a system compromise. Check out the full talk here:

<iframe width="560" height="315" src="https://www.youtube.com/embed/Z7BkdhO8P2I" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

After the talk, I decided to write up basically the above talk describing the design of the system in an expanded form in a whitepaper. [Check out the full whitepaper here (PDF)](https://securedrop.org/documents/13/SD_Qubes_Workstation_Whitepaper.pdf).
