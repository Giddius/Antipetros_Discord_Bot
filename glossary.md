

# Glossary

---

<h3><u>Cog</h3></u>

<details><summary></summary>
<br>

Container for Commands. Simplified it is a Discord class. As a class it is able to keep states.

__Inside a Cog there can be defined__:
- commands
- listener
- background loops

It is implemented in a way, that it gets loaded like a plugin, therefore can be disabled, reloaded or unloaded easily.
Can also be seen as a kind of Category for commands. Each Cog has access to the bot itself and can therefore access bot attributes as well as other Cogs (in a complicated way).

</details>


---

<h3><u>Asyncio</h3></u>

<details><summary></summary>
<br>

Asynchronus code excecution. It is the reason why the bot still responds even though there is a command already running.
Some aweful implementation which makes code duplication almost mandatory. I may write more about it when I stop hating it like the devilspawn it is.

__asnycio function definition__:
```py
async def function_name(parameter_name):
    print(parameter_name)
    return parameter_name
```
__asyncio function call__:
```py
x = await function_name('I hate asyncio')
```

__stupid asyncio problems:__
- you can call normal functions from asyncio functions, but you cannot call asyncio functions from normal functions
- you should almost always look for a version of the package you want to use, that is written specialy for asyncio. (**aiohttp** vs. **requests**)
- if you call a normal function make sure it is not a long calculating one, as everything basically halts while it is executing.
- If you do have to, use
```python
x = await run_in_executor(normal_function_name, parmeter_name)
```

- best to most often write the function or method as normal function and I will convert it to the astupido afterwards.


yay Cargo-culting

</details>


---

<h3><u>Listener</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Commands</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Background loop</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Checks</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Cooldowns</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Bot Support</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Context</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Embeds</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Presence</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

<h3><u>Intents</h3></u>

<details><summary></summary>
<br>

TODO

</details>


---

