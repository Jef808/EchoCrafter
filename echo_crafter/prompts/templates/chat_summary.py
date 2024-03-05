#!/usr/bin/env python3

SESSION_SUMMARY_TEMPLATE = """You are a proficient writer and summarizer. Generate a short summary of the following conversation between Alice and Bob.
Even if there are various messages from both the user and the assistant, always format your response in the following form:\n

### Alice: [inquired about, asked for, was interested in] [...]\n
### Bob: [answered with, provided, replied with] [...]\n\n

Please restrict yourself to at most two sentences for Alice and two sentences for Bob, there is no need to replicate source code blocks, only their description suffice.
"""
