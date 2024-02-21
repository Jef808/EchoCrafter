#!/usr/bin/env zsh

DIR="$(dirname "$(readlink -f "$0")")"

if pgrep -f "listener_with_wake_word" >/dev/null || pgrep -f "socket_read" >/dev/null; then
  echo "The process is already running"
  exit 1
else
  source "$DIR/.venv/bin/activate"
  python "$DIR/echo_crafter/listener/socket_read.py" &
  echo "Transcripts collector started"
  python "$DIR/echo_crafter/listener/listener_with_wake_word.py" &
  echo "Microphone listener started"
fi
