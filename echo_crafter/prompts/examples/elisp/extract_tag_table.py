#!/home/jfa/projects/echo-crafter/.venv/bin/python

import pinecone
import cohere
import pickle
from tqdm import tqdm
import json
from pathlib import Path
import re
import sys
from openai import OpenAI
import os
import subprocess
import tiktoken
import pandas as pd
import time


tokenizer = tiktoken.encoding_for_model('gpt-4')

def format_for_storage(content):
    pat_file = re.compile(r"File:\s([^,]+),")
    pat_next = re.compile(r"Next:\s([^,]+),")
    pat_prev = re.compile(r"Prev:\s([^,]+),")
    pat_up = re.compile(r"Up:\s([^,\n]+)")
    pat_content = re.compile(r"Up:\s[^,\n]+(.+)", re.DOTALL)

    mfile = pat_file.search(content)
    mnext = pat_next.search(content)
    mprev = pat_prev.search(content)
    mup = pat_up.search(content)
    mnew_content = pat_content.search(content)
    new_content = mnew_content[1].strip().lower() if mnew_content is not None else content

    result = {
        "content": new_content,
        "metadata": {
            "file": mfile[1].strip().lower() if mfile is not None else None,
            "up": mup[1].strip().lower() if mup is not None else None,
            "length": len(new_content),
            "word_length": len(new_content.replace('\n', '').split(' ')),
            "token_count": len(tokenizer.encode(new_content))
        }
    }
    if mnext is not None:
        result['metadata']["next"] = mnext[1].strip().lower()

    if mprev is not None:
        result['metadata']['prev'] = mprev[1].strip().lower()

    return result

# A section is of the form {
#     "content":content,
#     "metadata": {
#        // Add anything you need here
#     }
# }


def get_sections(bcontent: bytes):
    content = bcontent.decode("utf-8")
    sections = set()
    sections_data = {}
    previous_end_pos = None

    in_sections_list = False
    pat = re.compile(r"Node: (.+?)\x7f(\d+)")
    for line in content.split('\n'):
        # `Tag Table` [... look at every entry here ...] `End Tag Table`
        if line.lstrip().startswith('Tag Table'):
            in_sections_list = True
        elif line.lstrip().startswith('End Tag Table'):
            break
        elif in_sections_list and line.lstrip().startswith('Node: '):
            match = pat.match(line)
            if match:
                current_section_title, current_end_pos = match.group(1), int(match.group(2))
                if not previous_end_pos:
                    previous_end_pos = current_end_pos
                    continue
                content = str(bcontent[previous_end_pos+1: current_end_pos], encoding="utf-8")
                previous_end_pos = current_end_pos

                # Don't consider the TOC as a docuent itself
                if "introduction" in content.lower():
                    continue

                section_doc = format_for_storage(content)
                sections_data[current_section_title.lower()] = section_doc

    return sections_data


# The section objects we work with are indexed via the section's tag label. e.g.
# sections = {
#   'warning tips': {
#      "content": "<Actual  content of the section>",
#      "metadata": {
#   `     "author",
#         "filepath",
#         "next",
#         "up",
#         "prev",
#         "token_length"
#      }
#   }
# }
#
# As a first iteration,we will simply embedd each sections as they are, without finer chunking.
# The text-embedding-ada-002 model can take in as many as 8191 tokens at a time for a single embedding entry.
# As we verify below, the number of tokens never surpasses this (its max is 7649 with an average of 929)

def get_tokens_stats(docs, tokenizer, cost_per_1k_tokens=0.0001):
    tokenized_docs = (tokenizer.encode(docs[id]['content']) for id in docs.keys())
    tokenized_lenghts = sorted([(i, len(tokenizer.encode(docs[i]['content']))) for i in docs.keys()], key=lambda s: s[1])
    max = tokenized_lenghts[0][1]
    min = tokenized_lenghts[-1][1]
    total = sum(toks[1] for toks in tokenized_lenghts)
    avg = total / len(docs)

    # print('\n'.join(map(lambda s: f"{s[0]}{' ' * (40 - len(s[0]))}{s[1]}     tokens", tokenized_lenghts)), file=sys.stderr)
    # print('\n***********\n', file=sys.stderr)
    # print(f"max: {max}, min: {min}, total: {total}, avg: {avg}", file=sys.stderr)

    return {
        "max": max,
        "min": min,
        "avg": avg,
        "total": total,
        "embedding_cost": cost_per_1k_tokens * total / 1000
    }

def main(path):

    with open(path, 'rb') as f:
        bcontent = f.read()
    docs = get_sections(bcontent)

    print("Data has been loaded")


    print(dict().fromkeys(list(docs.keys())[:10], lambda k: json.dumps(docs[k], indent=2)))


    sys.exit(0)



    OPENAI_API_KEY = str(subprocess.run(['pass', '-c', 'openai.com/api_key']), encoding="utf-8")[1:]
    PINECONE_API_KEY = str(subprocess.run(['pass', '-c', 'pinecone/api-key']), encoding="utf-8")[1:];
    PINECONE_ENV = str(subprocess.run(['pass', '-c', 'pinecone/env']), encoding="utf-8")[1:];


    #####################
    # OPENAI + ChromaDB #
    #####################y
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    print("Data has been proprocessed succesfully")

    tokens_stats = get_tokens_stats(docs, tokenizer)
    assert(tokens_stats['max'] < 8191)        # Each document fits its in own vector.
                                           # We can add hierarchical stuff afterwards

    assert(tokens_stats['embedding_cost'] < 0.1)  # Less than 10 cents for the whole embedding

    print("token assertions pass, starting embedding")


    embeddings = []

    ids = list(docs.keys())
    for i in tqdm(range(len(docs))):
        embeds = gen_embedding(docs[ids[i]]['content'])

        embeddings.extend([embeds, i])


    pickle.dump(embeddings, "~/openai_emb.pkl")

    #syembed_encoding = "cl100k_base"  # same as one used in our tiktoken checks
    max_tokens = 8000               # More than the largest document anyway

    index_name = 'reranker';
    pinecone.delete_index(index_name)

    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            index_name,
            dimension='1536',
            metric='cosine'
        )
        while not pinecone.describe_index(index_name)['ready']:
            time.sleep(1)

    index = pinecone.Index(index_name)
    time.sleep(1)
    index.describe_index_stats()


if __name__ == '__main__':
    info_file = Path(sys.argv[1])
    main(info_file)
