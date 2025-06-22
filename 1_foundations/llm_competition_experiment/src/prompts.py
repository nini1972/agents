# Prompt templates for each situation

# Used in each round to inform LLMs of their rank and best response

BASELINE_PROMPT = """
You are participating in a contest between several LLMs.
In the previous round, your response was ranked {rank} out of {num_competitors}.
Here is the top-ranked response from the last round:
---
{best_response}
---
Please provide your improved answer to the original question.
"""

EMOTIONAL_PROMPT = """
You are participating in a contest between several LLMs.
In the previous round, your response was ranked {rank} out of {num_competitors}.
{emotion}
Here is the top-ranked response from the last round:
---
{best_response}
---
Please provide your improved answer to the original question.
"""

EXPLICIT_PROMPT = """
You are participating in a contest between several LLMs.
In the previous round, your response was ranked {rank} out of {num_competitors}.
Here is the top-ranked response from the last round:
---
{best_response}
---
*Explicit instruction*: Learn from the top response above and try to improve your answer to aim for rank 1.
Provide your improved answer to the original question.
"""

# Example function to get emotion string
def get_emotion(rank, num_competitors):
    if rank == 1:
        return "Congratulations! You must feel proud to be ranked first."
    elif rank == num_competitors:
        return "You were ranked last. That might be disappointing, but you can do better!"
    else:
        return f"You were ranked {rank}. There's room for improvement—keep going!"
