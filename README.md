# <p align="center">Antipetros Discordbot</p>


<p align="center"><img src="art/finished/images/AntiPetros_for_readme.png" alt="Antipetros Discordbot Avatar"/></p>


---

## ToC



  
  - [Installation](#Installation)    
    - [PyPi](#PyPi)  
  - [Usage](#Usage)  
  - [Description](#Description)  
  - [Features](#Features)    
    - [AdministrationCog](#AdministrationCog)    
    - [AntistasiLogWatcherCog](#AntistasiLogWatcherCog)    
    - [BotAdminCog](#BotAdminCog)    
    - [CommunityServerInfoCog](#CommunityServerInfoCog)    
    - [ConfigCog](#ConfigCog)    
    - [FaqCog](#FaqCog)    
    - [GeneralDebugCog](#GeneralDebugCog)    
    - [GiveAwayCog](#GiveAwayCog)    
    - [ImageManipulatorCog](#ImageManipulatorCog)    
    - [KlimBimCog](#KlimBimCog)    
    - [PurgeMessagesCog](#PurgeMessagesCog)    
    - [SaveSuggestionCog](#SaveSuggestionCog)    
    - [SubscriptionCog](#SubscriptionCog)    
    - [TemplateCheckerCog](#TemplateCheckerCog)    
    - [TranslateCog](#TranslateCog)  
  - [Dependencies](#Dependencies)    
    - [Python dependencies](#Python-dependencies)    
    - [External dependencies](#External-dependencies)  
  - [License](#License)  
  - [Development](#Development)    
    - [Future Plans](#Future-Plans)  
  - [See also](#See-also)    
    - [Links](#Links)



---



__**Bot-Name:**__

> AntiPetros

__**Version:**__

> 1.0.1





---

## Installation



### PyPi

```shell
pip install antipetros_discordbot==1.0.1
```



---

## Usage




- __**antipetrosbot clean**__
    > Cli command to clean the 'APPDATA' folder that was created.


- __**antipetrosbot run**__
    > Standard way to start the bot and connect it to discord.


- __**antipetrosbot stop**__
    > Cli way of autostoping the bot.





---

## Description







---

## Features




<details><summary><b>Currently usable Cogs</b></summary><blockquote>



### <p align="center"><b>[AdministrationCog](antipetros_discordbot/cogs/discord_admin_cogs/discord_admin_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Soon</blockquote>

#### Config Name

<blockquote>administration</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- OUTDATED

- NEEDS_REFRACTORING

- FEATURE_MISSING

- UNTESTED

- OPEN_TODOS
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **DELETE_MSG**
    

    
    - **aliases:** *delete+msg*, *deletemsg*, *delete.msg*, *delete-msg*
    

    
    - **checks:** *log_invoker*, *owner_or_admin*
    

    
    - **signature:**
        ```diff
        @AntiPetros <msg_id>
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[AntistasiLogWatcherCog](antipetros_discordbot/cogs/antistasi_tool_cogs/antistasi_log_watcher_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>soon</blockquote>

#### Config Name

<blockquote>antistasi_log_watcher</blockquote>


#### Cog State Tags

```diff
- EMPTY

- DOCUMENTATION_MISSING

- CRASHING

- OUTDATED

- FEATURE_MISSING

- UNTESTED
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **GET_NEWEST_LOGS**
    

    
    - **aliases:** *get+newest+logs*, *get.newest.logs*, *getnewestlogs*, *get-newest-logs*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros <server> <sub_folder> [amount=1]
        ```
    
    <br>


- **GET_NEWEST_MOD_DATA**
    

    
    - **aliases:** *get.newest.mod.data*, *get-newest-mod-data*, *getnewestmoddata*, *get+newest+mod+data*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros <server>
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[BotAdminCog](antipetros_discordbot/cogs/bot_admin_cogs/bot_admin_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Soon</blockquote>

#### Config Name

<blockquote>bot_admin</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- FEATURE_MISSING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **ADD_TO_BLACKLIST**
    

    
    - **aliases:** *add-to-blacklist*, *add.to.blacklist*, *add+to+blacklist*, *addtoblacklist*
    

    
    - **checks:** *log_invoker*, *owner_or_admin*
    

    
    - **signature:**
        ```diff
        @AntiPetros <user>
        ```
    
    <br>


- **ADD_WHO_IS_PHRASE**
    

    
    - **aliases:** *add-who-is-phrase*, *add+who+is+phrase*, *add.who.is.phrase*, *addwhoisphrase*
    

    
    - **checks:** *owner_or_admin*
    

    
    - **signature:**
        ```diff
        @AntiPetros <phrase>
        ```
    
    <br>


- **ALL_ALIASES**
    

    
    - **aliases:** *allaliases*, *all.aliases*, *all-aliases*, *all+aliases*
    

    

    
    <br>


- **INVOCATION_PREFIXES**
    

    
    - **aliases:** *invocation+prefixes*, *invocationprefixes*, *invocation.prefixes*, *invocation-prefixes*
    

    

    
    <br>


- **LIFE_CHECK**
    

    
    - **aliases:** *you_dead?*, *lifecheck*, *life.check*, *poke-with-stick*, *life+check*, *are-you-there*, *life-check*
    

    

    
    <br>


- **REMOVE_FROM_BLACKLIST**
    

    
    - **aliases:** *removefromblacklist*, *remove-from-blacklist*, *remove+from+blacklist*, *remove.from.blacklist*
    

    
    - **checks:** *log_invoker*, *owner_or_admin*
    

    
    - **signature:**
        ```diff
        @AntiPetros <user>
        ```
    
    <br>


- **SELF_ANNOUNCEMENT**
    

    
    - **aliases:** *self-announcement*, *selfannouncement*, *self.announcement*, *self+announcement*
    

    
    - **checks:** *is_owner*
    

    
    - **signature:**
        ```diff
        @AntiPetros <channel> [test=False]
        ```
    
    <br>


- **SEND_LOG_FILE**
    

    
    - **aliases:** *send+log+file*, *send.log.file*, *sendlogfile*, *send-log-file*
    

    
    - **checks:** *is_owner*
    

    
    - **signature:**
        ```diff
        @AntiPetros [which_logs=newest]
        ```
    
    <br>


- **TELL_UPTIME**
    

    
    - **aliases:** *tell.uptime*, *tell-uptime*, *tell+uptime*, *telluptime*
    

    

    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[CommunityServerInfoCog](antipetros_discordbot/cogs/antistasi_tool_cogs/community_server_info_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>soon</blockquote>

#### Config Name

<blockquote>community_server_info</blockquote>


#### Cog State Tags

```diff
- EMPTY

- DOCUMENTATION_MISSING

- CRASHING

- OUTDATED

- FEATURE_MISSING

- UNTESTED
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **CURRENT_ONLINE_SERVER**
    

    
    - **aliases:** *current-online-server*, *current.online.server*, *current+online+server*, *currentonlineserver*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    <br>


- **CURRENT_PLAYERS**
    

    
    - **aliases:** *currentplayers*, *current+players*, *current-players*, *current.players*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros <server>
        ```
    
    <br>


- **EXCLUDE_FROM_SERVER_STATUS_NOTIFICATION**
    

    
    - **aliases:** *exclude-from-server-status-notification*, *excludefromserverstatusnotification*, *exclude.from.server.status.notification*, *exclude+from+server+status+notification*
    

    
    - **checks:** *log_invoker*, *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros <server_name>
        ```
    
    <br>


- **UNDO_EXCLUDE_FROM_SERVER_STATUS_NOTIFICATION**
    

    
    - **aliases:** *undoexcludefromserverstatusnotification*, *undo+exclude+from+server+status+notification*, *undo-exclude-from-server-status-notification*, *undo.exclude.from.server.status.notification*
    

    
    - **checks:** *log_invoker*, *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros <server_name>
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[ConfigCog](antipetros_discordbot/cogs/bot_admin_cogs/config_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Cog with commands to access and manipulate config files, also for changing command aliases.
Almost all are only available in DM's

commands are hidden from the help command.</blockquote>

#### Config Name

<blockquote>config</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- CRASHING

- OUTDATED

- NEEDS_REFRACTORING

- FEATURE_MISSING

- UNTESTED

- OPEN_TODOS
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **ADD_ALIAS**
    

    
    - **aliases:** *add+alias*, *addalias*, *add.alias*, *add-alias*
    

    
    - **checks:** *log_invoker*, *owner_or_admin*
    

    
    - **signature:**
        ```diff
        @AntiPetros <command_name> <alias>
        ```
    
    <br>


- **CHANGE_SETTING_TO**
    
    ```diff
    + Command to change a single config setting.
    ```
    

    

    
    - **checks:** *is_owner*
    

    
    - **signature:**
        ```diff
        @AntiPetros <config> <section> <option> <value>
        ```
    
    <br>


- **CONFIG_REQUEST**
    
    ```diff
    + Sends config files via discord as attachments.
    ```
    

    

    
    - **checks:** *is_owner*
    

    
    - **signature:**
        ```diff
        @AntiPetros [config_name=all]
        ```
    
    <br>


- **LIST_CONFIGS**
    
    ```diff
    + Lists all available configs, usefull to get the name for the other commands
    ```
    

    

    
    - **checks:** *is_owner*
    

    
    <br>


- **OVERWRITE_CONFIG_FROM_FILE**
    
    ```diff
    + Accepts and config file as attachments and replaces the existing config with it.
    ```
    

    

    
    - **checks:** *log_invoker*, *is_owner*
    

    
    <br>


- **SHOW_CONFIG_CONTENT**
    

    

    
    - **checks:** *is_owner*
    

    
    - **signature:**
        ```diff
        @AntiPetros [config_name=all]
        ```
    
    <br>


- **SHOW_CONFIG_CONTENT_RAW**
    

    

    
    - **checks:** *is_owner*
    

    
    - **signature:**
        ```diff
        @AntiPetros [config_name=all]
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[FaqCog](antipetros_discordbot/cogs/special_channels_cogs/faq_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Creates Embed FAQ items.</blockquote>

#### Config Name

<blockquote>faq</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- FEATURE_MISSING

- UNTESTED

+ WORKING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **ADD_FAQ_ITEM**
    
    ```diff
    + UNFINISHED
    ```
    

    
    - **aliases:** *add-faq-item*, *add.faq.item*, *add+faq+item*, *addfaqitem*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros [faq_number] [from_message]
        ```
    
    <br>


- **CREATE_FAQS_AS_EMBED**
    
    ```diff
    + Posts all faqs ,that it has saved, at once and posts a TOC afterwards.
    ```
    

    
    - **aliases:** *create-faqs-as-embed*, *createfaqsasembed*, *create.faqs.as.embed*, *create+faqs+as+embed*
    

    
    - **checks:** *log_invoker*, *owner_or_admin*
    

    
    - **signature:**
        ```diff
        @AntiPetros [as_template]
        ```
    
    <br>


- **POST_FAQ_BY_NUMBER**
    
    ```diff
    + Posts an FAQ as an embed on request.
    ```
    

    
    - **aliases:** *postfaqbynumber*, *post-faq-by-number*, *post+faq+by+number*, *post.faq.by.number*, *faq*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros [faq_numbers]... [as_template]
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[GeneralDebugCog](antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Cog for debug or test commands, should not be enabled fo normal Bot operations.</blockquote>

#### Config Name

<blockquote>general_debug</blockquote>


#### Cog State Tags

```diff
- FOR_DEBUG

- DOCUMENTATION_MISSING

- NEEDS_REFRACTORING

- FEATURE_MISSING

- UNTESTED

- OPEN_TODOS

+ WORKING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **ALL_CHANNEL_PERMISSIONS**
    

    
    - **aliases:** *all.channel.permissions*, *all-channel-permissions*, *allchannelpermissions*, *all+channel+permissions*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros [member] [display_mode=only_true] [filter_category]
        ```
    
    <br>


- **CHECK_A_HOOK**
    

    
    - **aliases:** *check+a+hook*, *checkahook*, *check-a-hook*, *check.a.hook*
    

    

    
    <br>


- **CHECK_BOT_CHANNEL_PERMISSIONS**
    

    
    - **aliases:** *check-bot-channel-permissions*, *check.bot.channel.permissions*, *channel_permissions*, *checkbotchannelpermissions*, *check+bot+channel+permissions*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros [channel] [member] [display_mode=only_true] [json_file]
        ```
    
    <br>


- **CHECK_EMBED_GIF**
    

    

    

    
    <br>


- **CHECK_NOT_ALLOWED_CHANNEL**
    

    
    - **aliases:** *check-not-allowed-channel*, *check.not.allowed.channel*, *check+not+allowed+channel*, *checknotallowedchannel*
    

    

    
    <br>


- **CHECK_RELOAD_MECH**
    

    
    - **aliases:** *checkreloadmech*, *check+reload+mech*, *check.reload.mech*, *check-reload-mech*
    

    

    
    <br>


- **CREATE_ROLE_BY_NAME_AND_ASSIGN_TO_ALL**
    

    
    - **aliases:** *create-role-by-name-and-assign-to-all*, *createrolebynameandassigntoall*, *create.role.by.name.and.assign.to.all*, *create+role+by+name+and+assign+to+all*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros <role_name> <reason>
        ```
    
    <br>


- **DUMP_PERMISSIONS**
    

    
    - **aliases:** *dump.permissions*, *dump-permissions*, *dumppermissions*, *dump+permissions*
    

    

    
    <br>


- **GET_ALL_ATTACHMENTS**
    

    
    - **aliases:** *get.all.attachments*, *get-all-attachments*, *get+all+attachments*, *getallattachments*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros <channel> [amount_to_scan]
        ```
    
    <br>


- **GET_ALL_FROM_EMBED_USER**
    

    
    - **aliases:** *getallfromembeduser*, *get-all-from-embed-user*, *get.all.from.embed.user*, *get+all+from+embed+user*
    

    
    - **checks:** *only_giddi*
    

    
    <br>


- **GET_PREFIXES**
    

    

    

    
    - **signature:**
        ```diff
        @AntiPetros <message>
        ```
    
    <br>


- **MENTION_NOMAS**
    

    
    - **aliases:** *mention-nomas*, *mention+nomas*, *mentionnomas*, *mention.nomas*
    

    

    
    <br>


- **MOCK_SUBSCRIBE_THING**
    

    
    - **aliases:** *mock.subscribe.thing*, *mock+subscribe+thing*, *mocksubscribething*, *mock-subscribe-thing*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros [topics...]
        ```
    
    <br>


- **PIN_MESSAGE**
    

    
    - **aliases:** *pin-message*, *pin*, *pin.message*, *pinmessage*, *pin+message*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros <reason>
        ```
    
    <br>


- **QUICK_LATENCY**
    

    
    - **aliases:** *quicklatency*, *quick.latency*, *quick+latency*, *quick-latency*
    

    

    
    <br>


- **REQUEST_SERVER_RESTART**
    

    
    - **aliases:** *requestserverrestart*, *request-server-restart*, *request+server+restart*, *request.server.restart*
    

    

    
    <br>


- **ROLL_BLOCKING**
    

    
    - **aliases:** *roll.blocking*, *roll-blocking*, *roll+blocking*, *rollblocking*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros [target_time=1]
        ```
    
    <br>


- **SAVE_EMBED**
    

    
    - **aliases:** *save.embed*, *save+embed*, *save-embed*, *saveembed*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros <message>
        ```
    
    <br>


- **SHOW_COMMAND_NAMES**
    

    
    - **aliases:** *show-command-names*, *showcommandnames*, *show+command+names*, *show.command.names*
    

    

    
    <br>


- **THE_BOTS_NEW_CLOTHES**
    

    
    - **aliases:** *clr-scrn*
    

    

    
    <br>


- **UNPIN_MESSAGE**
    

    
    - **aliases:** *unpin+message*, *unpin*, *unpin-message*, *unpinmessage*, *unpin.message*
    

    

    
    - **signature:**
        ```diff
        @AntiPetros <reason>
        ```
    
    <br>


- **WRITE_DATA**
    

    
    - **aliases:** *write-data*, *write+data*, *write.data*, *writedata*
    

    

    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[GiveAwayCog](antipetros_discordbot/cogs/community_events_cogs/give_away_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Soon</blockquote>

#### Config Name

<blockquote>give_away</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- FEATURE_MISSING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **ABORT_GIVE_AWAY**
    

    
    - **aliases:** *abortgiveaway*, *abort+give+away*, *abort-give-away*, *abort.give.away*
    

    
    - **checks:** *log_invoker*, *allowed_channel_and_allowed_role_2*
    

    
    <br>


- **CREATE_GIVEAWAY**
    

    
    - **aliases:** *create+giveaway*, *creategiveaway*, *giveaway*, *create.giveaway*, *create-giveaway*
    

    
    - **checks:** *log_invoker*, *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros [--enter_emoji ENTER_EMOJI=🎁] [--start_message START_MESSAGE] [--end_message END_MESSAGE=Give away has finished!] [--num_winners NUM_WINNERS=1] [--end_date END_DATE=24 hours] [--title TITLE=Antistasi Give-Away]
        ```
    
    <br>


- **FINISH_GIVE_AWAY**
    

    
    - **aliases:** *finishgiveaway*, *finish-give-away*, *finish.give.away*, *finish+give+away*
    

    
    - **checks:** *log_invoker*, *allowed_channel_and_allowed_role_2*
    

    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[ImageManipulatorCog](antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Soon</blockquote>

#### Config Name

<blockquote>image_manipulation</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- NEEDS_REFRACTORING

- FEATURE_MISSING

- UNTESTED

- OPEN_TODOS

+ WORKING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **AVAILABLE_STAMPS**
    
    ```diff
    + Posts all available stamps.
    ```
    

    
    - **aliases:** *available.stamps*, *available+stamps*, *available-stamps*, *availablestamps*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    <br>


- **MEMBER_AVATAR**
    
    ```diff
    + Stamps the avatar of a Member with the Antistasi Crest.
    ```
    

    
    - **aliases:** *member-avatar*, *member+avatar*, *memberavatar*, *member.avatar*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    <br>


- **STAMP_IMAGE**
    
    ```diff
    + Stamps an image with a small image from the available stamps.
    ```
    

    
    - **aliases:** *stamp+image*, *stamp-image*, *stamp.image*, *stampimage*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros [--factor FACTOR] [--stamp_opacity STAMP_OPACITY=1.0] [--second_pos SECOND_POS=right] [--first_pos FIRST_POS=bottom] [--stamp_image STAMP_IMAGE=ASLOGO1]
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[KlimBimCog](antipetros_discordbot/cogs/general_cogs/klim_bim_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Collection of small commands that either don't fit anywhere else or are just for fun.</blockquote>

#### Config Name

<blockquote>klim_bim</blockquote>


#### Cog State Tags

```diff
+ WORKING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **FLIP_COIN**
    
    ```diff
    + Simulates a coin flip and posts the result as an image of a Petros Dollar.
    ```
    

    
    - **aliases:** *flip+coin*, *flip-coin*, *flip.coin*, *flipcoin*, *flip*, *coinflip*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    <br>


- **MAKE_FIGLET**
    
    ```diff
    + Posts an ASCII Art version of the input text.
    ```
    

    
    - **aliases:** *make.figlet*, *make+figlet*, *make-figlet*, *makefiglet*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros <text>
        ```
    
    <br>


- **THE_DRAGON**
    
    ```diff
    + Posts and awesome ASCII Art Dragon!
    ```
    

    
    - **aliases:** *thedragon*, *the.dragon*, *the-dragon*, *the+dragon*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    <br>


- **URBAN_DICTIONARY**
    
    ```diff
    + Searches Urbandictionary for the search term and post the answer as embed
    ```
    

    
    - **aliases:** *urbandictionary*, *urban+dictionary*, *urban.dictionary*, *urban-dictionary*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros <term> [entries=1]
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[PurgeMessagesCog](antipetros_discordbot/cogs/discord_admin_cogs/purge_messages_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Soon</blockquote>

#### Config Name

<blockquote>purge_messages</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- FEATURE_MISSING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **PURGE_ANTIPETROS**
    

    
    - **aliases:** *purge+antipetros*, *purge.antipetros*, *purgeantipetros*, *purge-antipetros*
    

    
    - **checks:** *in_allowed_channels*, *is_owner*
    

    
    - **signature:**
        ```diff
        @AntiPetros [--number_of_messages NUMBER_OF_MESSAGES=99999999999] [--and_giddi AND_GIDDI=False]
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[SaveSuggestionCog](antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Soon</blockquote>

#### Config Name

<blockquote>save_suggestion</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- NEEDS_REFRACTORING

- FEATURE_MISSING

- UNTESTED

- OPEN_TODOS

+ WORKING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **AUTO_ACCEPT_SUGGESTIONS**
    

    

    
    - **checks:** *dm_only*
    

    
    <br>


- **CLEAR_ALL_SUGGESTIONS**
    

    

    
    - **checks:** *owner_or_admin*
    

    
    - **signature:**
        ```diff
        @AntiPetros [sure=False]
        ```
    
    <br>


- **GET_ALL_SUGGESTIONS**
    

    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros [report_template=basic_report.html.jinja]
        ```
    
    <br>


- **MARK_DISCUSSED**
    

    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros [suggestion_ids...]
        ```
    
    <br>


- **REMOVE_ALL_USERDATA**
    

    

    
    - **checks:** *dm_only*
    

    
    <br>


- **REQUEST_MY_DATA**
    

    

    
    - **checks:** *dm_only*
    

    
    <br>


- **UNSAVE_SUGGESTION**
    

    

    
    - **checks:** *dm_only*
    

    
    - **signature:**
        ```diff
        @AntiPetros <suggestion_id>
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[SubscriptionCog](antipetros_discordbot/cogs/discord_admin_cogs/subscription_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Soon</blockquote>

#### Config Name

<blockquote>subscription</blockquote>


#### Cog State Tags

```diff
- DOCUMENTATION_MISSING

- FEATURE_MISSING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **CREATE_SUBSCRIPTION_CHANNEL**
    

    
    - **aliases:** *create-subscription-channel*, *createsubscriptionchannel*, *create.subscription.channel*, *create+subscription+channel*
    

    
    - **checks:** *owner_or_admin*
    

    
    - **signature:**
        ```diff
        @AntiPetros <category> <name>
        ```
    
    <br>


- **NEW_TOPIC**
    

    
    - **aliases:** *new+topic*, *new-topic*, *newtopic*, *new.topic*
    

    
    - **checks:** *has_attachments*
    

    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[TemplateCheckerCog](antipetros_discordbot/cogs/antistasi_tool_cogs/template_checker_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>soon</blockquote>

#### Config Name

<blockquote>template_checker</blockquote>


#### Cog State Tags

```diff
- EMPTY

- DOCUMENTATION_MISSING

- CRASHING

- OUTDATED

- FEATURE_MISSING

- UNTESTED
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **CHECK_TEMPLATE**
    

    
    - **aliases:** *checktemplate*, *check.template*, *check+template*, *check-template*
    

    
    - **checks:** *has_attachments*, *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros [all_items_file=True] [case_insensitive=False]
        ```
    
    <br>



</blockquote>

</details>

---



### <p align="center"><b>[TranslateCog](antipetros_discordbot/cogs/general_cogs/translate_cog.py)</b></p>

<details><summary><b>Description</b></summary>




#### Short Description

<blockquote>Collection of commands that help in translating text to different Languages.</blockquote>

#### Config Name

<blockquote>translate</blockquote>


#### Cog State Tags

```diff
+ WORKING
```

</details>

<details><summary><b>Commands</b></summary><blockquote>


- **AVAILABLE_LANGUAGES**
    

    
    - **aliases:** *available-languages*, *available.languages*, *availablelanguages*, *available+languages*
    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    <br>


- **TRANSLATE**
    
    ```diff
    + Translates text into multiple different languages.
    ```
    

    

    
    - **checks:** *allowed_channel_and_allowed_role_2*
    

    
    - **signature:**
        ```diff
        @AntiPetros [to_language_id=english] <text_to_translate>
        ```
    
    <br>



</blockquote>

</details>

---


</blockquote></details>



---

## Dependencies



**Developed with Python Version `3.9.1`**

### Python dependencies


- **Jinja2** *2.11.2*

- **Pillow** *8.1.2*

- **WeasyPrint** *52.2*

- **aiohttp** *3.7.3*

- **aiosqlite** *0.16.1*

- **antistasi_template_checker** *0.1.1*

- **arrow** *0.17.0*

- **async_property** *0.2.1*

- **asyncstdlib** *3.9.0*

- **beautifulsoup4** *4.9.3*

- **click** *7.1.2*

- **cryptography** *3.3.1*

- **dateparser** *1.0.0*

- **discord-flags** *2.1.1*

- **dpytest** *0.0.22*

- **emoji** *1.1.0*

- **fuzzywuzzy** *0.18.0*

- **gidappdata** *0.1.13*

- **gidconfig** *0.1.16*

- **gidlogger** *0.1.9*

- **googletrans** *4.0.0rc1*

- **humanize** *3.2.0*

- **icecream** *2.0.0*

- **marshmallow** *3.10.0*

- **matplotlib** *3.3.3*

- **psutil** *5.8.0*

- **pyfiglet** *0.8.post1*

- **python_a2s** *1.3.0*

- **python_dotenv** *0.15.0*

- **pytz** *2020.5*

- **rich** *9.13.0*

- **tldextract** *3.1.0*

- **watchgod** *0.6*

- **webdavclient3** *3.14.5*


### External dependencies



---

## License

MIT

---

## Development



### Future Plans





---

## See also



### Links


- [A3 Antistasi Official Discord Server](https://discord.gg/8WNsueDKf5)


