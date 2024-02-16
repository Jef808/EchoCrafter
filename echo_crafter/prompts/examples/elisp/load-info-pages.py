#!/home/jfa/projects/echo-crafter/.venv/bin/python

import chromadb
import pickle
from tqdm import tqdm
from pathlib import Path
import re
import sys
from openai import OpenAI
import subprocess
import tiktoken
import os
import pandas as pd
import openai
import time


openai_client = None


def setup_openai():
    """Try to retrieve and setup the openai api key."""
    global openai_client

    if os.getenv("OPENAI_API_KEY") is not None:
        openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return

    p = subprocess.run(['pass', '-c', 'openai.com/api_key'], stdout=subprocess.PIPE)
    if not p.stdout:
        print("Failed to retrieve OpenAI api key", file=sys.stderr)
        sys.exit(1)

    openai_client = openai.OpenAI(api_key=str(p.stdout, encoding="utf-8").strip())


def embed(docs: list[str]) -> list[list[float]]:
    """Uses the openai text-embeding-ada-002 to embed the documents passed."""
    res = openai_client.embeddings.create(input=docs, engine='text-embedding-ada-002')
    embeddings = [x["embeddings"] for x in res["data"]]
    return embeddings


def batch_embed(data, batch_size):
    """Perform the embedding on all our documents."""
    embeddings = []
    for i in tqdm(range(0, len(data), batch_size)):
        passed = False
        i_end = min(len(data), i+batch_size)
        batch = data[i:i_end]

        for j in range(5):
            try:
                res = embed(batch["text"])
                passed = True
            except openai.error.RateLimitError:
                time.sleep(2**j)
                print("Retrying...")
        if not passed:
            raise RunTimeError("Failed to create embeddings")
    embeds = [record['embeddings'] for record in res['data']]


def create_metadata(content):
    """Extract the relational data contained in the header of an info page."""
    pat_file = re.compile(r"File:\s([^,]+),")
    pat_next = re.compile(r"Next:\s([^,]+),")
    pat_prev = re.compile(r"Prev:\s([^,]+),")
    pat_up = re.compile(r"Up:\s([^,\n]+)")

    mfile = pat_file.search(content)
    mnext = pat_next.search(content)
    mprev = pat_prev.search(content)
    mup = pat_up.search(content)

    result = {
        "file": mfile[1].strip() if mfile is not None else None,
        "up": mup[1].strip() if mup is not None else None,
    }

    if mnext is not None:
        result['metadata']["next"] = mnext[1].strip()

    if mprev is not None:
        result['metadata']['prev'] = mprev[1].strip()

    return result


def chunk_by_page(bcontent: bytes) -> list[str]:
    """Chunk the whole info document into individual pages."""
    content = bcontent.decode("utf-8")
    pages = []
    old_endpos = None

    in_tag_table = False
    pat_node = re.compile(r"Node: (.+?)\x7f(\d+)")
    for line in content.split('\n'):
        # `Tag Table` [... look at every entry here ...] `End Tag Table`
        if line.startswith('Tag Table'):
            in_tag_table = True
            continue
        if line.startswith('End Tag Table'):
            break
        if in_tag_table and line.startswith('Node: '):
            match = pat_node.match(line)
            if match:
                section_title, section_endpos = match.group(1), int(match.group(2))
                if not old_endpos:
                    # We are at the root
                    old_endpos = section_endpos
                    continue
                page = str(bcontent[old_endpos+1: old_endpos], encoding="utf-8")
                pages.append(page)

    return pages


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

    print(f"data has been read: {len(bcontent)} bytes")

    pages = chunk_by_page(bcontent)

    print(f"Chunked the document into {len(pages)} info pages")

    print(pages[-10:])

    sys.exit(0)

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    print("Data has been proprocessed succesfully")

    tokens_stats = get_tokens_stats(docs, tokenizer)
    assert(tokens_stats['max'] < 8191)        # Each document fits its in own vector.
                                           # We can add hierarchical stuff afterwards

    assert(tokens_stats['embedding_cost'] < 0.1)  # Less than 10 cents for the whole embedding

    print("token assertions pass, starting embedding")


    for i in range(0, len(docs), 32):

        i_end = min(len(docs), i+32)


    embeddings = []
    def gen_embedding(content):
        to_embed = [c.strip() for c in content.split('\n\n')]
        return openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=to_embed
        )


    ids = list(docs.keys())
    for i in tqdm(range(len(docs))):
        embeds = gen_embedding(docs[ids[i]]['content'])

        embeddings.extend([embeds, i])


    pickle.dump(embeddings, "~/openai_emb.pkl")

    #syembed_encoding = "cl100k_base"  # same as one used in our tiktoken checks
    max_tokens = 8000               # More than the largest document anyway


if __name__ == '__main__':
    info_file = Path(sys.argv[1])
    main(info_file)
