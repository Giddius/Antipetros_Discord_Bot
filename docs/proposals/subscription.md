# Subscription Mechanic Through AntiPetros


## General

### From User PoV

From the users Point of view he just has to visit the `Subscription-Channel`, there he is presented with all available topics to subscribe. If He wants to subscribe to one, he just reacts to the Topic with the required Emoji. All other emojis are ignored and removed from the message.

Afterwards he gets a DM telling him that he has successfully subscribed to the topic and he now has a new Role.

If he wants to unsubscribe, he just goes back to the `Subscription-Channel` and removes his emoji.

There is another way to subscribe and unsubscribe and that is through a AntiPetros command either as DM or inside a channel (can be locked to DM's)

### From Teams PoV

First a Topic is created via the new_topic command. This command takes an txt file as attachment.
This is an example of the structure of the file:
```txt
name = another_test
emoji = 🎫
image = https://s3.eu-central-1.amazonaws.com/rausgegangen/p7PBNtdmS8iSkHm8Aqn5_happy-test-screen-01png
description = something I am to down to think of some clever text now
but hey, you can also use new lines

now a few morre also, blah I hate writing texts and thinking them up, please somebody do the text writing for me
```

It is basically `keyword` `=` `value`. It supports multiline inside the description value.

When there is a announcment for that topic, he just uses the created Role as `@createdRole` and all subscribers are pinged.

## Limitations

### Emojis

It only supports standard Discord emojis. This is a limitation of mine, as dealing with custom emojis is quite problematic and also custom emojis could be switched out while keeping the name. This could lead to an situation where the subscription emojis does not work anymore. It would not be a problem if we had a fix and almost non changing roster of custom emojis, but seeing how in flux they are, it is a problem.

### Roles

The roles created follow a simple template:
It is always "`NAME_OF_THE_TOPIC`_Subscriber", so for example for the Topic `Game_Night` it would be `@Game_Night_Subscriber`. These roles have no special permissions and are at the lowest level. Only thing theyx have is that they can be mentioned.

### Topic Names

It is not a must, but I would advise only creating names that DO NOT have spaces in them. Use underscores. This is not mandatory.



## Subscription Channel

I would advise creating a subscription channel, the bot already has a command that then would create an information head embed message. This makes it easier to see what subscriptions there are.




## Gifs

Attached there are two gives showing the general function (all specifics can be easily changed, dont get hung up on text or look)


## Pinging 3000+ User

The Bot is able to write the Mention ala `@Something` into the messages without pinging anyone.


## Info

The bot can be configured to write a welcome message to every new user, that also includes the direction to the subscription channels.

## Opt-in vs Opt-out

It should be Opt-in, because certain points of Discords Tos and Discords Dev ToS can be read as forbidding mass announcement spam.

see https://discord.com/developers/docs/resources/user#create-dm

```fix
You should not use this endpoint to DM everyone in a server about something. DMs should generally be initiated by a user action. If you open a significant amount of DMs too quickly, your bot may be rate limited or blocked from opening new ones.
```

https://discord.com/developers/docs/legal

```fix
COMMUNICATIONS

You agree to receive communications from us electronically, such as email, text, or mobile push notices, or notices and messages on the Service. For any direct marketing messages, we will ensure that we obtain your consent first, and also make it easy for you to opt out — we don’t want to send you messages you don’t want.

By using the Service or providing information to us, you agree that we may communicate with you electronically regarding security, privacy, and administrative issues relating to your use of the Service, and that all agreements, notices, disclosures, and other communications that Discord provides to you electronically satisfy any legal requirements that such communications be in writing.

You may use the Service to send messages to other users of the Service. You agree that your use of the Service will not include sending unsolicited marketing messages or broadcasts (i.e., spam). We may utilize a variety of means to block spammers and abusers from using the Service. If you believe spam originated from the Service, please email us immediately at support@discord.com.
```

```fix
post messages, trigger notifications, or play audio on behalf of a Discord user except in response to such Discord user expressly opting-in to each instance of such action;
```

https://discord.com/terms

```fix
You may use the Service to send messages to other users of the Service. You agree that your use of the Service will not include sending unsolicited marketing messages or broadcasts (i.e., SPAM). We may utilize a variety of means to block spammers and abusers from using the Service. If you believe spam originated from the Service, please email us immediately at support@discord.com.
```