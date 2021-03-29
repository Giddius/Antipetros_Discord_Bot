__**To implement a new INSTRUCTION that reacts to certain words in a message**__

use 
```css
@AntiPetros add_word_reaction_instruction [name of instruction] [word to react to] "[exceptions]" [emojis]
```
exceptions are always wrapped in `"` and are a semi-colon `;` seperated list of `type`,`id` seperated by an colon.
possible types are:
`user` --> do not trigger on message from the user with that id
`category` --> do not trigger in channels with that category id, example `DEVELOPMENT CORNER` is an category
`channel` --> do not trigger in channels with that id
`role` --> do not trigger for messages from users with that role.

**EXAMPLE**

```css
@AntiPetros add_word_reaction_instruction test_instruction antistasi "user,576522029470056450 ; channel,645930607683174401 ; category,820274917136269322 ; role,684643722335485999 ; role,509812769944502292 ; user,346595708180103170" 🤮 
```
This example would react with 🤮 to any mention of `antistasi`(case insensitive)

The example above would not trigger for:
1.) me as a user (my id is `576522029470056450`
2.) in bot-testing, its id is `645930607683174401`
3.) any channel in PR Lounge, its id is `820274917136269322`
4.) Any user that has the art team role, id `684643722335485999`
5.) Any user that has the Dev Team Lead role , id `509812769944502292`
6.) also not for Bob Murphy as his id is `346595708180103170`

you can add new exceptions by
```css
@AntiPetros add_exception_to_word_reaction_instruction [the name of the Instruction you want to modify] [type of exception] [id]
```