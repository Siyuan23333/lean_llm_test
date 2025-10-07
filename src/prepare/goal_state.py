import json
import asyncio
import multiprocessing as mp
from multiprocessing import Pool
import os

from tqdm import tqdm
from lean_interact import *
from lean_interact.interface import LeanError


def load_dataset(dataset_path: str):
    tasks = []
    with open(dataset_path) as f:
        for line in f.readlines():
            task = json.loads(line)
            tasks.append(task)
    return tasks


def get_goal_state(config, context_code, theorem_statement, timeout_per_proof=10):
    
    server = LeanServer(config)
    context_res = server.run(Command(cmd=context_code))
    assert not isinstance(context_res, LeanError)
    context_env = context_res.env

    lean_output = server.run(
        Command(cmd=theorem_statement + ":= sorry", env=context_env), timeout=timeout_per_proof
    )
    if isinstance(lean_output, LeanError) or not lean_output.lean_code_is_valid(allow_sorry=True):
        print(f"Error in Lean output for theorem '{theorem_statement}': {lean_output.message if isinstance(lean_output, LeanError) else 'Invalid code'}")
        return None
    
    goal_state = lean_output.sorries[0].goal
    
    return goal_state


config = LeanREPLConfig(project=LocalProject("/Users/siyuange/Documents/lean_llm_test/miniF2F-lean4"))
dataset_path = "/Users/siyuange/Documents/lean_llm_test/data/minif2f.jsonl"
tasks = load_dataset(dataset_path)

goal_states = []

for i, task in tqdm(enumerate(tasks), total=len(tasks), desc="Getting goal states"):
    context_code = task["srcContext"]
    theorem_statement = task["theoremStatement"]
    goal_state = get_goal_state(config, context_code, theorem_statement, timeout_per_proof=10)
    goal_states.append({
        "statement_idx": i,
        "goal_state": goal_state
    })

dataset_filename = os.path.basename(dataset_path)
output_filename = f"{dataset_filename.rsplit('.', 1)[0]}_goal_states.jsonl"
with open(output_filename, 'w', encoding='utf-8') as f:
    for result in goal_states:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")
print(f"Goal states saved to {output_filename}")
    