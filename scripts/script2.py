import json
import re
from typing import Dict, Any, List
import os

with open('/Users/siyuange/Documents/lean_llm_test/theorem_names.json', 'r') as f:
    data = json.load(f)
    brute_force_theorems = set(data['theorem_names'])    

def extract_category(theorem_name: str) -> str:
    """
    Extract category from theorem name based on the specified rules:
    - imo_* -> "imo"
    - amc12_* -> "amc12"  
    - others -> everything before first numeric part
    """
    if theorem_name.startswith("imo"):
        return "imo"
    elif theorem_name.startswith("amc"):
        return "amc12"
    elif theorem_name.startswith("aime"):
        return "aime"
    elif theorem_name.startswith("mathd_numbertheory"):
        return "mathd_numbertheory"
    elif theorem_name.startswith("mathd_algebra"):
        return "mathd_algebra"
    elif theorem_name.startswith("algebra"):
        return "algebra"
    elif theorem_name.startswith("numbertheory"):
        return "numbertheory"
    elif theorem_name.startswith("induction"):
        return "induction"
    else:
        print(f"Warning: Unrecognized theorem name '{theorem_name}'. Defaulting to 'unknown'.")
        return "unknown"

def can_solve_by_brute_force(theorem_name: str) -> bool:
    return theorem_name in brute_force_theorems


def process_jsonl_file(input_file: str, output_file: str) -> None:
    """
    Process the JSONL file to add category and brute_force fields.
    
    Args:
        input_file: Path to input .jsonl file
        output_file: Path to output .jsonl file
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process each theorem in the results
    if 'results' in data:
        for theorem_name, theorem_data in data['results'].items():
            # Extract category
            category = extract_category(theorem_name)
            
            # Check if can be solved by brute force
            brute_force = can_solve_by_brute_force(theorem_name)
            
            # Add the new fields
            theorem_data['category'] = category
            theorem_data['brute_force'] = brute_force
            
            print(f"Processed {theorem_name}: category='{category}', brute_force={brute_force}")
    
    # Write the updated data to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessing complete! Updated file saved to: {output_file}")

def analyze_categories(data: Dict[str, Any]) -> None:
    """
    Analyze the distribution of categories and brute force problems.
    """
    if 'results' not in data:
        return
    
    category_counts = {}
    brute_force_counts = {'True': 0, 'False': 0}
    category_brute_force = {}
    
    for theorem_name, theorem_data in data['results'].items():
        category = theorem_data.get('category', 'unknown')
        brute_force = theorem_data.get('brute_force', False)
        
        # Count categories
        category_counts[category] = category_counts.get(category, 0) + 1
        
        # Count brute force
        brute_force_counts[str(brute_force)] += 1
        
        # Count brute force by category
        if category not in category_brute_force:
            category_brute_force[category] = {'True': 0, 'False': 0}
        category_brute_force[category][str(brute_force)] += 1
    
    print("\n" + "="*50)
    print("ANALYSIS SUMMARY")
    print("="*50)
    
    print(f"\nTotal theorems: {len(data['results'])}")
    
    print(f"\nCategory distribution:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")
    
    print(f"\nBrute force distribution:")
    total = sum(brute_force_counts.values())
    for bf_status, count in brute_force_counts.items():
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"  {bf_status}: {count} ({percentage:.1f}%)")
    
    print(f"\nBrute force by category:")
    for category in sorted(category_brute_force.keys()):
        bf_data = category_brute_force[category]
        total_cat = bf_data['True'] + bf_data['False']
        bf_pct = (bf_data['True'] / total_cat) * 100 if total_cat > 0 else 0
        print(f"  {category}: {bf_data['True']}/{total_cat} ({bf_pct:.1f}% brute force)")

def main():
    """
    Main function to process the JSONL file.
    """
    # File paths - modify these as needed
    
    setting = "proof_idea"
    
    dir_path = f"/Users/siyuange/Documents/lean_llm_test/results/minif2f-results/{setting}"
    output_dir = f"/Users/siyuange/Documents/lean_llm_test/results/minif2f-results/enhanced/{setting}"
    
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(dir_path):
        if not filename.endswith("_results.jsonl"):
            continue
        
        input_file = os.path.join(dir_path, filename)
        output_file = os.path.join(output_dir, filename)
        
        print(f"Processing file: {input_file}")
        
        try:
            process_jsonl_file(input_file, output_file)
            print(f"Processed file saved to: {output_file}")
        except Exception as e:
            print(f"Error processing file {input_file}: {e}")
            

if __name__ == "__main__":
    main()