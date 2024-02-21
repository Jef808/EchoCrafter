#!/usr/bin/env zsh

DIR="$(dirname "$(readlink -f "$0")")"

microphone_listener=$(pgrep -f "listener_with_wake_word") 2>/dev/null
transcripts_collector=$(pgrep -f "socket_read") 2>/dev/null

if [ -n "$microphone_listener" ]; then
  kill -15 "$microphone_listener"
  echo "Microphone listener stopped"
fi
if [ -n "$transcripts_collector" ]; then
  kill -15 "$transcripts_collector"
  echo "Transcripts collector stopped"
fi
