#!/bin/env python3

import json

from core import JtNode, undefined


class JsonType:
    """Parses JSON values, building up a schema which satisfies
    all of them.

    Feed it new values with the "add" method.

    At any time, see the schema it has built so far by calling
    the "show" method.

    Usage example:

        from jsontypes import JsonType
        p = JsonType()
        p.add({"a": 1, "b": [1, 2]})
        p.add({"a": 100, "b": None, "c": "Hello"})

        p.show()
        # ...Prints:
        #
        # object:
        #   "a": number
        #   "b": union:
        #     array:
        #       number
        #     null
        #   "c": union:
        #     undefined
        #     string

    """

    def __init__(self, *values, match_verbose=False, _jt=JtNode("void")):
        self.jt = _jt
        self.match_verbose = match_verbose
        for value in values:
            self.add(value)

    def __str__(self):
        return self.tostr()

    def tostr(self):
        return self.tostr_jt(self.jt, depth=0)

    def tostr_jt(self, jt, depth=0):
        """Returns str."""
        jt_tag = jt.tag
        if jt_tag == "array":
            sub_jt = jt.data
            sub_str = self.tostr_jt(sub_jt, depth+1)
            return "[{}]".format(sub_str)
        elif jt_tag == "object":
            jt_dict = jt.data
            sub_strs = []
            for key, sub_jt in jt_dict.items():
                prefix = json.dumps(key) + ": "
                sub_str = prefix + self.tostr_jt(sub_jt, depth+1)
                sub_strs.append(sub_str)
            return "{{{}}}".format(", ".join(sub_strs))
        elif jt_tag == "union":
            sub_jts = jt.data
            sub_strs = []
            for sub_jt in sub_jts:
                sub_str = self.tostr_jt(sub_jt, depth+1)
                sub_strs.append(sub_str)
            return " | ".join(sub_strs)
        else:
            return jt_tag

    def show(self):
        """Prints stuff and returns None."""
        self.show_jt(self.jt)

    def show_jt(self, jt, depth=0, prefix=""):
        """Prints stuff and returns None."""
        jt_tag = jt.tag
        tabs = "  " * depth
        if jt_tag == "array":
            sub_jt = jt.data
            print(tabs + prefix + "array:")
            self.show_jt(sub_jt, depth+1)
        elif jt_tag == "object":
            jt_dict = jt.data
            print(tabs + prefix + "object:")
            for key, sub_jt in jt_dict.items():
                prefix = json.dumps(key) + ": "
                self.show_jt(sub_jt, depth+1, prefix)
        elif jt_tag == "union":
            sub_jts = jt.data
            print(tabs + prefix + "union:")
            for sub_jt in sub_jts:
                self.show_jt(sub_jt, depth+1)
        else:
            print(tabs + prefix + jt_tag)

    def add(self, value):
        """Merges given value's type into self.jt.
        Returns None."""
        self.jt = self.merge_value(self.jt, value)

    def get_value_tag(self, v):
        """Returns str."""
        if v is undefined:
            # Kind of a hack to make matching work with objects
            return "undefined"
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "boolean"
        if isinstance(v, str):
            return "string"
        if isinstance(v, (int, float)):
            return "number"
        if isinstance(v, dict):
            return "object"
        if isinstance(v, (tuple, list)):
            return "array"
        raise TypeError("Unsupported type")

    def get_value_jt(self, value):
        """Returns the type of given value."""
        tag = self.get_value_tag(value)
        if tag == "array":
            sub_jt = JtNode("void")
            for sub_value in value:
                sub_jt = self.merge_value(sub_jt, sub_value)
            return JtNode("array", sub_jt)
        elif tag == "object":
            jt_dict = {}
            for key, sub_value in value.items():
                jt_dict[key] = self.get_value_jt(sub_value)
            return JtNode("object", jt_dict)
        else:
            return JtNode(tag)

    def merge_value(self, jt, value):
        """Merges the type of given value into jt.

        May modify jt and/or return it."""

        jt_tag = jt.tag

        # Any merged with some other thing is still any
        if jt_tag == "any":
            return jt

        # Void is always replaced by a real type
        if jt_tag == "void":
            return self.get_value_jt(value)

        # Unions are special
        if jt_tag == "union":
            return self.union_merge_value(jt, value)

        # Attempt a basic merge
        merged_jt = self._merge_value_core(jt, value)
        if merged_jt is not None:
            return merged_jt

        # They are different types, so return a union of them
        value_jt = self.get_value_jt(value)
        return JtNode("union", [jt, value_jt])

    def _merge_value_core(self, jt, value):
        """Shared logic of merge_value and union_merge_value.
        In particular, handles all the merge cases where we modify &
        return the same jt we were passed.

        Modifies & returns jt, or returns None."""

        jt_tag = jt.tag
        value_tag = self.get_value_tag(value)

        # Both are arrays: merge them
        if value_tag == "array" and jt_tag == "array":
            sub_jt = jt.data
            for sub_value in value:
                sub_jt = self.merge_value(sub_jt, sub_value)
            jt = JtNode("array", sub_jt)
            return jt

        # Both are objects: merge them
        if value_tag == "object" and jt_tag == "object":
            jt_dict = jt.data
            for key, sub_value in value.items():
                sub_jt = jt_dict.get(key, JtNode("undefined"))
                sub_jt = self.merge_value(sub_jt, sub_value)
                jt_dict[key] = sub_jt
            return jt

        # Both are same simple type: return it
        if value_tag == jt_tag:
            return jt

        # Indicate no merge by returning None
        return None

    def union_merge_value(self, jt, value):
        """Modifies & returns jt (which must be a union)."""

        assert jt.tag == "union"
        value_tag = self.get_value_tag(value)

        # The algorithm:
        # We loop through the subtypes of the union.
        # We may merge value's type with one of the subtypes,
        # in which case we are done.
        # Otherwise, we append its type.

        # NOTE: subtypes of a union are guaranteed not to be unions
        # themselves.
        # (That is, unions are always flat.)
        sub_jts = jt.data
        for sub_jt in sub_jts:
            merged_jt = self._merge_value_core(sub_jt, value)
            if merged_jt is not None:
                return jt

        # We couldn't merge value's type with an exsting subtype of
        # the union.
        # So, we just append its type and we're done!
        value_jt = self.get_value_jt(value)
        sub_jts.append(value_jt)
        return jt

    def match(self, value):
        """Returns bool"""
        return self.match_value(self.jt, value)

    def match_value(self, jt, value):
        """Returns bool"""
        m = self._match_value(jt, value)
        if not m and self.match_verbose:
            print("No match!")
            print("Value: {}".format(value))
            print("Schema:")
            self.show_jt(jt, 1)
        return m

    def _match_value(self, jt, value):
        """Returns bool"""

        jt_tag = jt.tag
        value_tag = self.get_value_tag(value)

        # Any: always matches
        if jt_tag == "any":
            return True

        # Union: value matches if it matches any of union's subtypes
        if jt_tag == "union":
            sub_jts = jt.data
            for sub_jt in sub_jts:
                if self.match_value(sub_jt, value):
                    return True
            return False

        # Array: all elements of the array must match the subtype
        if jt_tag == "array" and value_tag == "array":
            sub_jt = jt.data
            for sub_value in value:
                if not self.match_value(sub_jt, sub_value):
                    if self.match_verbose:
                        print("(At subvalue: {})".format(sub_value))
                    return False
            return True

        # Object: values for all keys must match the corresponding subtype.
        # If subtype is "undefined", key must be missing entirely.
        if jt_tag == "object" and value_tag == "object":
            jt_dict = jt.data

            # Check all keys, relying on the "undefined" type and value
            # to tell us if any are missing
            keys = set(value) | set(jt_dict)

            # Value for each key must match corresponding subtype
            # (Missing keys are handled by a special undefined value)
            for key in keys:
                sub_jt = jt_dict.get(key, JtNode("undefined"))
                sub_value = value.get(key, undefined)
                if not self.match_value(sub_jt, sub_value):
                    if self.match_verbose:
                        print("(At key: {})".format(key))
                    return False

            # All matched!
            return True

        # Simple case: are these the same kind of thing or not?
        return jt_tag == value_tag


def test():
    v1 = {"a": 1, "b": [1, 2]}
    v2 = {"a": 100, "b": None, "c": "Hello"}

    j = JsonType()

    assert j.jt == JtNode("void")

    j.add(v1)

    assert j.match(v1)
    assert not j.match(v2)

    v1_alt = v1.copy()
    v1_alt["lallaa"] = undefined
    assert j.match(v1_alt)

    j.add(v2)

    assert j.match(v1)
    assert j.match(v2)

    print(j)
    assert str(j) == '{"a": number, "b": [number] | null, "c": undefined | string}'

    j.show()

    assert j.jt == JtNode("object", {
        "a": JtNode("number"),
        "b": JtNode("union", [
            JtNode("array", JtNode("number")),
            JtNode("null"),
        ]),
        "c": JtNode("union", [
            JtNode("undefined"),
            JtNode("string"),
        ]),
    })

    assert not j.match(None)
    assert not j.match(1)
    assert not j.match("asd")
    assert not j.match([1,2,3])
    assert not j.match({})
    assert not j.match({"a": 1})
    assert not j.match({"a": 1, "b": 2})
    assert not j.match({"a": 1, "b": [1, 2, "Q"]})
    assert not j.match({"a": 100, "c": "Hello"})
