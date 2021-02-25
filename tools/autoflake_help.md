usage: autoflake [-h] [-c] [-i] [-r] [--exclude globs] [--imports IMPORTS]
                 [--expand-star-imports] [--remove-all-unused-imports]
                 [--ignore-init-module-imports] [--remove-duplicate-keys]
                 [--remove-unused-variables] [--version] [-v]
                 files [files ...]

Removes unused imports and unused variables as reported by pyflakes.

positional arguments:
  files                 files to format

optional arguments:
  -h, --help            show this help message and exit
  -c, --check           return error code if changes are needed
  -i, --in-place        make changes to files instead of printing diffs
  -r, --recursive       drill down directories recursively
  --exclude globs       exclude file/directory names that match these comma-
                        separated globs
  --imports IMPORTS     by default, only unused standard library imports are
                        removed; specify a comma-separated list of additional
                        modules/packages
  --expand-star-imports
                        expand wildcard star imports with undefined names;
                        this only triggers if there is only one star import in
                        the file; this is skipped if there are any uses of
                        `__all__` or `del` in the file
  --remove-all-unused-imports
                        remove all unused imports (not just those from the
                        standard library)
  --ignore-init-module-imports
                        exclude __init__.py when removing unused imports
  --remove-duplicate-keys
                        remove all duplicate keys in objects
  --remove-unused-variables
                        remove unused variables
  --version             show program's version number and exit
  -v, --verbose         print more verbose logs (you can repeat `-v` to make
                        it more verbose)
