---
layout: page
title: Welcome!
tagline: hey hey
---
{% include JB/setup %}

## About me

I'm a scientist, developer and researcher interested in astrophysics,
security/crypto, and data analysis. I'm an avid user of free and open
source software, and I care deeply about privacy
rights and freedom of speech and information. Here are some links to
find out more about me and my projects:

- [Twitter](https://twitter.com/redshiftzero)
- [Github](https://github.com/redshiftzero) - Some of my public codes/slides 
- [Kaggle](https://www.kaggle.com/users/107418/cespanar) - Machine
  learning competitions

List of blog posts:

<ul class="posts">
  {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>

