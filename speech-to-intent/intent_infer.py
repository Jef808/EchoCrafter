#!/usr/bin/env python3

import shlex
import json
from pathlib import Path
import sqlite3
import pandas as pd

shell_history_query = r"""select strftime(case when datetime(max_start, 'unixepoch') > datetime('now', 'start of day') then '%H:%M' else '%d/%m' end, max_start, 'unixepoch', 'localtime') as time, session as ses, dir, argv as cmd from (select session, replace(places.dir, '/home/jfa', '~') as dir, replace(commands.argv, '
', '
') as argv, max(start_time) as max_start
from
  commands
  join history on history.command_id = commands.id
  join places on history.place_id = places.id
group by history.command_id, history.place_id
order by max_start desc) order by max_start asc"""


def get_shell_history():
    """Get the shell history from histdb database."""
    conn = sqlite3.connect(Path.home() / '.histdb/zsh-history.db')
    cursor = conn.cursor()
    cursor.execute(shell_history_query)
    history = cursor.fetchall()
    conn.close()
    return history


def annotate(df, event):
    """Annotate shell history events with topics."""
    time, ses, dir, cmd = event
    try:
        command = shlex.split(cmd)[0]
    except Exception:
        command = cmd.split(' ')[0]
    cmd_data = df[df['cmd'] == command]
    topic = cmd_data['topic'].values.tolist()
    return dict(time=time, ses=ses, dir=dir, cmd=cmd, topic=topic[0] if topic else None)


def main():
    """Print the annotated shell history."""
    history = get_shell_history()
    df = pd.read_csv("cmd_summary_with_clusters.csv")
    with open('annotated_shell_histtory.jsonl', 'w+') as f:
        for event in history:
            annotated_event = annotate(df, event)
            f.write(json.dumps(annotated_event) + '\n')


if __name__ == "__main__":
    main()
