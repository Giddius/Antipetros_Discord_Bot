# <p align="center">Antipetros Discordbot</p> #


<p align="center"><img src="misc/images/AntiPetros_for_readme.png" alt="Anti-Petros Avatar"/></p>


None


## Installation

still WiP





## Features ##

<details><summary><b>Currently usable Cogs</b></summary><blockquote>


### <p align="center">[AbsoluteTimeCog](d:/dropbox/hobby/modding/programs/github/my_repos/antipetros_discord_bot_new/.venv/lib/site-packages/antipetros_discordbot/cogs/general_cogs/absolute_time_cog.py)</p> ###

<details><summary><b>Description</b></summary>

<blockquote>The base class that all cogs must inherit from.

A cog is a collection of commands, listeners, and optional state to
help group commands together. More information on them can be found on
the :ref:`ext_commands_cogs` page.

When inheriting from this class, the options shown in :class:`CogMeta`
are equally valid here.</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- <ins>**REGISTER_TIMEZONE_CITY**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <in_data>
        ```
    <br>

- <ins>**TELL_ALL_REGISTERED_TIMEZONES**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**TO_ABSOLUTE_TIMES**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>


</blockquote>

</details>

---


### <p align="center">[AdministrationCog](d:/dropbox/hobby/modding/programs/github/my_repos/antipetros_discord_bot_new/.venv/lib/site-packages/antipetros_discordbot/cogs/admin_cogs/admin_cog.py)</p> ###

<details><summary><b>Description</b></summary>

<blockquote>The base class that all cogs must inherit from.

A cog is a collection of commands, listeners, and optional state to
help group commands together. More information on them can be found on
the :ref:`ext_commands_cogs` page.

When inheriting from this class, the options shown in :class:`CogMeta`
are equally valid here.</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- <ins>**ADD_TO_BLACKLIST**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <user_id>
        ```
    <br>

- <ins>**CONFIG_REQUEST**</ins>
    - **aliases:** *send_config*
    - **checks:** *dm_only*
    - **signature:**
        ```diff
        [config_name=all]
        ```
    <br>

- <ins>**DELETE_MSG**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <msg_id>
        ```
    <br>

- <ins>**LIST_CONFIGS**</ins>

    - **checks:** *dm_only*
    <br>

- <ins>**MAKE_FEATURE_SUGGESTION**</ins>


    - **signature:**
        ```diff
        <message>
        ```
    <br>

- <ins>**OVERWRITE_CONFIG_FROM_FILE**</ins>
    - **aliases:** *overwrite_config*
    - **checks:** *dm_only*
    - **signature:**
        ```diff
        <config_name>
        ```
    <br>

- <ins>**RELOAD_ALL_EXT**</ins>
    - **aliases:** *reload_all*, *reload*
    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**REMOVE_FROM_BLACKLIST**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <user_id>
        ```
    <br>

- <ins>**SHOW_COMMAND_NAMES**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**SHUTDOWN**</ins>
    - **aliases:** *go_away*, *close*, *die*, *exit*, *turn_of*
    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**TELL_UPTIME**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**WRITE_DATA**</ins>

    - **checks:** *in_allowed_channels*, *is_owner*
    <br>


</blockquote>

</details>

---


### <p align="center">[GeneralDebugCog](d:/dropbox/hobby/modding/programs/github/my_repos/antipetros_discord_bot_new/.venv/lib/site-packages/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py)</p> ###

<details><summary><b>Description</b></summary>

<blockquote>The base class that all cogs must inherit from.

A cog is a collection of commands, listeners, and optional state to
help group commands together. More information on them can be found on
the :ref:`ext_commands_cogs` page.

When inheriting from this class, the options shown in :class:`CogMeta`
are equally valid here.</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- <ins>**MULTIPLE_QUOTES**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [amount=10]
        ```
    <br>

- <ins>**QUOTE**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**ROLL**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [target_time=1]
        ```
    <br>


</blockquote>

</details>

---


### <p align="center">[ImageManipulatorCog](d:/dropbox/hobby/modding/programs/github/my_repos/antipetros_discord_bot_new/.venv/lib/site-packages/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py)</p> ###

<details><summary><b>Description</b></summary>

<blockquote>The base class that all cogs must inherit from.

A cog is a collection of commands, listeners, and optional state to
help group commands together. More information on them can be found on
the :ref:`ext_commands_cogs` page.

When inheriting from this class, the options shown in :class:`CogMeta`
are equally valid here.</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- <ins>**AVAILABLE_STAMPS**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**OTHER_MEMBERS_AVATAR**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [members]...
        ```
    <br>

- <ins>**STAMP_IMAGE**</ins>
    - **aliases:** *antistasify*
    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [stamp=ASLOGO1] [first_pos=bottom] [second_pos=right] [factor]
        ```
    <br>


</blockquote>

</details>

---


### <p align="center">[PerformanceCog](d:/dropbox/hobby/modding/programs/github/my_repos/antipetros_discord_bot_new/.venv/lib/site-packages/antipetros_discordbot/cogs/admin_cogs/performance_cog.py)</p> ###

<details><summary><b>Description</b></summary>

<blockquote>The base class that all cogs must inherit from.

A cog is a collection of commands, listeners, and optional state to
help group commands together. More information on them can be found on
the :ref:`ext_commands_cogs` page.

When inheriting from this class, the options shown in :class:`CogMeta`
are equally valid here.</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- <ins>**GET_COMMAND_STATS**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**REPORT**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>

- <ins>**REPORT_LATENCY**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [with_graph=True] [since_last_hours=24]
        ```
    <br>

- <ins>**REPORT_MEMORY**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [with_graph=True] [since_last_hours=24]
        ```
    <br>


</blockquote>

</details>

---


### <p align="center">[PurgeMessagesCog](d:/dropbox/hobby/modding/programs/github/my_repos/antipetros_discord_bot_new/.venv/lib/site-packages/antipetros_discordbot/cogs/admin_cogs/purge_messages_cog.py)</p> ###

<details><summary><b>Description</b></summary>

<blockquote>The base class that all cogs must inherit from.

A cog is a collection of commands, listeners, and optional state to
help group commands together. More information on them can be found on
the :ref:`ext_commands_cogs` page.

When inheriting from this class, the options shown in :class:`CogMeta`
are equally valid here.</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- <ins>**PURGE_ANTIPETROS**</ins>

    - **checks:** *in_allowed_channels*, *is_owner*
    - **signature:**
        ```diff
        [and_giddi] [number_of_messages=1000]
        ```
    <br>


</blockquote>

</details>

---


### <p align="center">[SaveLinkCog](d:/dropbox/hobby/modding/programs/github/my_repos/antipetros_discord_bot_new/.venv/lib/site-packages/antipetros_discordbot/cogs/general_cogs/save_link_cog.py)</p> ###

<details><summary><b>Description</b></summary>

<blockquote>An extension Cog to let users temporary save links.

Saved links get posted to a certain channel and deleted after the specified time period from that channel (default in config).
Deleted links are kept in the bots database and can always be retrieved by fuzzy matched name.

Checks against a blacklist of urls and a blacklist of words, to not store malicious links.</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- <ins>**ADD_FORBIDDEN_WORD**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <word>
        ```
    <br>

- <ins>**CLEAR_ALL_LINKS**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [sure=False]
        ```
    <br>

- <ins>**DELETE_LINK**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <name> [scope=channel]
        ```
    <br>

- <ins>**GET_ALL_LINKS**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [in_format=txt]
        ```
    <br>

- <ins>**GET_FORBIDDEN_LIST**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [file_format=json]
        ```
    <br>

- <ins>**GET_LINK**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <name>
        ```
    <br>

- <ins>**REMOVE_FORBIDDEN_WORD**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <word>
        ```
    <br>

- <ins>**SAVE_LINK**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        <link> [link_name] [days_to_hold]
        ```
    <br>


</blockquote>

</details>

---


### <p align="center">[SaveSuggestionCog](d:/dropbox/hobby/modding/programs/github/my_repos/antipetros_discord_bot_new/.venv/lib/site-packages/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py)</p> ###

<details><summary><b>Description</b></summary>

<blockquote>The base class that all cogs must inherit from.

A cog is a collection of commands, listeners, and optional state to
help group commands together. More information on them can be found on
the :ref:`ext_commands_cogs` page.

When inheriting from this class, the options shown in :class:`CogMeta`
are equally valid here.</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- <ins>**AUTO_ACCEPT_SUGGESTIONS**</ins>

    - **checks:** *dm_only*
    <br>

- <ins>**CLEAR_ALL_SUGGESTIONS**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [sure=False]
        ```
    <br>

- <ins>**GET_ALL_SUGGESTIONS**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [report_template=basic_report.html.jinja]
        ```
    <br>

- <ins>**MARK_DISCUSSED**</ins>

    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [suggestion_ids...]
        ```
    <br>

- <ins>**REMOVE_ALL_USERDATA**</ins>
    - **aliases:** *remove_all_my_data*
    - **checks:** *dm_only*
    <br>

- <ins>**REQUEST_MY_DATA**</ins>

    - **checks:** *dm_only*
    <br>

- <ins>**USER_DELETE_SUGGESTION**</ins>
    - **aliases:** *unsave_suggestion*
    - **checks:** *dm_only*
    - **signature:**
        ```diff
        <suggestion_id>
        ```
    <br>


</blockquote>

</details>

---

</blockquote></details>

## Dependencies ##

***Currently only tested on Windows***

**Developed with Python Version `3.9.1`**

- google_auth_oauthlib<=`0.4.2`
- networkx<=`2.5`
- watchgod<=`0.6`
- matplotlib<=`3.3.3`
- WeasyPrint<=`52.2`
- aiohttp<=`3.6.3`
- pytz<=`2020.5`
- Jinja2<=`2.11.2`
- psutil<=`5.8.0`
- pyfiglet<=`0.8.post1`
- fuzzywuzzy<=`0.18.0`
- async_property<=`0.2.1`
- click<=`7.1.2`
- googletrans<=`4.0.0rc1`
- pdfkit<=`0.6.1`
- dpytest<=`0.0.22`
- graphviz<=`0.16`
- pyowm<=`3.1.1`
- discord<=`1.0.1`
- gidappdata<=`0.1.1`
- gidlogger<=`0.1.3`
- google_api_python_client<=`1.12.8`
- Pillow<=`8.1.0`
- protobuf<=`3.14.0`
- PyQt5<=`5.15.2`
- python-dotenv<=`0.15.0`
- udpy<=`2.0.0`





## License

MIT

## Development


### Todo ###

<details><summary><b>TODOS FROM CODE</b></summary>

#### todo [admin_cog.py](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py): ####


- [ ] [admin_cog.py line 60:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L60) `get_logs command`


- [ ] [admin_cog.py line 61:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L61) `get_appdata_location command`


- [ ] [admin_cog.py line 250:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L250) `make as embed`


- [ ] [admin_cog.py line 256:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L256) `make as embed`


- [ ] [admin_cog.py line 265:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L265) `make as embed`


- [ ] [admin_cog.py line 271:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L271) `make as embed`


- [ ] [admin_cog.py line 277:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L277) `make as embed`


- [ ] [admin_cog.py line 284:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L284) `CRITICAL ! CHANGE TO SAVE TO JSON AND MAKE BOT METHOD FOR SAVING BLACKLIST JSON FILE`


- [ ] [admin_cog.py line 287:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L287) `make as embed`


- [ ] [admin_cog.py line 291:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L291) `make as embed`


- [ ] [admin_cog.py line 299:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L299) `make as embed`


- [ ] [admin_cog.py line 302:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L302) `make as embed`


- [ ] [admin_cog.py line 304:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L304) `make as embed`


- [ ] [admin_cog.py line 314:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L314) `make as embed`


- [ ] [admin_cog.py line 319:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L319) `make as embed`


- [ ] [admin_cog.py line 331:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L331) `make as embed`


- [ ] [admin_cog.py line 334:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L334) `make as embed`


- [ ] [admin_cog.py line 336:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L336) `make as embed`


- [ ] [admin_cog.py line 347:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L347) `make as embed`


---


#### todo [performance_cog.py](/antipetros_discordbot/cogs/admin_cogs/performance_cog.py): ####


- [ ] [performance_cog.py line 65:](/antipetros_discordbot/cogs/admin_cogs/performance_cog.py#L65) `get_logs command`


- [ ] [performance_cog.py line 66:](/antipetros_discordbot/cogs/admin_cogs/performance_cog.py#L66) `get_appdata_location command`


- [ ] [performance_cog.py line 155:](/antipetros_discordbot/cogs/admin_cogs/performance_cog.py#L155) `limit amount of saved data, maybe archive it`


---


#### todo [purge_messages_cog.py](/antipetros_discordbot/cogs/admin_cogs/purge_messages_cog.py): ####


- [ ] [purge_messages_cog.py line 66:](/antipetros_discordbot/cogs/admin_cogs/purge_messages_cog.py#L66) `get_logs command`


- [ ] [purge_messages_cog.py line 67:](/antipetros_discordbot/cogs/admin_cogs/purge_messages_cog.py#L67) `get_appdata_location command`


---


#### todo [general_debug_cog.py](/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py): ####


- [ ] [general_debug_cog.py line 55:](/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py#L55) `create regions for this file`


- [ ] [general_debug_cog.py line 56:](/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py#L56) `Document and Docstrings`


---


#### todo [image_manipulation_cog.py](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py): ####


- [ ] [image_manipulation_cog.py line 55:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L55) `create regions for this file`


- [ ] [image_manipulation_cog.py line 56:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L56) `Document and Docstrings`


- [ ] [image_manipulation_cog.py line 241:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L241) `make as embed`


- [ ] [image_manipulation_cog.py line 245:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L245) `make as embed`


- [ ] [image_manipulation_cog.py line 252:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L252) `make as embed`


- [ ] [image_manipulation_cog.py line 256:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L256) `maybe make extra attribute for input format, check what is possible and working. else make a generic format list`


- [ ] [image_manipulation_cog.py line 271:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L271) `make as embed`


---


#### todo [save_link_cog.py](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py): ####


- [ ] [save_link_cog.py line 52:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L52) `refractor 'get_forbidden_list' to not use temp directory but send as filestream or so`


- [ ] [save_link_cog.py line 54:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L54) `need help figuring out how to best check bad link or how to format/normalize it`


- [ ] [save_link_cog.py line 364:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L364) `refractor that monster of an function`


---


#### todo [save_suggestion_cog.py](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py): ####


- [ ] [save_suggestion_cog.py line 57:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L57) `create report generator in different formats, at least json and Html, probably also as embeds and Markdown`


- [ ] [save_suggestion_cog.py line 59:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L59) `Document and Docstrings`


- [ ] [save_suggestion_cog.py line 210:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L210) `make as embed`


- [ ] [save_suggestion_cog.py line 216:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L216) `make as embed`


- [ ] [save_suggestion_cog.py line 232:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L232) `make as embed`


- [ ] [save_suggestion_cog.py line 244:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L244) `make as embed`


- [ ] [save_suggestion_cog.py line 248:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L248) `make as embed`


- [ ] [save_suggestion_cog.py line 252:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L252) `make as embed`


- [ ] [save_suggestion_cog.py line 257:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L257) `make as embed`


- [ ] [save_suggestion_cog.py line 295:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L295) `make as embed`


- [ ] [save_suggestion_cog.py line 298:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L298) `make as embed`


- [ ] [save_suggestion_cog.py line 309:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L309) `make as embed`


- [ ] [save_suggestion_cog.py line 313:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L313) `make as embed`


- [ ] [save_suggestion_cog.py line 317:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L317) `make as embed`


- [ ] [save_suggestion_cog.py line 322:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L322) `make as embed`


- [ ] [save_suggestion_cog.py line 333:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L333) `make as embed`


- [ ] [save_suggestion_cog.py line 368:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L368) `make as embed`


- [ ] [save_suggestion_cog.py line 371:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L371) `make as embed`


- [ ] [save_suggestion_cog.py line 375:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L375) `make as embed`


---


#### idea [render_new_cog_file.py](/antipetros_discordbot/dev_tools/render_new_cog_file.py): ####


- [ ] [render_new_cog_file.py line 119:](/antipetros_discordbot/dev_tools/render_new_cog_file.py#L119) `create gui for this`


---


#### idea [antipetros_bot.py](/antipetros_discordbot/engine/antipetros_bot.py): ####


- [ ] [antipetros_bot.py line 65:](/antipetros_discordbot/engine/antipetros_bot.py#L65) `Use an assistant class to hold some of the properties and then use the __getattr__ to make it look as one object, just for structuring`


#### todo [antipetros_bot.py](/antipetros_discordbot/engine/antipetros_bot.py): ####


- [ ] [antipetros_bot.py line 63:](/antipetros_discordbot/engine/antipetros_bot.py#L63) `create regions for this file`


- [ ] [antipetros_bot.py line 64:](/antipetros_discordbot/engine/antipetros_bot.py#L64) `Document and Docstrings`


---


#### todo [sqldata_storager.py](/antipetros_discordbot/utility/sqldata_storager.py): ####


- [ ] [sqldata_storager.py line 35:](/antipetros_discordbot/utility/sqldata_storager.py#L35) `create regions for this file`


- [ ] [sqldata_storager.py line 36:](/antipetros_discordbot/utility/sqldata_storager.py#L36) `update save link Storage to newer syntax (composite access)`


- [ ] [sqldata_storager.py line 37:](/antipetros_discordbot/utility/sqldata_storager.py#L37) `Document and Docstrings`


- [ ] [sqldata_storager.py line 38:](/antipetros_discordbot/utility/sqldata_storager.py#L38) `refractor to subfolder`


---

### General Todos ###
</details>

