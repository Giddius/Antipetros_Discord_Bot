# <p align="center">Anti-Petros Discord Bot</p> #


<p align="center"><img src="misc/images/AntiPetros_for_readme.png" alt="Anti-Petros Avatar"/></p>


None


## Installation

still WiP





## Features ##

<details><summary><b>Currently usable Cogs</b></summary><blockquote>


### <p align="center">[Administration](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py)</p> ###

<details><summary><b>Description</b></summary><blockquote>

    None

</blockquote></details>

<details><summary><b>Commands</b></summary><blockquote>

- > add_to_blacklist

- > delete_msg

- > die

- > list_configs

- > overwrite_config

- > reload_all

- > remove_from_blacklist

- > send_config

- > tell_uptime

</blockquote></details>

---


### <p align="center">[GeneralDebug](/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py)</p> ###

<details><summary><b>Description</b></summary><blockquote>

    None

</blockquote></details>

<details><summary><b>Commands</b></summary><blockquote>

- > all_info_from_command_trigger

- > channel_name

- > guild

- > is_a_channel

- > last_message

- > members_list

- > message_by_id

</blockquote></details>

---


### <p align="center">[ImageManipulator](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py)</p> ###

<details><summary><b>Description</b></summary><blockquote>

    None

</blockquote></details>

<details><summary><b>Commands</b></summary><blockquote>

- > antistasify

- > available_stamps

- > member_avatar

</blockquote></details>

---


### <p align="center">[SaveLink](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py)</p> ###

<details><summary><b>Description</b></summary><blockquote>

    
An extension Cog to let users temporary save links.

Saved links get posted to a certain channel and deleted after the specified time period from that channel (default in config).
Deleted links are kept in the bots database and can always be retrieved by fuzzy matched name.

Checks against a blacklist of urls and a blacklist of words, to not store malicious links.

cogs_config.ini section: self.config_name



</blockquote></details>

<details><summary><b>Commands</b></summary><blockquote>

- > add_forbidden_word

- > clear_all_links

- > delete_link

- > get_all_links

- > get_forbidden_list

- > get_link

- > remove_forbidden_word

- > save_link

</blockquote></details>

---


### <p align="center">[SaveSuggestion](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py)</p> ###

<details><summary><b>Description</b></summary><blockquote>

    None

</blockquote></details>

<details><summary><b>Commands</b></summary><blockquote>

- > auto_accept_suggestions

- > clear_all_suggestions

- > get_all_suggestions

- > mark_discussed

- > remove_all_my_data

- > request_my_data

- > unsave_suggestion

</blockquote></details>

---


### <p align="center">[TestPlayground](/antipetros_discordbot/cogs/general_cogs/test_playground_cog.py)</p> ###

<details><summary><b>Description</b></summary><blockquote>

    None

</blockquote></details>

<details><summary><b>Commands</b></summary><blockquote>

- > big_message

- > changesettings

- > check_md_helper

- > check_md_helper_specific

- > embed_experiment

- > furthermore_do_you_want_to_say_something

- > map_changed

- > request_server_restart

- > roll

</blockquote></details>

---

</blockquote></details>

## Dependencies ##

***Currently only tested on Windows***

**Developed with Python Version `3.8.6`**

- async_property<=`0.2.1`
- fuzzywuzzy<=`0.18.0`
- Jinja2<=`2.11.2`
- aiohttp<=`3.6.3`
- WeasyPrint<=`52.2`
- watchgod<=`0.6`
- dpytest<=`0.0.22`
- pdfkit<=`0.6.1`
- discord<=`1.0.1`
- gidlogger<=`0.1.2`
- Pillow<=`8.0.1`
- PyQt5<=`5.15.2`
- python-dotenv<=`0.15.0`





## License

MIT

## Development


### Todo ###

<details><summary><b>TODOS FROM CODE</b></summary>

#### todo [admin_cog.py](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py): ####


- [ ] [admin_cog.py line 185:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L185) `make as embed`


- [ ] [admin_cog.py line 208:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L208) `make as embed`


- [ ] [admin_cog.py line 227:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L227) `make as embed`


- [ ] [admin_cog.py line 233:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L233) `make as embed`


- [ ] [admin_cog.py line 243:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L243) `make as embed`


- [ ] [admin_cog.py line 249:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L249) `make as embed`


- [ ] [admin_cog.py line 255:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L255) `make as embed`


- [ ] [admin_cog.py line 265:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L265) `make as embed`


- [ ] [admin_cog.py line 269:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L269) `make as embed`


- [ ] [admin_cog.py line 277:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L277) `make as embed`


- [ ] [admin_cog.py line 280:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L280) `make as embed`


- [ ] [admin_cog.py line 282:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L282) `make as embed`


- [ ] [admin_cog.py line 292:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L292) `make as embed`


- [ ] [admin_cog.py line 297:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L297) `make as embed`


- [ ] [admin_cog.py line 309:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L309) `make as embed`


- [ ] [admin_cog.py line 312:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L312) `make as embed`


- [ ] [admin_cog.py line 314:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L314) `make as embed`


- [ ] [admin_cog.py line 325:](/antipetros_discordbot/cogs/admin_cogs/admin_cog.py#L325) `make as embed`


---


#### todo [general_debug_cog.py](/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py): ####


- [ ] [general_debug_cog.py line 48:](/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py#L48) `create regions for this file`


- [ ] [general_debug_cog.py line 49:](/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py#L49) `Document and Docstrings`


---


#### todo [image_manipulation_cog.py](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py): ####


- [ ] [image_manipulation_cog.py line 51:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L51) `create regions for this file`


- [ ] [image_manipulation_cog.py line 52:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L52) `Document and Docstrings`


- [ ] [image_manipulation_cog.py line 248:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L248) `make as embed`


- [ ] [image_manipulation_cog.py line 252:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L252) `make as embed`


- [ ] [image_manipulation_cog.py line 259:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L259) `make as embed`


- [ ] [image_manipulation_cog.py line 263:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L263) `maybe make extra attribute for input format, check what is possible and working. else make a generic format list`


- [ ] [image_manipulation_cog.py line 277:](/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L277) `make as embed`


---


#### todo [save_link_cog.py](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py): ####


- [ ] [save_link_cog.py line 60:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L60) `refractor 'get_forbidden_list' to not use temp directory but send as filestream or so`


- [ ] [save_link_cog.py line 62:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L62) `need help figuring out how to best check bad link or how to format/normalize it`


- [ ] [save_link_cog.py line 64:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L64) `check if everything is documented`


- [ ] [save_link_cog.py line 250:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L250) `make as embed`


- [ ] [save_link_cog.py line 261:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L261) `make as embed`


- [ ] [save_link_cog.py line 311:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L311) `make as embed`


- [ ] [save_link_cog.py line 321:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L321) `make as embed`


- [ ] [save_link_cog.py line 344:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L344) `refractor that monster of an function`


- [ ] [save_link_cog.py line 366:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L366) `make as embed`


- [ ] [save_link_cog.py line 391:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L391) `make as embed`


- [ ] [save_link_cog.py line 568:](/antipetros_discordbot/cogs/general_cogs/save_link_cog.py#L568) `Add logging`


---


#### todo [save_suggestion_cog.py](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py): ####


- [ ] [save_suggestion_cog.py line 53:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L53) `create report generator in different formats, at least json and Html, probably also as embeds and Markdown`


- [ ] [save_suggestion_cog.py line 55:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L55) `Document and Docstrings`


- [ ] [save_suggestion_cog.py line 211:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L211) `make as embed`


- [ ] [save_suggestion_cog.py line 217:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L217) `make as embed`


- [ ] [save_suggestion_cog.py line 232:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L232) `make as embed`


- [ ] [save_suggestion_cog.py line 244:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L244) `make as embed`


- [ ] [save_suggestion_cog.py line 248:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L248) `make as embed`


- [ ] [save_suggestion_cog.py line 252:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L252) `make as embed`


- [ ] [save_suggestion_cog.py line 257:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L257) `make as embed`


- [ ] [save_suggestion_cog.py line 297:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L297) `make as embed`


- [ ] [save_suggestion_cog.py line 300:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L300) `make as embed`


- [ ] [save_suggestion_cog.py line 311:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L311) `make as embed`


- [ ] [save_suggestion_cog.py line 315:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L315) `make as embed`


- [ ] [save_suggestion_cog.py line 319:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L319) `make as embed`


- [ ] [save_suggestion_cog.py line 324:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L324) `make as embed`


- [ ] [save_suggestion_cog.py line 334:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L334) `make as embed`


- [ ] [save_suggestion_cog.py line 369:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L369) `make as embed`


- [ ] [save_suggestion_cog.py line 372:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L372) `make as embed`


- [ ] [save_suggestion_cog.py line 376:](/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L376) `make as embed`


---


#### idea [render_new_cog_file.py](/antipetros_discordbot/dev_tools/render_new_cog_file.py): ####


- [ ] [render_new_cog_file.py line 116:](/antipetros_discordbot/dev_tools/render_new_cog_file.py#L116) `create gui for this`


---


#### idea [antipetros_bot.py](/antipetros_discordbot/engine/antipetros_bot.py): ####


- [ ] [antipetros_bot.py line 50:](/antipetros_discordbot/engine/antipetros_bot.py#L50) `Use an assistant class to hold some of the properties and then use the __getattr__ to make it look as one object, just for structuring`


#### todo [antipetros_bot.py](/antipetros_discordbot/engine/antipetros_bot.py): ####


- [ ] [antipetros_bot.py line 48:](/antipetros_discordbot/engine/antipetros_bot.py#L48) `create regions for this file`


- [ ] [antipetros_bot.py line 49:](/antipetros_discordbot/engine/antipetros_bot.py#L49) `Document and Docstrings`


---


#### todo [sqldata_storager.py](/antipetros_discordbot/utility/sqldata_storager.py): ####


- [ ] [sqldata_storager.py line 35:](/antipetros_discordbot/utility/sqldata_storager.py#L35) `create regions for this file`


- [ ] [sqldata_storager.py line 36:](/antipetros_discordbot/utility/sqldata_storager.py#L36) `update save link Storage to newer syntax (composite access)`


- [ ] [sqldata_storager.py line 37:](/antipetros_discordbot/utility/sqldata_storager.py#L37) `Document and Docstrings`


- [ ] [sqldata_storager.py line 38:](/antipetros_discordbot/utility/sqldata_storager.py#L38) `refractor to subfolder`


---

### General Todos ###
#### Bugs ####

- [ ] *important*: check everything for blocking functions and move big ones into threads (run in executor)


---

#### features ####

- [ ] *important*: create nice looking help command

- [ ] *important*: better docstrings and docstring all commands at least

- [ ] *important*: create all needed check methods

- [ ] *important*: move to gidappdata as storage

- [ ] *unimportant*: assign good names to the cogs as argument in the init

- [ ] *unimportant*: ask for symbols at art team


---

#### misc ####


---

#### tests ####


---

</details>

