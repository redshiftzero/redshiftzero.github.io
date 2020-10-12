+++
date = "2020-10-06"
title = "Scanning for onion service availability"
slug = "onion-available"
categories = [ "Post", "Tor"]
tags = [ "onion services", "security" ]
+++

[Secure The News](https://securethe.news/) (STN) is a project by Freedom of the Press Foundation to track and advocate for security and privacy technologies in news organizations. I've been working a bit on expanding the scope of STN from its original goal, HTTPS adoption, to how news sites treat Tor users.

The first expansion is to [scan for onion service availability](https://github.com/freedomofpress/securethenews/pull/262) using the the `Onion-Location` header (or its [presence](https://github.com/freedomofpress/securethenews/pull/270) in a `<meta>` tag in the site's page content). This is used by Tor Browser to alert users to the presence of an onion service.


📈 Leaderboard: https://securethe.news/

📝 Blog announcement: https://freedom.press/news/onions-side-tracking-tor-availability-reader-privacy-major-news-sites/

🐿️ Code: https://github.com/freedomofpress/securethenews
