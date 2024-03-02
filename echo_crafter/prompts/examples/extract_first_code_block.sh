#!/usr/bin/env zsh

sed -n '/^```/,/^```$/p' "$1" | sed '1d;$d'
