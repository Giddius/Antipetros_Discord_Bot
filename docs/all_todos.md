# TODOs collected from files

## __main__.py

- [ ] [line 81:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/__main__.py#L81)  `way to convoluted, make it simpler look into better loggign frameworks.`
<br>

---

## aux_community_server_info_cog.py

- [ ] [line 137:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/auxiliary_classes/for_cogs/aux_community_server_info_cog.py#L137)  `Hardcode query_port to port +1`
<br>

---

## bot_supporter.py

- [ ] [line 73:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/bot_support/bot_supporter.py#L73)  `#     : Refactor so it is callable like cogs`
<br>

---

## blacklist_warden.py

- [ ] [line 130:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/bot_support/sub_support/blacklist_warden.py#L130)  `make embed`
<br>

---

## color_keeper.py

- [ ] [line 31:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/bot_support/sub_support/color_keeper.py#L31)  `redo this so it wont need all those values per color and maybe save it in the general db`
<br>

---

## embed_builder.py

- [ ] [line 250:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/bot_support/sub_support/embed_builder.py#L250)  `make custom error`
<br>

---

## error_handler.py

- [ ] [line 45:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/bot_support/sub_support/error_handler.py#L45)  `rebuild whole error handling system`
<br>
- [ ] [line 46:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/bot_support/sub_support/error_handler.py#L46)  `make it so that creating the embed also sends it, with more optional args`
<br>
- [ ] [line 48:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/bot_support/sub_support/error_handler.py#L48)  `Handlers needed: discord.ext.commands.errors.DisabledCommand,ParameterError,discord.ext.MissingRequiredArgument`
<br>
- [ ] [line 253:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/bot_support/sub_support/error_handler.py#L253)  `get normal sentence from BucketType, with dynamical stuff (user_name, channel_name,...)`
<br>

---

## community_server_info_cog.py

- [ ] [line 49:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/antistasi_tool_cogs/community_server_info_cog.py#L49)  `Refractor current online server out of method so it can be used with the loop and the command`
<br>

---

## github_cog.py

- [ ] [line 73:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/antistasi_tool_cogs/github_cog.py#L73)  `Transfer the classattribute urls into the config`
<br>

---

## steam_cog.py

- [ ] [line 33:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/antistasi_tool_cogs/steam_cog.py#L33)  `Add all special Cog methods`
<br>

---

## bot_admin_cog.py

- [ ] [line 275:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/bot_admin_cogs/bot_admin_cog.py#L275)  `make as embed`
<br>

---

## config_cog.py

- [ ] [line 39:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/bot_admin_cogs/config_cog.py#L39)  `get_logs command`
<br>
- [ ] [line 40:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/bot_admin_cogs/config_cog.py#L40)  `get_appdata_location command`
<br>

---

## performance_cog.py

- [ ] [line 45:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/bot_admin_cogs/performance_cog.py#L45)  `get_logs command`
<br>
- [ ] [line 46:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/bot_admin_cogs/performance_cog.py#L46)  `get_appdata_location command`
<br>
- [ ] [line 290:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/bot_admin_cogs/performance_cog.py#L290)  `make as error embed`
<br>

---

## general_debug_cog.py

- [ ] [line 80:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py#L80)  `create regions for this file`
<br>
- [ ] [line 81:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/dev_cogs/general_debug_cog.py#L81)  `Document and Docstrings`
<br>

---

## purge_messages_cog.py

- [ ] [line 36:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/discord_admin_cogs/purge_messages_cog.py#L36)  `Add all special Cog methods`
<br>

---

## image_manipulation_cog.py

- [ ] [line 44:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L44)  `create regions for this file`
<br>
- [ ] [line 45:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L45)  `Document and Docstrings`
<br>
- [ ] [line 213:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L213)  `make as embed`
<br>
- [ ] [line 217:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L217)  `make as embed`
<br>
- [ ] [line 224:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L224)  `make as embed`
<br>
- [ ] [line 228:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L228)  `maybe make extra attribute for input format, check what is possible and working. else make a generic format list`
<br>
- [ ] [line 244:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/image_manipulation_cog.py#L244)  `make as embed`
<br>

---

## info_cog.py

- [ ] [line 65:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/info_cog.py#L65)  `Docstring for all non command methods.`
<br>

---

## klim_bim_cog.py

- [ ] [line 366:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/klim_bim_cog.py#L366)  `Refractor this ugly mess`
<br>
- [ ] [line 418:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/klim_bim_cog.py#L418)  `Refractor this ugly mess`
<br>

---

## save_suggestion_cog.py

- [ ] [line 62:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L62)  `create report generator in different formats, at least json and Html, probably also as embeds and Markdown`
<br>
- [ ] [line 64:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L64)  `Document and Docstrings`
<br>
- [ ] [line 313:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L313)  `make as embed`
<br>
- [ ] [line 325:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L325)  `make as embed`
<br>
- [ ] [line 329:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L329)  `make as embed`
<br>
- [ ] [line 333:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L333)  `make as embed`
<br>
- [ ] [line 338:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L338)  `make as embed`
<br>
- [ ] [line 373:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L373)  `make as embed`
<br>
- [ ] [line 376:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L376)  `make as embed`
<br>
- [ ] [line 387:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L387)  `make as embed`
<br>
- [ ] [line 391:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L391)  `make as embed`
<br>
- [ ] [line 395:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L395)  `make as embed`
<br>
- [ ] [line 400:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L400)  `make as embed`
<br>
- [ ] [line 410:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L410)  `make as embed`
<br>
- [ ] [line 445:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L445)  `make as embed`
<br>
- [ ] [line 448:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L448)  `make as embed`
<br>
- [ ] [line 452:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/save_suggestion_cog.py#L452)  `make as embed`
<br>

---

## translate_cog.py

- [ ] [line 206:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/general_cogs/translate_cog.py#L206)  `Make embed with Hyperlink`
<br>

---

## subscription_cog.py

- [ ] [line 591:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/special_channels_cogs/subscription_cog.py#L591)  `Custom Error and handling`
<br>
- [ ] [line 596:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/cogs/special_channels_cogs/subscription_cog.py#L596)  `Custom Error and handling`
<br>

---

## antipetros_bot.py

- [ ] [line 70:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/engine/antipetros_bot.py#L70)  `create regions for this file`
<br>
- [ ] [line 71:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/engine/antipetros_bot.py#L71)  `Document and Docstrings`
<br>
- [ ] [line 395:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/engine/antipetros_bot.py#L395)  `How to make sure they are also correctly restarted, regarding all loops on the bot`
<br>
- [ ] [line 529:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/engine/antipetros_bot.py#L529)  `make dynamic`
<br>

---

## checks.py

- [ ] [line 189:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/utility/checks.py#L189)  `make as before invoke hook and not check!`
<br>

---

## misc.py

- [ ] [line 480:](https://github.com/official-antistasi-community/Antipetros_Discord_Bot/tree/command_and_cogs_refactoring/antipetros_discordbot/utility/misc.py#L480)  `Custom Error`
<br>

---

