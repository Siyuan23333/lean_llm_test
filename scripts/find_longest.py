import json
import heapq
import os
import glob
from typing import List, Tuple, Dict, Any

def find_longest_correct_proofs_directory(directory_path: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Find the theorems with the longest correct proofs across all JSONL files in a directory.
    
    Args:
        directory_path: Path to the directory containing JSONL files
        top_k: Number of top theorems to return (default: 3)
    
    Returns:
        List of dictionaries containing theorem info and longest correct proof
    """
    
    # Use a min-heap to keep track of top k longest proofs across all files
    min_heap = []
    
    # Find all JSONL files in the directory
    jsonl_files = glob.glob(os.path.join(directory_path, "*.jsonl"))
    
    if not jsonl_files:
        print(f"No JSONL files found in directory: {directory_path}")
        return []
    
    print(f"Found {len(jsonl_files)} JSONL files to analyze:")
    for file_path in jsonl_files:
        print(f"  - {os.path.basename(file_path)}")
    print()
    
    # Process each JSONL file
    for file_path in jsonl_files:
        print(f"Processing {os.path.basename(file_path)}...")
        
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                
                # Extract results for each theorem
                results = data.get('results', {})
                
                for theorem_name, theorem_data in results.items():
                    theorem_statement = theorem_data.get('theoremStatement', '')
                    candidates = theorem_data.get('candidates', [])
                    
                    # Find the longest correct proof for this theorem
                    longest_correct_proof = ""
                    longest_proof_length = 0
                    longest_proof_info = None
                    
                    for candidate in candidates:
                        if candidate.get('is_correct', False):
                            proof = candidate.get('proof', '')
                            proof_length = len(proof)
                            
                            if proof_length > longest_proof_length:
                                longest_proof_length = proof_length
                                longest_correct_proof = proof
                                longest_proof_info = candidate
                    
                    # Only consider theorems that have at least one correct proof
                    if longest_proof_length > 0:
                        theorem_info = {
                            'theorem_name': theorem_name,
                            'theorem_statement': theorem_statement,
                            'proof': longest_correct_proof,
                            'proof_length': longest_proof_length,
                            'proof_info': longest_proof_info,
                            'source_file': os.path.basename(file_path)
                        }
                        
                        # Append experiment settings to theorem info
                        theorem_info['experiment_setting'] = data.get('experiment_setting', {})
                        
                        # Use min-heap to maintain top k longest proofs
                        if len(min_heap) < top_k:
                            heapq.heappush(min_heap, (longest_proof_length, theorem_name, theorem_info))
                        elif longest_proof_length > min_heap[0][0]:
                            heapq.heapreplace(min_heap, (longest_proof_length, theorem_name, theorem_info))
                
                 # combine theorem info in the topwith settings         
                        
        
        except json.JSONDecodeError as e:
            print(f"  Warning: Error reading {os.path.basename(file_path)}: {e}")
            continue
        except Exception as e:
            print(f"  Warning: Error processing {os.path.basename(file_path)}: {e}")
            continue
    
    # Extract theorems from heap and sort by length (descending)
    top_theorems = [theorem_info for _, _, theorem_info in min_heap]
    top_theorems.sort(key=lambda x: x['proof_length'], reverse=True)
    
    # For each theorem info in top_theorems, add the experiment settings
    
    return top_theorems

def find_longest_correct_proofs_single_file(jsonl_file_path: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Find the theorems with the longest correct proofs in a single JSONL file.
    
    Args:
        jsonl_file_path: Path to the JSONL file containing experiment results
        top_k: Number of top theorems to return (default: 3)
    
    Returns:
        List of dictionaries containing theorem info and longest correct proof
    """
    
    # Use a min-heap to keep track of top k longest proofs
    min_heap = []
    
    with open(jsonl_file_path, 'r') as file:
        data = json.loads(file)
        settings = data['experiment_setting']
        
        # Extract results for each theorem
        results = data.get('results', {})
        
        for theorem_name, theorem_data in results.items():
            theorem_statement = theorem_data.get('theoremStatement', '')
            candidates = theorem_data.get('candidates', [])
            
            # Find the longest correct proof for this theorem
            longest_correct_proof = ""
            longest_proof_length = 0
            longest_proof_info = None
            
            for candidate in candidates:
                if candidate.get('is_correct', False):
                    proof = candidate.get('proof', '')
                    proof_length = len(proof)
                    
                    if proof_length > longest_proof_length:
                        longest_proof_length = proof_length
                        longest_correct_proof = proof
                        longest_proof_info = candidate
            
            # Only consider theorems that have at least one correct proof
            if longest_proof_length > 0:
                theorem_info = {
                    'theorem_name': theorem_name,
                    'theorem_statement': theorem_statement,
                    'proof': longest_correct_proof,
                    'proof_length': longest_proof_length,
                    'proof_info': longest_proof_info,
                    'source_file': os.path.basename(jsonl_file_path)
                }
                
                
                
                # Use min-heap to maintain top k longest proofs
                if len(min_heap) < top_k:
                    heapq.heappush(min_heap, (longest_proof_length, theorem_name, theorem_info))
                elif longest_proof_length > min_heap[0][0]:
                    heapq.heapreplace(min_heap, (longest_proof_length, theorem_name, theorem_info))
    
    # Extract theorems from heap and sort by length (descending)
    top_theorems = [theorem_info for _, _, theorem_info in min_heap]
    top_theorems.sort(key=lambda x: x['proof_length'], reverse=True)
    
    
    return top_theorems

def save_results(theorems: List[Dict[str, Any]], output_file: str = 'longest_correct_proofs.json'):
    """
    Save the results to a JSON file.
    
    Args:
        theorems: List of theorem dictionaries
        output_file: Output file path
    """
    
    # Prepare data for saving (exclude proof_info for cleaner output)
    save_data = []
    for i, theorem in enumerate(theorems, 1):
        save_data.append({
            'rank': i,
            'theorem_name': theorem['theorem_name'],
            'theorem_statement': theorem['theorem_statement'],
            'proof': theorem['proof'],
            'proof_length': theorem['proof_length'],
            'source_file': theorem.get('source_file', 'unknown'),
            'experiment_setting': theorem.get('experiment_setting', {})
        })
    
    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    print(f"Results saved to {output_file}")

def print_results(theorems: List[Dict[str, Any]]):
    """
    Print the results in a readable format.
    
    Args:
        theorems: List of theorem dictionaries
    """
    
    print("=" * 80)
    print("TOP 3 THEOREMS WITH LONGEST CORRECT PROOFS")
    print("=" * 80)
    
    for i, theorem in enumerate(theorems, 1):
        print(f"\n{i}. THEOREM: {theorem['theorem_name']}")
        print(f"   SOURCE FILE: {theorem.get('source_file', 'unknown')}")
        print(f"   PROOF LENGTH: {theorem['proof_length']} characters")
        print(f"   STATEMENT: {theorem['theorem_statement']}")
        print(f"   PROOF:")
        print(f"   {'-' * 60}")
        # Print proof with proper indentation
        proof_lines = theorem['proof'].split('\n')
        for line in proof_lines:
            print(f"   {line}")
        print(f"   {'-' * 60}")

def main():
    """
    Main function to run the analysis.
    """
    
    # File path - update this to match your actual file path
    dir_path = input("Enter the path to your JSONL file: ").strip()
    dir_name = os.path.basename(dir_path)
    
    # Find the longest correct proofs
    print("Analyzing proofs...")
    longest_theorems = find_longest_correct_proofs_directory(dir_path, top_k=3)
    
    if not longest_theorems:
        print("No theorems with correct proofs found in the file.")
        return
    
    # Print results
    print_results(longest_theorems)
    
    # Save results
    save_results(longest_theorems, output_file=f'{dir_name}_longest_correct_proofs.json')
    
    print(f"\nAnalysis complete! Found {len(longest_theorems)} theorems with correct proofs.")


if __name__ == "__main__":
    main()