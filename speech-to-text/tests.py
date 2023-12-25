#!/usr/bin/env python3

from speech_reco import handle_on_message

def expanding_text_add_to_running_partial_transcript():
    print(f"\n   * {expanding_text_add_to_running_partial_transcript.__name__} *\n")
    TEXT="Hello World"
    MESSAGE_TYPE="PartialTranscript"
    RUNNING_PARTIAL_TRANSCRIPT="Hello"
    running_partial_transcript, utterance = handle_on_message(
        TEXT, MESSAGE_TYPE, RUNNING_PARTIAL_TRANSCRIPT
    )

    assert running_partial_transcript == "Hello World"
    assert utterance == ""

    return True

def repeating_partial_does_nothing():
    print(f"\n   * {repeating_partial_does_nothing.__name__} *\n")
    TEXT="Hello World"
    MESSAGE_TYPE="PartialTranscript"
    RUNNING_PARTIAL_TRANSCRIPT = "Hello World"
    running_partial_transcript, utterance = handle_on_message(
        TEXT, MESSAGE_TYPE, RUNNING_PARTIAL_TRANSCRIPT
    )

    result = True

    try:
        assert running_partial_transcript == "Hello World"
    except:
        print(f"while asserting running_partial_transcript == 'Hello World'\nExpected: \033[1mHello World\033[0m, Actual: \033[1m{running_partial_transcript}\033[0m")
        result = result and False
    try:
        assert utterance == ""
    except:
        print(f"while asserting utterance == ''\nExpected: \033[1m''\033[0m, Actual: \033[1m{utterance}\033[0m")
        result = result and False

    return result

def non_prefix_partial_triggers_append_running_partial():
    print(f"\n   * {non_prefix_partial_triggers_append_running_partial.__name__} *\n")
    TEXT="This is new"
    MESSAGE_TYPE="PartialTranscript"
    RUNNING_PARTIAL_TRANSCRIPT = "Hello World"
    running_partial_transcript, utterance = handle_on_message(
        TEXT, MESSAGE_TYPE, RUNNING_PARTIAL_TRANSCRIPT
    )

    result = True

    try:
        assert running_partial_transcript == "This is new"
    except:
        print(f"while asserting running_partial_transcript == 'This is new'\nExpected: \033[1mHello World\033[0m, Actual: \033[1m{running_partial_transcript}\033[0m")
        result = result and False
    try:
        assert utterance == "Hello World"
    except:
        print(f"while asserting utterance == 'Hello World'\nExpected: \033[1mHello World\033[0m, Actual: \033[1m{utterance}\033[0m")
        result = result and False

    return result


if __name__ == '__main__':
    print("*** TESTING HANDLE_ON_MESSAGE ***")

    res = expanding_text_add_to_running_partial_transcript()
    print(f"\n   {expanding_text_add_to_running_partial_transcript.__name__}: \033[1m{'PASSED' if res else 'FAILED'}\033[0m")

    res = repeating_partial_does_nothing()
    print(f"\n   {repeating_partial_does_nothing.__name__}: \033[1m{'PASSED' if res else 'FAILED'}\033[0m")

    res = non_prefix_partial_triggers_append_running_partial()
    print(f"\n   {non_prefix_partial_triggers_append_running_partial.__name__}: \033[1m{'PASSED' if res else 'FAILED'}\033[0m")
