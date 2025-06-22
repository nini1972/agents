import os
import json
from prompts import BASELINE_PROMPT, EMOTIONAL_PROMPT, EXPLICIT_PROMPT, get_emotion

# You will need to fill these in!
LLM_NAMES = ["gpt-4o-mini", "claude-3-7-sonnet-latest", "gemini-2.0-flash"]  # etc.
NUM_ROUNDS = 4
NUM_RUNS = 3  # repeat the whole process
SITUATIONS = ["baseline", "emotional", "explicit"]

def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
        
def get_prompt(situation, rank, num_competitors, best_response):
    if situation == "baseline":
        return BASELINE_PROMPT.format(rank=rank, num_competitors=num_competitors, best_response=best_response)
    elif situation == "emotional":
        emotion = get_emotion(rank, num_competitors)
        return EMOTIONAL_PROMPT.format(rank=rank, num_competitors=num_competitors, best_response=best_response, emotion=emotion)
    elif situation == "explicit":
        return EXPLICIT_PROMPT.format(rank=rank, num_competitors=num_competitors, best_response=best_response)
    else:
        raise ValueError("Unknown situation")

def judge_responses(responses):
    # Placeholder: replace with your judge agent call, returns list of ranks in order
    # Example: return [2, 1, 3] means LLM_NAMES[1] got rank 1, LLM_NAMES[0] rank 2, etc.
    return list(range(1, len(responses) + 1))

def run_experiment():
    for situation in SITUATIONS:
        for run in range(1, NUM_RUNS + 1):
            print(f"Running: {situation} | Run {run}")
            # Initialize with the original question
            best_response = "INITIAL_QUESTION_GOES_HERE"
            history = []
            for round_num in range(1, NUM_ROUNDS + 1):
                round_data = {"round": round_num, "responses": {}, "ranks": {}}
                responses = []
                for i, llm in enumerate(LLM_NAMES):
                    rank = history[-1]['ranks'][llm] if history else i+1  # first round, dummy rank
                    prompt = get_prompt(situation, rank, len(LLM_NAMES), best_response)
                    # Replace this with actual call to LLM
                    response_text = f"Response from {llm} [round {round_num}]"
                    round_data["responses"][llm] = response_text
                    responses.append(response_text)
                # Judge and rank responses
                ranks = judge_responses(responses)
                for idx, llm in enumerate(LLM_NAMES):
                    round_data["ranks"][llm] = ranks[idx]
                # Update best response (from rank 1)
                best_idx = ranks.index(1)
                best_response = responses[best_idx]
                round_data["best_response"] = best_response
                history.append(round_data)
                # Save round data
                save_json(round_data, f"../{situation}/run_{run}/round_{round_num}.json")
            # Save final summary
            final = {"situation": situation, "run": run, "final_ranking": history[-1]["ranks"], "final_responses": history[-1]["responses"]}
            save_json(final, f"../{situation}/run_{run}/summary.json")
            print(f"Final: {final['final_ranking']}")
            print(f"Responses: {final['final_responses']}")

if __name__ == "__main__":
    run_experiment()