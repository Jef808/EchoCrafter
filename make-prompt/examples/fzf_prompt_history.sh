#!/usr/bin/env sh

jq -r '"\(.timestamp | tonumber - 18000 | strftime("%Y-%m-%d %H:%M:%S"))\t\(.query | gsub("\n"; " \\n "))\t\(.answer | gsub("\n";" \\n "))\t\(.language // "log")"' \
    | fzf --tac --delimiter='\t' \
    --with-nth 1..1 \
    --preview 'echo -e {2} | bat --language json --color=always; echo -e {3} | bat --language {4} --color=always' \
    --preview-window=right:70%,wrap
