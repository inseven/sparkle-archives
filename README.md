# Sparkle Archives

[![build](https://github.com/inseven/sparkle-archives/actions/workflows/build.yaml/badge.svg)](https://github.com/inseven/sparkle-archives/actions/workflows/build.yaml)

Generate and publish Sparkle appcasts

## Overview

Generates appcasts for the following apps:

- [Fileaway](https://fileaway.jbmorley.co.uk)
- [Folders](https://folders.jbmorley.co.uk)
- [InContext Helper](https://incontext.jbmorley.co.uk)
- [Reconnect](https://reconnect.jbmorley.co.uk)
- [Thoughts](https://thoughts.jbmorley.co.uk)

## Service

Appcasts are published to [https://sparkle.jbmorley.co.uk](https://sparkle.jbmorley.co.uk).

Paths are of the form:

```
https://sparkle.jbmorley.co.uk/<owner>/<repo>/appcast.xml
```

e.g., The appcast for Thoughts is located at [https://sparkle.jbmorley.co.uk/inseven/thoughts/appcast.xml](https://sparkle.jbmorley.co.uk/inseven/thoughts/appcast.xml).

## Development

Right now the list of apps is hardcoded in `scripts/build.py`. Adding an app is a matter of adding an entry to the `repositories` variable. For example,

```python
repositories = [
    ('inseven', 'fileaway', 'Fileaway'),
    ('inseven', 'folders', 'Folders'),
    ('inseven', 'incontext', 'InContext Helper'),
    ('inseven', 'reconnect', 'Reconnect'),
    ('inseven', 'thoughts', 'Thoughts'),
]
```
