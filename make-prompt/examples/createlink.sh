#!/usr/bin/env zsh

function add_shebang() {
    EXTENSION="${1##*.}"
    FIRST_LINE="$(head -n 1 $1)"
    if [[ ! $FIRST_LINE =~ ^#! ]]; then
        case $EXTENSION in
            sh)
                echo -e "#!/usr/bin/env zsh\n$(cat $1)" > $1
                ;;
            py)
                echo -e "#!/usr/bin/env python\n$(cat $1)" > $1
                ;;
            *)
                echo "Failed to add shebang, unknown file type"
                ;;
        esac
    fi
}

relative_path="$1"

absolute_path="$PWD/$relative_path"

# Extract filename without extension
filename_without_extension="${${relative_path##*/}%.*}"

# Replace underscores with dashes
filename="${filename_without_extension//_/-}"

target="$HOME/.local/bin/$filename"

add_shebang $absolute_path

# Create soft link in $HOME/.local/bin
ln -sf "$absolute_path" "$target"

# Make sure the source is executable
chmod +x $relative_path

echo "Created symlink $target -> $absolute_path"
