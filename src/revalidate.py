import json
import os

from lean_interact import *
from lean_interact.interface import LeanError
from tqdm import tqdm

def load_dataset(dataset_path: str):
    tasks = []
    with open(dataset_path) as f:
        for line in f.readlines():
            task = json.loads(line)
            tasks.append(task)
    return tasks


def load_generation(generation_path: str):
    with open(generation_path) as f:
        lines = f.readlines()
        settings = json.loads(lines[0])["experiment_setting"]
        generations = json.loads(lines[1])["generation_results"]
    return settings, generations
      

def check_context_proofs(args: tuple[int, LeanREPLConfig, int, str, str, list[str]]):
    """
    Check the correctness of the given proofs for a given context and declaration to prove.
    """
    idx, repl_config, timeout_per_proof, context_code, theorem_statement, proofs = args

    server = LeanServer(repl_config)
    context_res = server.run(Command(cmd=context_code))
    assert not isinstance(context_res, LeanError)
    context_env = context_res.env

    correctness = []
    error_messages = []
    error_positions = []
    compiled_line_counts = []
    
    for proof in proofs:
        try:
            lean_output = server.run(
                Command(cmd=theorem_statement + " := " + proof, env=context_env), timeout=timeout_per_proof
            )
            if not isinstance(lean_output, LeanError) and lean_output.lean_code_is_valid(allow_sorry=False):
                correctness.append(True)
                error_messages.append(None)
                error_positions.append(None)
                compiled_line_counts.append(len(proof.splitlines()))
            elif isinstance(lean_output, LeanError):
                correctness.append(False)
                error_messages.append(lean_output.message)
                error_positions.append(None)
                compiled_line_counts.append(None)
            else:
                correctness.append(False)
                messages = lean_output.messages
                message = messages[0]
                error_messages.append(message.data)
                error_positions.append({
                    'start_pos': (message.start_pos.line, message.start_pos.column),
                    'end_pos': (message.end_pos.line, message.end_pos.column)
                } if message.start_pos and message.end_pos else None)
                compiled_line_counts.append(message.start_pos.line - len(theorem_statement.splitlines()) if message.start_pos else None)
                
        except (TimeoutError, ConnectionAbortedError, json.JSONDecodeError):
            correctness.append(None)
            error_positions.append(None)
            error_messages.append(None)
            compiled_line_counts.append(None)

    return idx, correctness, error_positions, error_messages, compiled_line_counts



config = LeanREPLConfig(project=LocalProject("/Users/siyuange/Documents/lean_llm_test/miniF2F-lean4"))
dataset_path = "/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f.jsonl"

dir_path = "/Users/siyuange/Documents/lean_llm_test/results/minif2f/proof_idea"

generation_paths = []

for filename in os.listdir(dir_path):
    if filename.endswith("_generation.jsonl"):
        generation_paths.append(os.path.join(dir_path, filename))

for generation_path in generation_paths:
    validation_path = generation_path.replace("generation", "validation")
    tasks = load_dataset(dataset_path)
    settings, generations = load_generation(generation_path)

    print(f"Loaded generations from {generation_path}.")

    with open(validation_path) as f:
        lines = f.readlines()
        settings = json.loads(lines[0])["experiment_setting"]
        validations = json.loads(lines[1])["validation_results"]

    revalidate = []

    for i, result in enumerate(validations):
        expected_len = 6
        if result["error_messages"] is None or result["error_positions"] is None or result["correctness"] is None:
            revalidate.append(i)
            continue
        if (len(result["error_messages"]) != expected_len):
            revalidate.append(i)
            continue
        if(len(result["error_positions"]) != expected_len):
            revalidate.append(i)
            continue
        if(len(result["correctness"]) != expected_len):
            revalidate.append(i)
            continue
        if any(correct is None for correct in result["correctness"]):
            revalidate.append(i)
            continue


    for idx in tqdm(revalidate):
      
        task = tasks[idx]
        generation = generations[idx]

        context_code = task["srcContext"]
        theorem_statement = task["theoremStatement"]
        proofs = generation["candidates"]

        n_tries = 0
        
        correctness = None
        error_positions = None
        error_messages = None
        compiled_line_counts = None
        
        while correctness is None and n_tries < 5:
            try:
                idx, correctness, error_positions, error_messages, compiled_line_counts = check_context_proofs(
                    (idx, config, 90, context_code, theorem_statement, proofs)
                )
            except Exception as e:
                print(f"Error processing theorem {idx}: {str(e)}")
            n_tries += 1

        validation_result = {
            "statement_idx": idx,
            "correctness": correctness,
            "error_positions": error_positions,
            "error_messages": error_messages,
            "compiled_line_counts": compiled_line_counts,
        }

        validations[idx] = validation_result
        
    with open(validation_path, "w") as f:
        f.write(json.dumps({"experiment_setting": settings}) + '\n')
        f.write(json.dumps({"validation_results": validations}) + '\n')