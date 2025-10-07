import json
from pathlib import Path
import os

def load_jsonl(file_path):
    """Load a JSONL file and return a list of JSON objects."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def combine_files(problems_file, generation_file, validation_file, output_file):
    """Combine the three JSONL files into the specified format."""
    
    # Load all files
    print(f"Loading files for {os.path.basename(generation_file)}...")
    problems_data = load_jsonl(problems_file)
    generation_data = load_jsonl(generation_file)
    validation_data = load_jsonl(validation_file)
    
    # Extract experiment settings (should be the same in both generation and validation)
    generation_settings = generation_data[0]["experiment_setting"]
    validation_settings = validation_data[0]["experiment_setting"]
    
    # Use generation settings as the base (they should be the same except for model and timestamp)
    experiment_setting = generation_settings.copy()
    
    # Extract generation and validation results
    generation_results = {}
    validation_results = {}
    
    # Process generation results
    for item in generation_data:
        if "generation_results" in item:
            for result in item["generation_results"]:
                stmt_idx = result["statement_idx"]
                generation_results[stmt_idx] = result
    
    # Process validation results
    for item in validation_data:
        if "validation_results" in item:
            for result in item["validation_results"]:
                stmt_idx = result["statement_idx"]
                validation_results[stmt_idx] = result
    
    # Create the combined structure
    combined_data = {
        "experiment_setting": experiment_setting,
        "results": {}
    }
    
    # Process each problem
    print("Combining data...")
    for stmt_idx, problem in enumerate(problems_data):
        if stmt_idx in generation_results and stmt_idx in validation_results:
            gen_result = generation_results[stmt_idx]
            val_result = validation_results[stmt_idx]
            
            # Create candidates list
            candidates = []
            n_candidates = len(gen_result["candidates"])
            
            for i in range(n_candidates):
                if val_result["correctness"] is None:
                    candidate = {
                        "proof": gen_result["candidates"][i],
                        "is_correct": None,
                        "duration": gen_result["durations"][i],
                        "prompt_tokens": gen_result["prompt_tokens"][i],
                        "completion_tokens": gen_result["completion_tokens"][i],
                        "total_tokens": gen_result["total_tokens"][i],
                        "compiled_lines": None,
                        "error_message": None,
                        "error_position": None
                    }
                else:
                    candidate = {
                        "proof": gen_result["candidates"][i],
                        "is_correct": val_result["correctness"][i],
                        "duration": gen_result["durations"][i],
                        "prompt_tokens": gen_result["prompt_tokens"][i],
                        "completion_tokens": gen_result["completion_tokens"][i],
                        "total_tokens": gen_result["total_tokens"][i],
                        "compiled_lines": val_result["compiled_line_counts"][i],
                        "error_message": val_result["error_messages"][i],
                        "error_position": val_result["error_positions"][i]
                    }
                candidates.append(candidate)
            
            # Create the result entry
            combined_data["results"][problem["theoremName"]] = {
                "theoremStatement": problem["theoremStatement"],
                "theoremName": problem["theoremName"],
                "candidates": candidates
            }
        else:
            print(f"Warning: Missing generation or validation data for statement {stmt_idx}")
    
    # Write the combined data to output file
    print(f"Writing combined data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully combined {len(combined_data['results'])} problems into {output_file}")
    
    # Print some statistics
    total_candidates = sum(len(result["candidates"]) for result in combined_data["results"].values())
    correct_candidates = sum(
        sum(1 for candidate in result["candidates"] if candidate["is_correct"]) 
        for result in combined_data["results"].values()
    )
    
    print(f"Statistics:")
    print(f"  Total problems: {len(combined_data['results'])}")
    print(f"  Total candidates: {total_candidates}")
    print(f"  Correct candidates: {correct_candidates}")
    print(f"  Success rate: {correct_candidates/total_candidates*100:.2f}%")

def main():
    problems_file = "/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f.jsonl"
    
    generation_dir = "/Users/siyuange/Documents/lean_llm_test/results/minif2f/false_attempts"
    
    for filename in os.listdir(generation_dir):
        if not filename.endswith("_generation.jsonl"):
            continue
        generation_file = os.path.join(generation_dir, filename)
        validation_file = generation_file.replace("generation", "validation")
        output_file = generation_file.replace("generation", "results")
        
        # Verify input files exist
        for file_path in [problems_file, generation_file, validation_file]:
            if not Path(file_path).exists():
                print(f"Error: File {file_path} does not exist")
                return
        
        combine_files(problems_file, generation_file, validation_file, output_file)

if __name__ == "__main__":
    main()