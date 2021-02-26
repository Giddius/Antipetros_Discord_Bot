__**command "create_giveaway"**__

```py
@AntiDEVtros create_giveaway [--title] [--end-date] [--num-winners] [--end-message] [--start-message] [--enter-emoji]
```

**Flags**

__--title__
    short: `-t`
    type: `TEXT`
    default: `Antistasi Give-Away`
    description: The text that is at the top of the give-away embed

__--end-date__
    short: `-end`
    type: `TEXT`
    default: `24 hours`
    description: Amount of time the give-away should run. The bot will parse it from normal speach (i.e. "3 days and 2 hours", "1 week", "10 seconds")

__--num-winners__
    short: `-nw`
    type: `NUMBER`
    default: `1`
    description: How many winners should be selected at the end.
                 If less people participated than this number, the bot chooses all participants as winners (i.e. --num-winners 4, participants 2, 2 winners get choosen)

__--end-message__
    short: `-emsg`
    type: `TEXT`
    default: `Give away has finished!`
    description: The message that should show up on the embed that announces the winners.

__--start-message__
    short: `-smsg`
    type: `TEXT`
    default: `NO DEFAULT`
    description: The message that should show up on the embed, where people can participate.

__--enter-emoji__
    short: `-em`
    type: `EMOJI`
    default: `🎁`
    description: The emoji people have to use to enter the give-away. All other emojis that people add to the give-away embed get deleted to keep joksters at bay.

**Overall Description**
After invocation of the command the bot will present you with an embed, that summarizes your input and he will ask you to confirm it via click on the ✅ emoji.

The bot will choose via an non-deterministic RNG, that is also used for password secrets and so on. Therefore it is as random as you can get with python.
After the give-away has finished it will send a DM with the name of the winners to the user that initiated the give-away. If no one participated, the bot will delete the give-away and also
send a DM to the initiator that the give-away failed because no one participated.
Also after the give-away has finished it will delete the embed where people can add the emoji to enter and replace it with an embed that contains the `end-message` and the name of the winners.
Flags can be set in any order you wish and work just like CommandLineInteface Flags for CMD or SHELL.

**IMPORTANT**
All entries need to be quoted if they have spaces in them. e.g.: `@AntiPetros giveaway -t "this is the title" -smsg "this is the start message" -end "3 days and 9 hours"`

**Example**
```cmd
@AntiPetros giveaway -t "Example Give-Away" -em 🎁 -smsg "test give away please if you can read this hit the emoji to help me test it" -end "15 min" -emsg "Congratulations you have won the gift of friendship" -nw 2
```