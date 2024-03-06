#!/usr/bin/env python3

import json
import jsonschema
from jsonschema import Draft7Validator
from collections import defaultdict
import sys

def generate_json_schema(json_obj: dict) -> dict:
    """
    Generate a JSON schema for a given JSON object.
    
    :param json_obj: A dictionary representing a JSON object.
    :return: A dictionary representing the JSON schema of the input JSON object.
    """
    generator = jsonschema.Draft7Validator
    schema = generator.generate(json_obj)
    return schema

def identify_and_generate_schemas(jsonl_file_path: str) -> dict:
    """
    Identify different JSON objects in a JSONL file and generate JSON schemas for each type.
    
    :param jsonl_file_path: Path to the JSONL file.
    :return: A dictionary with line numbers as keys and their corresponding JSON schemas as values.
    """
    schemas = defaultdict(list)
    with open(jsonl_file_path, 'r') as file:
        for line_number, line in enumerate(file, start=1):
            try:
                json_obj = json.loads(line)
                schema = generate_json_schema(json_obj)
                schemas[json.dumps(schema)].append(line_number)
            except json.JSONDecodeError:
                print(f"Error decoding JSON on line {line_number}", file=sys.stderr)
    
    # Convert schema back to dict for readability
    schema_dict = {json.loads(schema): lines for schema, lines in schemas.items()}
    return schema_dict

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_json_schemas.py <path_to_jsonl_file>", file=sys.stderr)
        sys.exit(1)
    
    jsonl_file_path = sys.argv[1]
    schemas = identify_and_generate_schemas(jsonl_file_path)
    
    for schema, lines in schemas.items():
        print(f"Schema for lines: {lines}\n{json.dumps(schema, indent=4)}\n")

if __name__ == "__main__":
    main()