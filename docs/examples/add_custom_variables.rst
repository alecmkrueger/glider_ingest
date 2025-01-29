Add custom variables
======================================

You can add custom variables using just the name of the variable

.. literalinclude:: ../examples/add_custom_variables_string.py

You can also add custom variables by initlizing the variable using the Variable class and assigning attributes to it.
This is useful when you want to add attributes to the NetCDF file for that variable. Like assigning units or adding a comment.

.. literalinclude:: ../examples/add_custom_variables.py
