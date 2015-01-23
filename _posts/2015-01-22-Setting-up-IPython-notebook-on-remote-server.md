---
layout: post
category : python 
tagline: "Setting up IPython notebook on a remote server"
tags : [python]
---
{% include JB/setup %}

If you do data analysis in Python and you aren't using IPython notebooks,
 you really should be. Using notebooks allows for easier collaboration as 
well as the fact it's a much more convienient way to store notes, code, and plots 
associated with a given dataset. If using a cloud-based workflow 
like I do, 
you might want to setup an IPython notebook server: this enables you to work
on your notebook on your from your local browser. Here I'll describe how to 
go from a setup that opens a browser (running on the server) when you 
type `ipython notebook` to 
one that will enable you to safely use a browser on your local machine (your laptop). 
Everything here was done on Debian Linux, but it should work similarly on 
other platforms. 

Create a new profile
--------------------

First start IPython, and create a profile that you are going to use for your notebook server: 

    In [1]: !ipython profile create default
    [ProfileCreate] Generating default config file: u'/home/exampleuser/.config/ipython/profile_default/ipython_config.py'
    [ProfileCreate] Generating default config file: u'/home/exampleuser/.config/ipython/profile_default/ipython_notebook_config.py'

Very important note: You're setting up an application that is going to allow 
whoever has access to remotely execute arbitary code. Be certain that you do the next
two steps - setting up a strong password, and enabling SSL/TLS - before you 
start the server.

Set a password
--------------

Start IPython and generate the hash of the password you'd like to use:

    In [1]: from IPython.lib import passwd

    In [2]: passwd()
    Enter password: 
    Verify password: 
    Out[2]: 'sha1:879e46b9cfec:13307bf7f989dd64151302b806f5c9f977966b9d'

Now add the following line to `/home/exampleuser/.config/ipython/profile_def     ault/ipython_notebook_config.py` under `c=get_config()`:

    c.NotebookApp.password = u'sha1:879e46b9cfec:13307bf7f989dd64151302b806f5c9f977966b9d'

Enable HTTPS
------------

Now you'll want to generate an SSL/TLS certificate that you will use
to encrypt the connection between you and the remote server:

    $ openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout nbcert.key -out nbcert.crt
    Generating a 4096 bit RSA private key
    ....................................................++
    ................................................................................................................................................................................................++
    writing new private key to 'nbcert.key'
    -----
    You are about to be asked to enter information that will be incorporated
    into your certificate request.
    What you are about to enter is what is called a Distinguished Name or a DN.
    There are quite a few fields but you can leave some blank
    For some fields there will be a default value,
    If you enter '.', the field will be left blank.
    -----
    Country Name (2 letter code) []:US
    State or Province Name (full name) [Some-State]:RealstateUSA
    Locality Name (eg, city) []:RealcityUSA
    Organization Name (eg, company) []:Example LLC
    Organizational Unit Name (eg, section) []:
    Common Name (e.g. server FQDN or YOUR name) []:example
    Email Address []:example@example.com

Then add the locations of the cert and keyfile to `/home/exampleuser/.config/ipython/profile_def     ault/ipython_notebook_config.py`:

    c.NotebookApp.certfile = u'/home/exampleuser/.config/ipython/profile_default/nbcert.crt'
    c.NotebookApp.keyfile = u'/home/exampleuser/.config/ipython/profile_default/nbcert.key'

There's room for a little more
------------------------------

A few other things that you'll want to setup for this profile (By adding to `/home/exampleuser/.config/ipython/profile_default/ipython_notebook_config.py`):

    c.IPKernelApp.pylab = 'inline'  # Have plots appear in the notebook 
    c.NotebookApp.open_browser = False  # Don't automatically start browser 
    c.NotebookApp.port = 9998  # Port that you'll connect to
    c.NotebookApp.ip = '*'  # Set IPs you allow to connect, * if all
 
It is time
----------

Now you can start your new shiny notebook server with `ipython notebook --profile=default`.
Leave this application running on your remote machine (e.g. with [tmux](http://tmux.sourceforge.net)) 
and in a browser on your laptop type the URL: `https://<my_server_ip>:9998` and login! You can go ahead and start coding. 
