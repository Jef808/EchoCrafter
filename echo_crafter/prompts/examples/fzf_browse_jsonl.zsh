#!/bin/zsh

# The script begins by defining a check for the presence of the `fzf_browse_jsonl` function.
# If the function is not found in the global functions list, the script throws an error and exits.

# fzf_browse_with_search_jsonl will operate on top of the fzf_browse_jsonl function by creating a custom FZF command with the ctrl+s keybinding enabled for searching.

: <<'END'
fzf_browse_with_search_jsonl utilizes fzf_browse_jsonl, which provides pretty printed representation of json data from jsonl files in a preview window,
to enable searching within values in the json data with the ctrl+s keybinding.
END
fzf_browse_with_search_jsonl() {
  # 'export' function is used to export the defined 'FZF_DEFAULT_COMMAND' to child processes. 
  # Keybinding 'ctrl+s' is enabled with the '--bind' flag.
  export FZF_DEFAULT_COMMAND='fzf_browse_jsonl'
  fzf --bind "ctrl+s:toggle-search"
}

# Call the searching function.
fzf_browse_with_search_jsonl
