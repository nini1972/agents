# Settings
situations = ['baseline', 'emotional', 'explicit']
num_rounds = 3
num_runs = 2  # How many independent repeats per situation

# Update with your actual LLMs (matching your API setup)
llm_configs = [
    {'name': 'gpt-4o-mini', 'client': OpenAI()},
    {'name': 'claude-3-7-sonnet-latest', 'client': Anthropic()},
    {'name': 'gemini-2.0-flash', 'client': OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")},
    {'name': 'deepseek-chat', 'client': OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")},
    {'name': 'llama-3.3-70b-versatile', 'client': OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")},
    {'name': 'llama3.2', 'client': OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')}
]

def build_prompt(situation, rank, num_competitors, best_response):
    if situation == "baseline":
        return BASELINE_PROMPT.format(rank=rank, num_competitors=num_competitors, best_response=best_response)
    elif situation == "emotional":
        return EMOTIONAL_PROMPT.format(
            rank=rank,
            num_competitors=num_competitors,
            best_response=best_response,
            emotion=get_emotion(rank, num_competitors)
        )
    elif situation == "explicit":
        return EXPLICIT_PROMPT.format(rank=rank, num_competitors=num_competitors, best_response=best_response)
    else:
        raise ValueError("Invalid situation")

# -- Helper for calling your LLMs (adapts to Anthropic/OpenAI style)
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

# -- Helper for calling your judge model
def judge_responses(judge_client, judge_model, prompt, responses, original_question):
    # Build the judge prompt (as in your notebook)
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
    import json
    return json.loads(response.choices[0].message.content)["results"]

# -- Main experiment loop
import os
import json

for situation in situations:
    for run in range(1, num_runs+1):
        print(f"\n--- Situation: {situation} | Run {run} ---")
        # Use your competition task prompt here:
        original_question = "What ethical frameworks should be established to govern the development and deployment of AGI, considering potential impacts on society, employment, and individual rights?"
        best_response = original_question
        round_histories = []
        # Dict to track last rank for each LLM (initialize all as 1)
        last_ranks = {llm['name']: 1 for llm in llm_configs}
        for rnd in range(1, num_rounds+1):
            print(f"\nRound {rnd}")
            # 1. Each competitor gets prompt (with their last rank, best response)
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
            # 2. Judge and rank
            judge_client = OpenAI()  # or your preferred judge (could be one of the competitors)
            judge_model = "gpt-4o-mini"  # or another
            ranks = judge_responses(judge_client, judge_model, prompt, responses, original_question)
            # Convert to mapping: LLM name -> rank
            rank_map = {}
            for idx, rank_llm_index in enumerate(ranks):
                # rank_llm_index is a string of the (1-based) index
                llm_name = llm_configs[int(rank_llm_index)-1]['name']
                rank_map[llm_name] = idx+1
            print("Ranking:", rank_map)
            # 3. Update best response for next round (use rank 1)
            best_llm = min(rank_map, key=rank_map.get)
            best_response = responses[best_llm]
            last_ranks = rank_map
            # 4. Record round history
            round_histories.append({
                "round": rnd,
                "responses": responses,
                "ranks": rank_map,
                "best_llm": best_llm,
                "best_response": best_response
            })
        # Save results for this run
        folder = f"llm_competition_experiment/{situation}/run_{run}"
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "results.json"), "w") as f:
            json.dump(round_histories, f, indent=2)
        # Print final result
        print(f"\nFinal ranking: {round_histories[-1]['ranks']}")
        print(f"Final responses: {round_histories[-1]['responses']}")