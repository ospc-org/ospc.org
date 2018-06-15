Parameter Policy
====================

Goal: document parameter handling approach

Parameter Parsing
-------------------

Ideally, the string received from the user input is parsed into the the
Python type it most closely matches. That means that `'True'` parses
to `True`, `'1'` to `1`, `'20000.0'` to `20000.0`, and so on. It is then
up to the upstream package to perform type and range validation on the
converted object and provide the appropriate error messages.

However, due to issues with the interface, the user's input has to be massaged
into the correct format. For instance, places where we expect a boolean
string display `1.0` as a default value instead of `True`. Thus, the value
parsing logic must be capable of parsing `'1.0'`, `'1'`, or `'True'` to `True`.
There are other issues such as values that should only be integers (e.g. age)
are displayed as floating point values. Once we display more accurate
default values, we should remove this functionality in order to simplify the
codebase. Note that there will always be some element of string massaging
since PolicyBrain users tend to be less technical and thus, may not realize
the significance of entering `True` versus `true` or `TRUE`.


Parameter Deprecation
---------------------

Our primary goal is to preserve the results and relevant information for all
runs. The goal of allowing the user to edit and re-submit previous runs is a
lower priority than the first goal. The underlying modeling packages change
overtime which means that parameter names change, their underlying definitions
change, they are split in to multiple components, and some are removed.
PolicyBrain only allows the user to view and submit parameters that are
supported by the current version of the underlying package. Thus, when a user
tries to access a run submitted on an older version of the underlying package
via the edit parameters page, some of the parameters may not exist on the page
anymore. The PolicyBrain policy in this situation is to allow the user to view
and edit the parameters that still exist and for the parameters that do not,
display an error message at the top of the page for each missing parameter that
says:

    Field {parameter name} has been deprecated. Refer to the Tax-Calculator
    documentation for a sensible replacement.
