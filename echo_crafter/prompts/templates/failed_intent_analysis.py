
ANALYZE_FAILED_INTENT = """I received a spoken command that failed to match any expressions in my intent recognition system. The command was: '[Your Command Here]'. I need
 to update my 'computer-commands.yml' file and the corresponding intent handler to recognize and execute similar commands in the future.

 1. Analyze the command and determine whether it fits within an existing intent or requires a new intent. Provide a brief explanation for your
 decision.
 2. For an existing intent, suggest new grammar rules to be added to the 'computer-commands.yml' file. For a new intent, suggest a suitable intent
 name along with relevant grammar rules.
 3. Generate the necessary YAML code snippet for the 'computer-commands.yml' file to update my intent recognition system.
 4. Additionally, generate the Python code for the intent handler that will execute the command based on the identified intent. This includes
 creating a new function if a new intent is identified or suggesting modifications to an existing function if applicable."

 Please provide the updates to the 'computer-commands.yml' file and the Python code for the intent handler as separate code snippets.
 """
