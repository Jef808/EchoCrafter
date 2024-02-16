import argparse
import tree_sitter
import sys
import json
from pathlib import Path


# Get the language of the file
def check_language(filepath):
    extension = filepath.suffix
    if extension == '.js':
        return 'js'
    elif extension == '.ts':
        return 'ts'
    elif extension == '.tsx':
        return 'tsx'
    else:
        return 'other'


# Initialize the JavaScript language parser
# You can change the language name as per your requirement, like for python use 'python', for ruby use 'ruby'
GRAMMAR_JS = tree_sitter.Language('/home/jfa/projects/echo-crafter/build/tree-sitter-languages.so', 'javascript')
GRAMMAR_TS = tree_sitter.Language('/home/jfa/projects/echo-crafter/build/tree-sitter-languages.so', 'typescript')
GRAMMAR_TSX = tree_sitter.Language('/home/jfa/projects/echo-crafter/build/tree-sitter-languages.so', 'tsx')

# Initialize two parsers using the specific languages
PARSER = {
    'js': tree_sitter.Parser(),
    'ts': tree_sitter.Parser(),
    'tsx': tree_sitter.Parser()
}

PARSER['js'].set_language(GRAMMAR_JS)
PARSER['ts'].set_language(GRAMMAR_TS)
PARSER['tsx'].set_language(GRAMMAR_TSX)


def parse_file(file, lang):
    parser = PARSER[lang]
    code = file.read()

    # Parse the code
    tree = parser.parse(bytes(code, "utf8"))

    # Print the tree
    return tree.root_node.sexp()


def parse_directory(directory):
    for item in directory.rglob('*'):
        if item.is_file():
            lang = check_language(item)
            if lang in ['js', 'ts', 'tsx']:
                with open(item, 'r') as f:
                    ast = parse_file(f, lang)
                print(json.dumps({str(item): ast}))
        elif item.is_dir():
            sub_result = parse_directory(item)
        else:
            continue
    return result


def parse_directories(directories):
    result = dict()
    for parsed in (parse_directory(dir) for dir in directories):
        result |= parsed
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get input to parse')
    parser.add_argument('-r', '--recursive', action='store_true', help='Parse recursively on directories')
    parser.add_argument('paths', nargs='+', help='space-separated list of paths to parse')
    args = parser.parse_args()

    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            if not args.recursive:
                print(f"{sys.argv[0]}: -r not specified; omitting directory {path}", file=sys.stderr)
            else:
                parse_directory(path)
        elif path.is_file():
            lang = check_language(path)
            if lang in ['js', 'ts', 'tsx']:
                with open(path, 'r') as f:
                    ast = parse_file(f, lang)
                print(json.dumps({str(path): ast}))
        else:
            continue
