#!/usr/bin/env zsh
# This script takes a single quoted string as input with newline (\n) and double quote (\") characters escaped.
# It unescapes these characters and pretty-prints the resulting string.

# Check for the correct number of arguments. If not exactly one, print an error message and exit.
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 \"<string_with_escaped_characters>\""
  exit 1
fi

# Replace escaped newline and double quote characters with their unescaped versions.
# Note: `echo` is used here with the `-e` option to enable interpretation of backslash escapes.
echo -e $1  # | sed '//\n/g' | sed '/\//g'


