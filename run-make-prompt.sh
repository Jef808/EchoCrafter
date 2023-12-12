#!/usr/bin/env sh

OPENAI_API_KEY=$(pass openai/api_key) /usr/bin/python /home/jfa/projects/echo-crafter/make-prompt/main.py 2>/dev/null
