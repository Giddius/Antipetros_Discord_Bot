

class VersionItem:
    separator_char = '.'

    def __init__(self, major: int, minor: int, patch: int) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def from_string(cls, version_string):
        major, minor, patch = map(int, version_string.strip().split(cls.separator_char))
        return cls(major=major, minor=minor, patch=patch)

    def __str__(self):
        return self.separator_char.join(map(str, [self.major, self.minor, self.patch]))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.major}, {self.minor}, {self.patch})"
