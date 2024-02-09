#!/usr/bin/env sh

jq -r '"\(.timestamp | tonumber - 18000 | strftime("%Y-%m-%d %H:%M:%S"))\t\(.query | gsub("\n"; " \\n "))\t\(.answer | gsub("\n";" \\n "))\t\(.language // "log")"' \
    | fzf \
    --delimiter='\t' \
    --tac \
    --scheme=history \
    --no-sort \
    --with-nth 1..1 \
    --nth=2 \
    --multi \
    --keep-right \
    --no-hscroll \
    --preview 'echo -e {2} | bat -l md --color=always --style=header-filename,grid --file-name=USER; echo -e {3} | bat -l {4} --file-name=ASSISTANT --color=always --style=header-filename,numbers,snip,grid' \
    --preview-window=right:80%,wrap
