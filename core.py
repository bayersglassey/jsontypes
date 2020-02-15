from collections import namedtuple



JT_TAGS = {
    "any",
    "void",
    "undefined",
    "null",
    "boolean",
    "string",
    "number",
    "object",
    "array",
    "union",
}

JtNode = namedtuple("JtNode", ["tag", "data"])
JtNode.__new__.__defaults__ = ("void", None)


class Undefined:
    def __str__(self):
        return "undefined"
    def __repr__(self):
        return "undefined"
undefined = Undefined()
