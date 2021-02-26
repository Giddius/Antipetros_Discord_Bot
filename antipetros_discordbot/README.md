
## __**Foreword**__

I only recently started programming and never even wrote as much as a batch script. This fact combined with me mostly coding alone and teaching myself, led to some idiosyncrasies and special functions or classes that I use.

### **Why?**

When I don't completly understand an external package, I just try to recreate it from scratch the way I think it works. I don't want to work with magic Blackboxes that I can't fix if they fail. Often after "rebuilding" them and understanding them, I will switch over and use the actual package, but some times I prefer my implementation more and so keep it.

If some function has a clunky or (for me) weird and unusual behaviour, I sometimes create wrapper functions. This most often happens because what a function really does is ambigous or I always mix up the syntax and have to constantly look it up. Therefore I just wrap it in a way that is more natural to me.



***e.g.***

**The `os.path.splitext()` function, the name is ambigous enough and the fact it will return a tuple is not clear, that alternately think it either returns a clean file_name or a clean extension. That it returns the extension with the leading dot, also trips me up a lot.**

```python
import os

file_name = 'test_file.txt'

# What I most often expect:
os.path.splitext(file_name)
>>> 'txt'

# what really happens:
os.path.splitext(file_name)
>>> ('test_file', '.txt')


# what you often will see in my code
# explicitly spliting it
file_name.split('.')[-1]
>>> 'txt'

```




## Giddi's Idiosyncrasies

---

### pathmaker

Most often you will find `pathmaker('some_path', 'some_path_2)`. This is a wrapper over `os.path.join()`, with a few extras. The Big reason I use this and not `os.path.join()` is that `pathmaker()` always returns the path as a POSIX delimited path.
Windows actually can handle these paths (exception is in a batch file) and it makes interacting with them not only really cross-platform, but also more predictable. It also normalizes the path.

#### e.g.

```python

os.path.join("C:\User\Documents")
>>> C:\\User\\Documents

pathmaker("C:\User\Documents")
C:/User/Documents

```


#### source code:

```python

def pathmaker(first_segment, *in_path_segments, rev=False):
    """
    Normalizes input path or path fragments, replaces '\\' with '/' and combines fragments.

    Parameters
    ----------
    first_segment : str

    rev : bool, optional
        If 'True' reverts path back to Windows default, by default None

    Returns
    -------
    str
        New path from segments and normalized.
    """

    _path = first_segment

    _path = os.path.join(_path, *in_path_segments)
    if rev is True or sys.platform not in ['win32', 'linux']:
        return os.path.normpath(_path)
    return os.path.normpath(_path).replace(os.path.sep, '/')

```

#### possible future replacement

**pathlib**
I am currently working on my own inherited pathlib class, but the inheritance is sadly broken for pathlib right now and so it stalled.



## Differences to vanilla [Discord.py](https://discordpy.readthedocs.io/en/latest/)