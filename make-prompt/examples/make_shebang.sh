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

add_shebang $1
