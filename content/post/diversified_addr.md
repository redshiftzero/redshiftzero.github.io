+++
date = "2025-08-20"
title = "Understanding Diversified Addresses"
slug = "diversified-addresses"
categories = [ "Post", "Cryptography"]
tags = [ "cryptography" ]
+++

Diversified addresses are a feature of ZCash-like protocols that let you publish
an effectively unlimited number (well, $2^{88}$) of unlinkable payment addresses all of
which pay into the same wallet.

This means you don't need to manage separate accounts or wallets to give each
counterparty a unique address. Instead you get the benefits of unlinkability while
consolidating funds under a single spending authority.

# Trial Decryption

Private cryptocurrencies like ZCash use trial decryption to figure out which
payments belong to you.

When you make a simple spending transaction, you include an encrypted note. They specify an amount of e.g. ZEC,
and the address of the recipient. These encrypted notes are posted to the blockchain.

To learn which notes are yours, your wallet downloads the entire chain and
attempts to decrypt note ciphertexts. If decryption succeeds, then the note belongs to you. That's a big performance bottleneck.

Under the hood, here's what happening cryptographically:

* Notes are encrypted with a symmetric key.
* This key is derived from the IVK, the incoming viewing key.
* The IVK doesn't let you spend, but it lets you view.
* The sender and recipient derive a shared secret using Diffie-Hellman key agreement between the sender and the recipient's IVK.

We'll discuss more how this works later in the post. First, let's discuss what addresses are.

# Addresses

In most cryptocurrencies, an address is a string of characters that represents a hash of a public key. Whoever can sign with the corresponding private key can spend the funds.

In ZCash, addresses are a little different. A shielded payment address contains:

* a diversifier $d$ (in ZCash Sapling, 11 bytes)
* a 32-byte transmission key $pk_d$ (32 bytes)

Here's the key innovation: in ZCash, you can have many "diversified" addresses that all decrypt with the same IVK, and spend with the same spending key. To an observer, they appear completely unrelated.

# Key Agreement

Let's discuss basic key agreement in a ZCash-like cryptocurrency.

We've discussed the incoming viewing key. We take the scalar $ivk$ and multiply it by a basepoint $G$, to give us a public key. This public key we'll put in our address. Let's call this recipient public key $pk$ for now:

$pk = [ivk] G$

The sender generates a random ephemeral secret key $esk$, and generate a shared secret, using the public key $pk$ of the recipient:

$[esk]pk = [esk][ivk]G$

Then the sender provides the corresponding ephemeral public key $epk = [esk]G$ in the transaction with the encrypted note such that the recipient can calculate the same shared secret:

$[ivk]epk = [esk][ivk]G$

This shared secret is used to derive the symmetric key used to encrypt the note.

# Diversification

The problem, is that using this approach, when we do trial decryption, we're only
finding the notes corresponding to our one address $pk$. If we stopped there, each recipient would only have one address, meaning that addresses are linkable.

Instead, we are going to vary the basepoint, instead of assuming our basepoint $G$ is fixed.

We'll use the diversifier $d$ in our address, to derive a diversified basepoint for each diversifier:

$G_{d} = H(d)$

Here $H$ is a hash-to-group function, which just maps arbitrary input into a valid group element, in our case, an elliptic curve point. The resulting $G_d$ we call the *diversified basepoint*. (In ZCash, $d$ is produced by encrypting an index with AES, which ensures the distribution looks random.)

Then, we use that diversified basepoint $G_d$ to derive our diversified transmission key $pk_d$:

$pk_d = [ivk] G_d$

Each address is now $(d, pk_d)$.

# Why it works

This lets you scan for all your payments, to all your diversified addresses, since they all use the _same_ incoming viewing key. All these payments map back to the same spending authority. But to observers, each $pk_d$ looks independent, since the basepoint $G_d$ is derived uniquely per diversifier $d$.

This lets you hand out a fresh, unlinkable address for each counterparty or payment.
