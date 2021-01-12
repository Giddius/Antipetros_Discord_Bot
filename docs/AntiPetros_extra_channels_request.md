# AntiPetros Extra Channels Request

<p align="center"><img src="../misc/images/AntiPetros_for_readme.png" alt="Anti-Petros Avatar"/></p>


## These are very broad request and I do not need them all right now. I split them into importance


---

### **Important for Core Commands**




- **<ins>suggestions</ins>**:

    ```python

    Needed for all suggestion save commands. Bot can save suggestions ,that are marked by an special emoji, to his Database.
    The user gets messaged per DM that his suggestion is saved and gets an option to unsave it (GDPR),
    also to auto accept it in the future and not get messaged again if an suggestion of his gets saved.

    ```

-  **<ins>any channel where you would want to save links for a certain time:</ins>**

    ```python

    The bot can save links via an command, he will save them in his database but also post them as an embed in an designated channel.
    After a specified time he will delete the embed to keep the channel fresh, but keep the link in his Database, where it can be retrieved via command.

    ```

-  **<ins>full-members:</ins>**

    ```python

    Needed for Antistasi avatar commmand.
    Provides an command to allow members to get an image that is their current avatar modified by an antistasi badge in the lower right.
    (see giddi avatar)

    ```

<p align="center"><img src="Giddi_Member_avatar.png" alt="Anti-Petros Avatar"/></p>

---

### **Would be Nice for Commands roughly finished**



-  **<ins>faq</ins>**

    ```python

    Plan is to use the bot to make the Faq items as embeds and also use an command (example: @Antipetros faq_you 12) to get the faq embed from everywhere.
    More so provides an command that generates new Faqs or edits old ones (with clean up)

    ```

-  **<ins>announcements</ins>**

    ```python

    Plan is to make the announcements as embeds, also to provide possible future automated (Webhooks? from Server?) announcements.
    There is already an command that can dynamically overlay text over an provided image, to make the announcments especially nice.
    (also can implement random text for stuff like "You know what to do with that tea and the convenient amount of sand just laying around.")

    ```

-  **<ins>any channel you want to selectively purge messages</ins>**

    ```python

    Bot has the ability to purge messages from specific users, in specific time frames or not.
    Or all messages containing images or all messages that do not have a certain format,...
    basically whatever kind of special selective purge you want I can implement it.

    ```

---

### **For Planned Future commands**



-  **<ins>art team channels</ins>**

    ```python

    As the bot can dynamically add watermarks and also overlay text, it can be very usefull for the art team in that regard.

    ```

-  **<ins>bug-report-gameplay-feedback</ins>**

    ```python

    Can implement the same feature as with suggestions.
    Also I can run a questioneer on all posted feedback, that ask for vital info like server, version, mods
    and afterwards edits the users post to include it (unsure) or appands an message with that info.
    Would need to have new feedback somehow marked (example beginning with "# new feedback") to differentiate between discussion and new feedback.

    ```

-  **<ins>server-status</ins>**

    ```python

    Creating embeds as status, and also possible automation in the future.

    ```

-  **<ins>server-rules</ins>**

    ```python

    Same as with faq

    ```


-  **<ins>team-roster</ins>**

    ```python

    It would be very easy to keep the roster up to date by just querying the user with those roles.

    ```

-  **<ins>any channel you want the user to be able to contact admins filtered by the bot</ins>**

    ```python

    The way this works the user uses the command (example)
    | @Call request_server_restart |
    , the bot will then ask the user if the game is saved and everything is ready and if it is
    -> The bot will go through the list of admins currently online and from an internal hierachy will select the top most online one and message only him.
    If he does not answer with "accept" in certain minutes the bot will delete the message and go to the next on the list.
    The bot will also relay all info gathered from the user.

    This could be done with more interactions between admin and user and could speed up the process and make it less painfull for both sides.
    can use pagination see :

    ```
<p align="center"><img src="aSgIG.png" alt="Anti-Petros Avatar"/></p>

---

### **Misc**

- **<ins>Data</ins>**

    ```python
    Bot currently collects usage data (as simple integers) of all channels and can already provide a heat map for channel usage, just an fyi
    ```