

# Glossary

---


<details><summary><b><u>Cog</b></u></summary>
<br>

Container for Commands. Simplified it is a Discord class. As a class it is able to keep states.

__Inside a Cog there can be defined__:
* commands
* listener
* background loops

It is implemented in a way, that it gets loaded like a plug-in, therefore can be disabled, reloaded or unloaded easily.
Can also be seen as a kind of Category for commands. Each Cog has access to the bot itself and can therefore access bot attributes as well as other Cogs (in a complicated way).

</details>



---


<details><summary><b><u>Asyncio</b></u></summary>
<br>

Asynchronous code execution. It is the reason why the bot still responds even though there is a command already running.
Some awful implementation which makes code duplication almost mandatory. I may write more about it when I stop hating it like the devilspawn it is.

__asyncio function definition__:
```python
async def function_name(parameter_name):
    print(parameter_name)
    return parameter_name
```
__asyncio function call__:
```python
x = await function_name('I hate asyncio')
```

__stupid asyncio problems:__
* you can call normal functions from asyncio functions, but you cannot call asyncio functions from normal functions
* you should almost always look for a version of the package you want to use, that is written special for asyncio. (**aiohttp** vs. **requests**)
* if you call a normal function make sure it is not a long calculating one, as everything basically halts while it is executing.
* If you do have to, use
```python
x = await run_in_executor(normal_function_name, parameter_name)
```

* best to most often write the function or method as normal function and I will convert it to the astupido afterwards.

</details>



---


<details><summary><b><u>Listener</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Commands</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Background loop</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Checks</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Cooldowns</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Bot Support</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Context</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Embeds</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Presence</b></u></summary>
<br>

TODO

</details>



---


<details><summary><b><u>Intents</b></u></summary>
<br>

TODO

</details>



---

