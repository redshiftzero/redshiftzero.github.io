+++
date = "2020-10-14"
title = "Investigating the Signal Protocol, Part 2: Groups, devices"
slug = "signal-group-multidevice"
categories = [ "Post", "Signal"]
tags = [ "Signal", "security", "protocol" ]
+++

Next in the series, I investigate how groups and multi-device support are handled. If you have thoughts on this or notice any errors, feel free to drop me a note on [Twitter](https://twitter.com/redshiftzero) or by [email](mailto:jen@redshiftzero.com).

# Groups

Signal allows [private groups](https://signal.org/blog/private-groups/) where the server doesn't have access to the group metadata, including the list of members in each group. Servers cannot even distinguish group from direct messages.

Let's say a group contains two users, Alice👧🏼 and Bob👦🏽, and a third user Jen🧙 wants to send the group a message. Alice👧🏼 adds Jen🧙 to the group, and then Jen🧙 can send the group a message by sending messages individually to each user in the group: she encrypts her message $M$ to each group participant separately, encrypting using the next message key she has for Alice👧🏼 and Bob👦🏽. One caveat is that she uses separate ratchet state than her direct chats with Alice👧🏼 and Bob👦🏽.

Group management messages are regular Signal (i.e. e2e encrypted) messages that only clients can decrypt and act on. The advantage of this approach is that the server stores nothing about groups, although the server can of course infer group participants through observing the timing and metadata of messages, but we'll put that aside for now.

For example, if Alice👧🏼 chooses to leave a group:

1. Alice👧🏼 sends a leave group management message to all other group members (along with the ID of the group).
2. Clients process this and remove Alice👧🏼 from their locally stored list of users in that group.

Similarly for other group information update tasks, any group participant can send a group management message adding (but not deleting) new users or updating the group information. This means that since users must remove *themselves* from groups using a leave message, if a group wants to remove a given user and the user does not leave, effectively users must create a new group without the participant they want to remove.

The group system is under active development, see the preview version of the group management using anonymous credentials described [here](https://signal.org/blog/signal-private-group-system/). Note also that Whatsapp appears to handle groups differently from the Signal application.

# Multi-device

*The full description is covered in [this specification](https://signal.org/docs/specifications/sesame/).*

For multi-device support, the main concepts we need to know about are:

* Users, which are identified by `UserID` and can have one or more devices.
* Devices, which are identified by `DeviceID`. Each device has its own keypair.
* Sessions, which are identified by `SessionID`. This is the ratchet state that can be used for processing incoming and outgoing messages.

The server keeps track of the mapping of users (`UserID`) to devices (`DeviceID`). This is different than with groups, where the server doesn't need to keep track of users in groups.

An *initiation message* begins a session. In this message, the sender includes their device public key, so the recipient knows which of the user's devices is active. Clients keep track locally of a mapping of users (`UserID`) to devices (`DeviceID`) and furthermore, which of the devices is active.

When Bob👦🏽 sends Alice👧🏼 a message $m$, he encrypts $m$ for all of Alice👧🏼's devices using active sessions if available. This is the first batch of messages. Bob👦🏽 does the same action for himself: he encrypts the message $m$ to all of his own devices (a second batch of messages). For each batch he:

1. Sends the batch of messages to the server.
2. If Bob👦🏽's local view of the receiver device state was stale, the server rejects the messages and lets Bob👦🏽 know to update. Else, the servers puts the messages in the message delivery queues for those devices.

By doing this Bob👦🏽's other devices will also have the message history of this conversation even if the device is not active.

When Alice👧🏼 connects to the server to get her messages, she uses any initiation messages to update her local store of device and session state. Otherwise, she uses the existing session state as usual to process the message.
