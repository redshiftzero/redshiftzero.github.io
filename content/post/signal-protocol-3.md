+++
date = "2020-10-22"
title = "Investigating the Signal Protocol, Part 3: Web applications"
slug = "signal-webapps"
categories = [ "Post", "Signal"]
tags = [ "Signal", "security", "protocol" ]
+++

Next in the series, I investigate current messaging applications that both provide web applications and are using the Signal Protocol (or a protocol very similar or derived from Signal), here specifically Wire and Whatsapp. I'm not looking into the voice and video aspects, just the messaging and file sharing capabilities as I'm investigating to see how a similar approach could be used for SecureDrop, where voice/video isn't an option. As always, if you have thoughts on this or notice errors, feel free to drop me a note on [Twitter](https://twitter.com/redshiftzero) or by [email](mailto:jen@redshiftzero.com).

# End-to-end over the web

A [lot](https://www.nccgroup.com/us/about-us/newsroom-and-events/blog/2011/august/javascript-cryptography-considered-harmful/) [has been](https://community.signalusers.org/t/web-app-for-signal/1272/) [written](https://www.zfnd.org/blog/so-you-want-an-e2e-encrypted-webapp/) already on the significant challenges using a web browser for e2e crypto.

The main issue is that when you use an e2e webapp, the webserver you're connected to is serving the cryptographic code to you. This means a malicious server can tamper with any of the code served to you and can, for example, display "verified fingerprints" in the webapp while an active man-in-the-middle is taking place.

Compare this with developer-signed desktop applications, where you can ensure that code from the developer you trust is what is running. In the desktop application case, if the server you're connected to is malicious they can't replace the code running on your desktop.

But for e2e webapps, you're trusting the server - and the integrity of the data flow between your browser and the server.

Another challenge is you need to decide where to store the key material. One could put it in browser storage, but what happens if a user changes browsers? Do you generate new keys each time a user uses a new browser? Or do you put the key material somewhere else on the user's machine? At least for Wire, they do generate new keys when you use a new browser, which we'll see more below.

# Wire

*The below information is from reading the [Wire Whitepaper](https://wire-docs.wire.com/download/Wire+Security+Whitepaper.pdf).*

Wire has apps for mobile (Android, iOS), desktop (macOS, Windows, Linux), as well as an end-to-end encrypted web application.

### User and client registration

First, users must have a Wire account to use the service. User registration can be done via:

* email, where the user must validate a random verification code sent via email (to prove ownership of the account); these must be verified in three attempts,
* phone, where the user must validate a verification code sent via SMS, this code must also be verified in three attempts,

User registration gets the user their Wire internal ID (UUID v4) and an authentication cookie (used to authenticate to the Wire API).

Next, users can register clients in order to start sending/receiving e2e messages. Wire allows a single temporary client and up to 7 permanent devices. During client registration, the client generates a Curve25519 long-term identity keypair and sends:

* what type it is (either Permanent or Temporary),
* the public Curve25519 identity key
* 65,535 one-time use Curve25519 prekeys (see Blog post 1 on X3DH for how that works), which clients periodically replenish, and
* the "last resort" (lr) prekey, which is similar to the signed prekey in X3DH, in that it's used if all other prekeys are exhausted. The Wire whitepaper makes no mention of signing this prekey though.

### Encryption

The primitives Wire uses are ChaCha20, HMAC-SHA256, and Curve25519, with HKDF for key derivation.

Senders encrypt a message to all members of a group ("conversation" in Wire) for every participant and send in a batch to the server. If the sender did not include messages for all participants, the server rejects the batch. Clients keep track of which participants are in a conversation, and learn from the server when they need to update. This is more similiar to how Sesame works in Signal, compared to Signal groups v1, as the server is keeping track of group participants, which clients update to.

For large file attachments, senders generate a symmetric key and encrypt the file using AES-CBC-256 with PKCS#5 padding. The key and SHA-256 of the ciphertext are then encrypted for each participant. The servers gets just one copy of the encrypted file and a message as usual for each participant. This means that clients do not need to upload the same potentially large file many times encrypted to different participants. According to the whitepaper, these assets are stored basically indefinitely (as opposed to when all clients have downloaded the attachment).

### Fingerprint Verification

Users can compare fingerprints, and if all clients in a conversation are verified, this in indicated in the UI with a blue shield.

### Web Client

New "devices" (i.e. new browsers) generate new device keys, the private key material of which is stored using [IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API). Messages are also stored only locally once fetched from the server, which is why conversation history does not appear when you sign in using a new device.

The use of IndexedDB is why Wire does not work in Tor Browser - IndexedDB does not work in PBM (Private Browsing Mode) ([Tor ticket](https://gitlab.torproject.org/tpo/applications/tor-browser/-/issues/26463), [Firefox ticket 1](https://bugzilla.mozilla.org/show_bug.cgi?id=781982)). This makes sense since IndexedDB adheres to a same-origin policy and as such stores data associated with the origin, so allowing this storage in PBM would present privacy issues. However, there are some [proposals](https://bugzilla.mozilla.org/show_bug.cgi?id=1562669) on the Mozilla side to resolve this and thus enable IndexedDB storage in PBM, so this is an area to monitor.

# WhatsApp

*The below information is from reading the [WhatsApp Security Whitepaper](https://scontent.whatsapp.net/v/t39.8562-34/89275998_627986927772871_4167828889579552768_n.pdf?_nc_sid=2fbf2a&_nc_ohc=CZmsR-aJVosAX8yXnbf&_nc_ht=scontent.whatsapp.net&oh=c06ea21064d8cab63370372bdd20296b&oe=5F9C2FD1).*

WhatsApp provides clients for mobile (Android, iOS), desktop (macOS, Windows), as well as a web client via WhatsApp Web. I couldn't really find too much detail about how the web client was approached from a security standpoint, but the below information should apply to all clients.

### User and client registration

During client registration, the process works as one would expect from reading the [X3DH specification](https://signal.org/docs/specifications/x3dh/): clients generate a long-term identity key, a signed prekey, and one-time pre-keys. The client then sends the public parts of all the above keys along with the signature of (signed) prekey to the WhatsApp server.

Clients authenticate to servers using their long-term keypair, so there are no user credentials on the server to compromise.

### Encryption

To establish sessions, the initiator computes a shared key ($SK$ in the [X3DH specification](https://signal.org/docs/specifications/x3dh/)), which the receiver also constructs on receipt of the initiating message. They both use HKDF to derive an initial root key and chain key to initialize session state. From that point clients can encrypt and decrypt messages by deriving each individual message key from chain keys, ratcheting chain keys forward, and updating root keys using updated shared secrets. This is all performed as described in the [double ratchet specification](https://signal.org/docs/specifications/doubleratchet).

For large attachments, WhatsApp has a similar blob store as Wire. They have senders generate an ephemeral 32-byte AES encryption key (for AES-CBC with random IV) and an ephemeral 32-byte MAC key (for HMAC-SHA256). They encrypt-then-MAC and upload the attachment. The message to the recipient then just contains the AES key, the IV, the MAC key, a SHA256 hash, and a reference to the location in the blob store. Recipients must download, decrypt, and verify the hash and MAC prior to decryption. As above, this prevents clients from having to encrypt and send the same large file to multiple participants.

In terms of groups, WhatsApp uses a method that requires servers have knowledge of group participants. This is because Whatsapp uses a "server-side fan out", wherein a message to N clients is just sent once by the client, then forwarded on to the N clients by the server. The disadvantage here is that the server must know which N participants should receive the message. The advantage is that one could have larger groups than if you require a client-side fan out, wherein all clients send each message to all N participants in a group.

In more detail, WhatsApp has clients generate a random *Chain key* and random Curve25519 key pair they call the *Signature key* upon joining a group. These two keys are described as a *Sender key*, and are sent to all group participants pairwise. Each chain key is used by participants to derive individual message keys. Ciphertexts are signed by senders using the signature key. When a group participant sends a message, the server performs the server-side fan out, sending the ciphertext to all other group participants. The receiving group participants can decrypt the ciphertext since they received the chain key from the sender previously. The sender keys are rotated whenever a group member leaves. One hiccup here is that as described, the DH ratchet is not happening: if a chain key is compromised, all other messages using message keys dervied from that chain key can be decrypted. This will be the case until a group member leaves.

One other interesting note from the whitepaper is that client-server connections are also encrypted at the transport-level using [Noise Pipes](https://noiseprotocol.org/) (they used Curve25519, AES-GCM, SHA256).

### Fingerprint Verification

Fingerprints are in the form of QR codes or 60-digit fingerprints (30 digits per party). These codes are derived from the public part of the long-term identity key for both parties, along with for the QR code, a version and user identifiers for each party.
