
# Py2/3 compatibility
if "raw_input" not in globals():
    # noinspection PyShadowingBuiltins
    raw_input = input
