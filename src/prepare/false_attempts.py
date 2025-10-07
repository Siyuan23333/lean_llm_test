import json
import os
from typing import Dict, List


def read_jsonl_file(filepath: str) -> Dict:
    data = {"experiment_setting": None, "results": []}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if "experiment_setting" in parsed:
                data["experiment_setting"] = parsed["experiment_setting"]
            elif "generation_results" in parsed:
                data["results"] = parsed["generation_results"]
            elif "validation_results" in parsed:
                data["results"] = parsed["validation_results"]
    return data

def read_tasks(filepath: str) -> List[Dict]:
    tasks = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            tasks.append(json.loads(line))
    return tasks


def extract_unique_false_proofs(generation_data: Dict, validation_data: Dict, task_data: List[Dict]):
    generation_results = generation_data["results"]
    validation_results = validation_data["results"]
    
    # Create a mapping from statement_idx to validation results
    validation_map = {result["statement_idx"]: result for result in validation_results}
    
    output_data = []
    
    for gen_result in generation_results:
        statement_idx = gen_result["statement_idx"]
        candidates = gen_result["candidates"]
        task = task_data[statement_idx]
        theorem_statement = task["theoremStatement"]
        num_statement_lines = theorem_statement.count('\n') + 1
        
        validation_result = validation_map[statement_idx]
        
        correctness = validation_result["correctness"]
        error_messages = validation_result["error_messages"]
        error_positions = validation_result["error_positions"]
        
        expected_length = len(candidates)
        if len(correctness) != expected_length:
            raise ValueError(f"Mismatch in correctness length for statement {statement_idx}: ")
        
        if len(error_messages) != expected_length:
            raise ValueError(f"Mismatch in error_messages length for statement {statement_idx}: ")
        
        if len(error_positions) != expected_length:
            raise ValueError(f"Mismatch in error_positions length for statement {statement_idx}: ")
        
        # Track unique proofs and their details
        unique_false_attempts = {}  # proof_text -> (error_message, error_position)
        
        for i in range(expected_length):
            candidate = candidates[i]
            is_correct = correctness[i]
            error_message = error_messages[i]
            error_position = error_positions[i]
            
            if is_correct or error_position is None:
                continue
            
            normalized_proof = candidate.replace('\r\n', '\n').replace('\r', '\n')
            error_end_pos = error_position['end_pos']
            error_end_line = error_end_pos[0] - num_statement_lines
            
            false_attempt = '\n'.join(normalized_proof.splitlines()[:error_end_line + 1]).strip()
            
            if false_attempt not in unique_false_attempts:
                unique_false_attempts[false_attempt] = (error_message, error_position)
        
        false_attempts = []
        for false_attempt, (error_message, error_position) in unique_false_attempts.items():
            false_attempts.append({
                "proof": false_attempt,
                "error_message": error_message,
                "error_position": error_position
            })
        
        output_data.append({
            "statement_idx": statement_idx,
            "false_attempts": false_attempts
        })
    
    return output_data


def write_jsonl_file(data: List[Dict], output_filepath: str) -> None:
    """Write data to a JSONL file."""
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
        print(f"Successfully wrote {len(data)} entries to {output_filepath}")
    except Exception as e:
        print(f"Error writing to {output_filepath}: {e}")
        raise


generation_path = "/Users/siyuange/Documents/lean_llm_test/results/minif2f/None/experiment_results_gemini-2.5-flash-preview-05-20_wo_20250620_043058_generation.jsonl"
validation_path = generation_path.replace("generation", "validation")
task_path = "/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f.jsonl"

temp = os.path.basename(generation_path).replace("experiment_results_", "")
model_name = temp.rsplit("_w", 1)[0]
output_path = f"minif2f_{model_name}_false_attempts.jsonl"

print("Loading generation data...")
generation_data = read_jsonl_file(generation_path)
print(f"Found {len(generation_data['results'])} generation results")

print("Loading validation data...")
validation_data = read_jsonl_file(validation_path)
print(f"Found {len(validation_data['results'])} validation results")
print()

print("Loading task data...")
task_data = read_tasks(task_path)
print(f"Found {len(task_data)} tasks in the dataset")
print()

# Extract false proofs
print("Extracting unique incorrect proofs...")
false_proof_data = extract_unique_false_proofs(generation_data, validation_data, task_data)
print()

# Write output
print("Writing results...")
write_jsonl_file(false_proof_data, output_path)

# Summary statistics
total_statements_with_errors = len(false_proof_data)
total_false_attempts = sum(len(entry["false_attempts"]) for entry in false_proof_data)

print(f"\nSummary:")
print(f"- Total statements processed: {len(generation_data['results'])}")
print(f"- Statements with incorrect proofs: {total_statements_with_errors}")
print(f"- Total unique incorrect proofs: {total_false_attempts}")