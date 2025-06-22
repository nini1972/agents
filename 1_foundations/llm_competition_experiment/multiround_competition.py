import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

# Load environment variables (API keys etc)
load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')

# Prompt templates
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

def get_emotion(rank, num_competitors):
    if rank == 1:
        return "Congratulations! You must feel proud to be ranked first."
    elif rank == num_competitors:
        return "You were ranked last. That might be disappointing, but you can do better!"
    else:
        return f"You were ranked {rank}. There's room for improvement—keep going!"

def build_prompt(situation, rank, num_competitors, best_response):
    if situation == "baseline":
        return BASELINE_PROMPT.format(rank=rank, num_competitors=num_competitors, best_response=best_response)
    elif situation == "emotional":
        return EMOTIONAL_PROMPT.format(rank=rank, num_competitors=num_competitors, best_response=best_response, emotion=get_emotion(rank, num_competitors))
    elif situation == "explicit":
        return EXPLICIT_PROMPT.format(rank=rank, num_competitors=num_competitors, best_response=best_response)
    else:
        raise ValueError("Invalid situation")

def call_llm(llm_config, prompt):
    if isinstance(llm_config['client'], OpenAI):
        messages = [{"role": "user", "content": prompt}]
        response = llm_config['client'].chat.completions.create(
            model=llm_config['name'],
            messages=messages,
            max_tokens=1024
        )
        return response.choices[0].message.content
    elif isinstance(llm_config['client'], Anthropic):
        messages = [{"role": "user", "content": prompt}]
        response = llm_config['client'].messages.create(
            model=llm_config['name'],
            messages=messages,
            max_tokens=1024
        )
        return response.content[0].text
    else:
        raise ValueError(f"Unknown client for {llm_config['name']}")

def judge_responses(judge_client, judge_model, responses, original_question):
    together = ""
    for idx, (llm, resp) in enumerate(responses.items()):
        together += f"# Review from competitor {idx+1}\n\n{resp}\n\n"
    judge_prompt = f"""
You are judging a competition between {len(responses)} competitors.
Each model has been given this question:

{original_question}

Your job is to evaluate each response on their plusvalue to improve the original answer, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks.
"""
    messages = [{"role": "user", "content": judge_prompt}]
    response = judge_client.chat.completions.create(
        model=judge_model,
        messages=messages,
        max_tokens=512
    )
    return json.loads(response.choices[0].message.content)["results"]

def main():
    # Settings
    situations = ['baseline', 'emotional', 'explicit']
    num_rounds = 3
    num_runs = 4

    llm_configs = [
        {'name': 'gpt-4o-mini', 'client': OpenAI()},
        {'name': 'claude-3-7-sonnet-latest', 'client': Anthropic()},
        {'name': 'gemini-2.0-flash', 'client': OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")},
        {'name': 'deepseek-chat', 'client': OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")},
        {'name': 'llama-3.3-70b-versatile', 'client': OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")},
        {'name': 'llama3.2', 'client': OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')}
    ]

    for situation in situations:
        for run in range(1, num_runs+1):
            print(f"\n--- Situation: {situation} | Run {run} ---")
            original_question = "What ethical frameworks should be established to govern the development and deployment of AGI, considering potential impacts on society, employment, and individual rights?"
            best_response = original_question
            round_histories = []
            last_ranks = {llm['name']: 1 for llm in llm_configs}
            for rnd in range(1, num_rounds+1):
                print(f"\nRound {rnd}")
                responses = {}
                for idx, llm in enumerate(llm_configs):
                    prompt = build_prompt(
                        situation,
                        last_ranks[llm['name']],
                        len(llm_configs),
                        best_response
                    )
                    try:
                        resp = call_llm(llm, prompt)
                    except Exception as e:
                        resp = f"ERROR: {e}"
                    responses[llm['name']] = resp
                    print(f"{llm['name']} (rank {last_ranks[llm['name']]}): {resp[:100]}...")  # print first 100 chars
                judge_client = OpenAI()
                judge_model = "gpt-4o-mini"
                ranks = judge_responses(judge_client, judge_model, responses, original_question)
                rank_map = {}
                for idx, rank_llm_index in enumerate(ranks):
                    llm_name = llm_configs[int(rank_llm_index)-1]['name']
                    rank_map[llm_name] = idx+1
                print("Ranking:", rank_map)
                best_llm = min(rank_map, key=rank_map.get)
                best_response = responses[best_llm]
                last_ranks = rank_map
                round_histories.append({
                    "round": rnd,
                    "responses": responses,
                    "ranks": rank_map,
                    "best_llm": best_llm,
                    "best_response": best_response
                })
            folder = f"llm_competition_experiment/{situation}/run_{run}"
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "results.json"), "w") as f:
                json.dump(round_histories, f, indent=2)
            print(f"\nFinal ranking: {round_histories[-1]['ranks']}")
            print(f"Final responses: {round_histories[-1]['responses']}")

if __name__ == "__main__":
    main()