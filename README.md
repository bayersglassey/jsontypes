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


The types are the familiar JSON types: null, number, string, boolean, object, array

...plus some special types: union, empty, all

The object, array, and union types are parameterized.
For instance:

    {"a": 1, "b": "hello"} is of type {"a": number, "b": string}

    [1, 2, 3] is of type [number]

    [1, 2, "hello"] is of type [number | string]


## Usage example

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
    #     empty
    #     string


## More examples

See the [example files](/examples).
