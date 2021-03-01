# <p align="center">Antipetros Discordbot</p> #


<p align="center"><img src="art/finished/images/AntiPetros_for_readme.png" alt="Anti-Petros Avatar"/></p>


Placeholder Description for AntiPetros DiscordBot


if you want to suggest and feature or an idea for a new command

> Use the command -->

```shell
@AntiPetros new_feature [YOUR SUGGESTION TEXT]
```

You can even attach images to the suggestion.



## Installation
### Via PyPi

Use the following command with pip:

```cmd
pip install antipetros_discordbot==0.1.11
```







## Features ##

<details><summary><b>Currently usable Cogs</b></summary><blockquote>


### <p align="center"><b>[ImageManipulatorCog](antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py)</b></p> ###

<details><summary><b>Description</b></summary>

<blockquote>Soon</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- **AVAILABLE_STAMPS**

    - **aliases:** *availablestamps*, *available-stamps*, *available.stamps*
    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>
- **MAP_CHANGED**

    - **aliases:** *map.changed*, *map-changed*, *mapchanged*
    - **checks:** *allowed_channel_and_allowed_role*
    - **signature:**
        ```diff
        <marker> <color>
        ```
    <br>
- **MEMBER_AVATAR**

    - **aliases:** *memberavatar*, *member.avatar*, *member-avatar*
    - **checks:** *in_allowed_channels*, *has_any_role*
    <br>
- **STAMP_IMAGE**

    - **aliases:** *stampimage*, *antistasify*, *stamp-image*, *stamp.image*
    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [stamp=ASLOGO1] [first_pos=bottom] [second_pos=right] [factor]
        ```
    <br>

</blockquote>

</details>

---


### <p align="center"><b>[KlimBimCog](antipetros_discordbot/cogs/general_cogs/klimbim_cog.py)</b></p> ###

<details><summary><b>Description</b></summary>

<blockquote>Soon</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- **FLIP_COIN**

    - **aliases:** *flip*, *flip-coin*, *flip.coin*, *flipcoin*
    - **checks:** *allowed_channel_and_allowed_role*
    <br>
- **MAKE_FIGLET**

    - **aliases:** *makefiglet*, *make-figlet*, *make.figlet*
    - **checks:** *allowed_channel_and_allowed_role*
    - **signature:**
        ```diff
        <text>
        ```
    <br>
- **THE_DRAGON**

    - **aliases:** *the-dragon*, *the.dragon*, *thedragon*
    - **checks:** *allowed_channel_and_allowed_role*
    <br>
- **URBAN_DICTIONARY**


    - **checks:** *allowed_channel_and_allowed_role*
    - **signature:**
        ```diff
        <term>
        ```
    <br>

</blockquote>

</details>

---


### <p align="center"><b>[SaveSuggestionCog](antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py)</b></p> ###

<details><summary><b>Description</b></summary>

<blockquote>Soon</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- **AUTO_ACCEPT_SUGGESTIONS**

    - **aliases:** *auto.accept.suggestions*, *auto-accept-suggestions*, *autoacceptsuggestions*
    - **checks:** *dm_only*
    <br>
- **CLEAR_ALL_SUGGESTIONS**

    - **aliases:** *clearallsuggestions*, *clear.all.suggestions*, *clear-all-suggestions*
    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [sure=False]
        ```
    <br>
- **GET_ALL_SUGGESTIONS**

    - **aliases:** *getallsuggestions*, *get-all-suggestions*, *get.all.suggestions*
    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [report_template=basic_report.html.jinja]
        ```
    <br>
- **MARK_DISCUSSED**

    - **aliases:** *mark.discussed*, *mark-discussed*, *markdiscussed*
    - **checks:** *in_allowed_channels*, *has_any_role*
    - **signature:**
        ```diff
        [suggestion_ids...]
        ```
    <br>
- **REMOVE_ALL_USERDATA**

    - **aliases:** *remove.all.my.data*, *removeallmydata*, *remove-all-userdata*, *removealluserdata*, *remove-all-my-data*, *remove.all.userdata*
    - **checks:** *dm_only*
    <br>
- **REQUEST_MY_DATA**

    - **aliases:** *requestmydata*, *request-my-data*, *request.my.data*
    - **checks:** *dm_only*
    <br>
- **USER_DELETE_SUGGESTION**

    - **aliases:** *unsavesuggestion*, *user.delete.suggestion*, *unsave.suggestion*, *unsave-suggestion*, *user-delete-suggestion*, *userdeletesuggestion*
    - **checks:** *dm_only*
    - **signature:**
        ```diff
        <suggestion_id>
        ```
    <br>

</blockquote>

</details>

---


### <p align="center"><b>[TranslateCog](antipetros_discordbot/cogs/general_cogs/translate_cog.py)</b></p> ###

<details><summary><b>Description</b></summary>

<blockquote>Soon</blockquote>

</details>

<details><summary><b>Commands</b></summary><blockquote>

- **TRANSLATE**
    ```diff
    + Translates text into multiple different languages.
    ```


    - **checks:** *allowed_channel_and_allowed_role*
    - **signature:**
        ```diff
        [to_language_id=english] <text_to_translate>
        ```
    <br>

</blockquote>

</details>

---

</blockquote></details>

## Dependencies ##

***Currently only tested on Windows***

**Developed with Python Version `3.9.1`**

- Jinja2<=`2.11.2`
- googletrans<=`4.0.0rc1`
- icecream<=`2.0.0`
- aiohttp<=`3.7.3`
- watchgod<=`0.6`
- emoji<=`1.1.0`
- discord_flags<=`2.1.1`
- cryptography<=`3.3.1`
- WeasyPrint<=`52.2`
- fuzzywuzzy<=`0.18.0`
- matplotlib<=`3.3.3`
- psutil<=`5.8.0`
- marshmallow<=`3.10.0`
- arrow<=`0.17.0`
- dateparser<=`1.0.0`
- humanize<=`3.2.0`
- pyfiglet<=`0.8.post1`
- async_property<=`0.2.1`
- click<=`7.1.2`
- pytz<=`2020.5`
- antistasi_template_checker<=`0.1.1`
- discord<=`1.0.1`
- gidappdata<=`0.1.8`
- gidlogger<=`0.1.7`
- Pillow<=`8.1.0`
- python-dotenv<=`0.15.0`
- udpy<=`2.0.0`


## See also
- [Antistasi Discord Invite](https://discord.gg/m7e792Kg)
- [Antistasi Website](https://a3antistasi.enjin.com/)



## License

MIT

## Development


### Todo ###

<details><summary><b>TODOS FROM CODE</b></summary>

#### todo [\_\_main\_\_.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/__main__.py): ####


- [ ] [\_\_main\_\_.py line 43:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/__main__.py#L43) `create prompt for token, with save option`


---


#### todo [blacklist_warden.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/bot_support/sub_support/blacklist_warden.py): ####


- [ ] [blacklist_warden.py line 140:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/bot_support/sub_support/blacklist_warden.py#L140) `make embed`


---


#### todo [error_handler.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/bot_support/sub_support/error_handler.py): ####


- [ ] [error_handler.py line 36:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/bot_support/sub_support/error_handler.py#L36) `rebuild whole error handling system`


- [ ] [error_handler.py line 37:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/bot_support/sub_support/error_handler.py#L37) `make it so that creating the embed also sends it, with more optional args`


---


#### todo [admin_cog.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/admin_cog.py): ####


- [ ] [admin_cog.py line 37:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L37) `get_logs command`


- [ ] [admin_cog.py line 38:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L38) `get_appdata_location command`


- [ ] [admin_cog.py line 195:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L195) `make as embed`


- [ ] [admin_cog.py line 220:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L220) `make as embed`


---


#### todo [config_cog.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py): ####


- [ ] [config_cog.py line 37:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py#L37) `get_logs command`


- [ ] [config_cog.py line 38:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py#L38) `get_appdata_location command`


- [ ] [config_cog.py line 184:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py#L184) `make as embed`


- [ ] [config_cog.py line 190:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py#L190) `make as embed`


- [ ] [config_cog.py line 199:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py#L199) `make as embed`


- [ ] [config_cog.py line 207:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py#L207) `make as embed`


- [ ] [config_cog.py line 213:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py#L213) `make as embed`


- [ ] [config_cog.py line 285:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/config_cog.py#L285) `make as embed`


---


#### todo [performance_cog.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/performance_cog.py): ####


- [ ] [performance_cog.py line 41:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/performance_cog.py#L41) `get_logs command`


- [ ] [performance_cog.py line 42:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/performance_cog.py#L42) `get_appdata_location command`


- [ ] [performance_cog.py line 136:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/performance_cog.py#L136) `limit amount of saved data, maybe archive it`


---


#### todo [purge_messages_cog.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/purge_messages_cog.py): ####


- [ ] [purge_messages_cog.py line 28:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/purge_messages_cog.py#L28) `get_logs command`


- [ ] [purge_messages_cog.py line 29:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/admin_cogs/purge_messages_cog.py#L29) `get_appdata_location command`


---


#### todo [general_debug_cog.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py): ####


- [ ] [general_debug_cog.py line 48:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py#L48) `create regions for this file`


- [ ] [general_debug_cog.py line 49:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py#L49) `Document and Docstrings`


---


#### todo [image_manipulation_cog.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py): ####


- [ ] [image_manipulation_cog.py line 54:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L54) `create regions for this file`


- [ ] [image_manipulation_cog.py line 55:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L55) `Document and Docstrings`


- [ ] [image_manipulation_cog.py line 245:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L245) `make as embed`


- [ ] [image_manipulation_cog.py line 249:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L249) `make as embed`


- [ ] [image_manipulation_cog.py line 256:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L256) `make as embed`


- [ ] [image_manipulation_cog.py line 260:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L260) `maybe make extra attribute for input format, check what is possible and working. else make a generic format list`


- [ ] [image_manipulation_cog.py line 275:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L275) `make as embed`


---


#### todo [save_link_cog.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_link_cog.py): ####


- [ ] [save_link_cog.py line 35:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L35) `refractor 'get_forbidden_list' to not use temp directory but send as filestream or so`


- [ ] [save_link_cog.py line 37:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L37) `need help figuring out how to best check bad link or how to format/normalize it`


- [ ] [save_link_cog.py line 372:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L372) `refractor that monster of an function`


---


#### todo [save_suggestion_cog.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py): ####


- [ ] [save_suggestion_cog.py line 57:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L57) `create report generator in different formats, at least json and Html, probably also as embeds and Markdown`


- [ ] [save_suggestion_cog.py line 59:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L59) `Document and Docstrings`


- [ ] [save_suggestion_cog.py line 199:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L199) `make as embed`


- [ ] [save_suggestion_cog.py line 205:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L205) `make as embed`


- [ ] [save_suggestion_cog.py line 220:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L220) `make as embed`


- [ ] [save_suggestion_cog.py line 232:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L232) `make as embed`


- [ ] [save_suggestion_cog.py line 236:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L236) `make as embed`


- [ ] [save_suggestion_cog.py line 240:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L240) `make as embed`


- [ ] [save_suggestion_cog.py line 245:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L245) `make as embed`


- [ ] [save_suggestion_cog.py line 281:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L281) `make as embed`


- [ ] [save_suggestion_cog.py line 284:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L284) `make as embed`


- [ ] [save_suggestion_cog.py line 295:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L295) `make as embed`


- [ ] [save_suggestion_cog.py line 299:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L299) `make as embed`


- [ ] [save_suggestion_cog.py line 303:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L303) `make as embed`


- [ ] [save_suggestion_cog.py line 308:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L308) `make as embed`


- [ ] [save_suggestion_cog.py line 318:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L318) `make as embed`


- [ ] [save_suggestion_cog.py line 353:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L353) `make as embed`


- [ ] [save_suggestion_cog.py line 356:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L356) `make as embed`


- [ ] [save_suggestion_cog.py line 360:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L360) `make as embed`


---


#### idea [render_new_cog_file.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/dev_tools_and_scripts/render_new_cog_file.py): ####


- [ ] [render_new_cog_file.py line 72:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/dev_tools_and_scripts/render_new_cog_file.py#L72) `create gui for this`


---


#### idea [antipetros_bot.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/engine/antipetros_bot.py): ####


- [ ] [antipetros_bot.py line 58:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/engine/antipetros_bot.py#L58) `Use an assistant class to hold some of the properties and then use the __getattr__ to make it look as one object, just for structuring`


#### todo [antipetros_bot.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/engine/antipetros_bot.py): ####


- [ ] [antipetros_bot.py line 56:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/engine/antipetros_bot.py#L56) `create regions for this file`


- [ ] [antipetros_bot.py line 57:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/engine/antipetros_bot.py#L57) `Document and Docstrings`


---


#### todo [sqldata_storager.py](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/utility/sqldata_storager.py): ####


- [ ] [sqldata_storager.py line 36:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/utility/sqldata_storager.py#L36) `create regions for this file`


- [ ] [sqldata_storager.py line 37:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/utility/sqldata_storager.py#L37) `update save link Storage to newer syntax (composite access)`


- [ ] [sqldata_storager.py line 38:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/utility/sqldata_storager.py#L38) `Document and Docstrings`


- [ ] [sqldata_storager.py line 39:](D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antipetros_Discord_Bot_new/antipetros_discordbot/utility/sqldata_storager.py#L39) `refractor to subfolder`


---

### General Todos ###
</details>

