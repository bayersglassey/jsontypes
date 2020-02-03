# JSONTYPES

## Overview

Super-simple type system for JSON.
The use case is discovering the schema of existing datasets.

For instance, given a database full of JSON blobs which are similar but have
no official schema, you could feed them into a JsonType and see just how similar they are:

    from jsontypes import JsonType
    jt = JsonType()

    # You'll need to define this function.
    blobs = get_json_blobs_from_database()

    # Feed the blobs to the JsonType; it will build up a schema.
    for blob in blobs:
        jt.add(blob)

    # Now let's find out just how similar those blobs were...
    jt.show()

There are the familiar JSON types: null, number, string, boolean, object, array

...plus some special types: union, void, any, undefined


## The types

### Parameterized types

The object, array, and union types are parameterized.
For instance:

    {"a": 1, "b": "hello"} is of type {"a": number, "b": string}

    [1, 2, 3] is of type [number]

    [1, 2, "hello"] is of type [number | string]


### Void and any

The void type does not match any values.

The any type matches all values.


### Undefined

The undefined type doesn't match any real JSON values, but it does match the
conceptual value stored on an obect for a key the object doesn't actually have.
If that doesn't make sense to you, let me describe it like this:

    {} is of type {}
    {} is also of type {"a": undefined}
    {} is also of type {"a": undefined, "b": undefined}
    ...etc

In practise, we only need this type so that we can use it with union to define
optional object keys.
For instance:

    Let T be the type {"a": number, "b": undefined | number}

    {"a": 1} is of type T
    {"a": 1, "b": 2} is also of type T


## The schema-building algorithm

In a nutshell: we start having seen no values so far.
So our schema is the least permissive possible: void.
When we see a value, we modify the schema as little as possible so that
it will accept the value.
We do this by traversing the value and the schema at the same time,
depth-first, and... uh...

TODO: describe the algorithm, with examples


## Basic usage

Create a JsonType and add() values to it.

    from jsontypes import JsonType
    p = JsonType()
    p.add({"a": 1, "b": [1, 2]})
    p.add({"a": 100, "b": None, "c": "Hello"})

    print(p)
    # ...Prints: {"a": number, "b": [number] | null, "c": undefined | string}

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


## Examples

See the [example files](/examples).
