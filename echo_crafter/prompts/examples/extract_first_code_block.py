#!/usr/bin/env python3

"""This script extract the code blocks from the string passed as standard input."""

import re
import sys

if __name__ == '__main__':
    content = sys.stdin.read()
    #code_blocks = []

    code_blocks = re.findall(r"(?:```\S+\\n)(.*)(?:\\n```)", content, re.DOTALL)

    print("\n\n".join(code_blocks))

    sys.exit(0)
    # split = re.split(r"```\S+\s", content, maxsplit=1)

    # while len(split) > 1:
    #     double_split = re.split(r"```\s", split[1], maxsplit=1)
    #     code_blocks.append(double_split[0])
    #     content = double_split[1]
    #     split = re.split(r"```\S+\s", content, maxsplit=1)

    # code_blocks.append(split[0])
    # print('\n\n'.join(code_blocks))
