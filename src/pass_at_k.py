import json
import os
import pandas as pd
import glob
from collections import defaultdict
import math

def load_results_from_directory(directory_path):
    """Load all JSONL files matching the pattern from directory, organized by model"""
    pattern = os.path.join(directory_path, "experiment_results*_*_wo_*_results.jsonl")
    files = glob.glob(pattern)
    
    model_results = {}
    
    for file_path in files:
        print(f"Loading {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Extract model name from the data or filename
            model_name = data.get('experiment_setting', {}).get('model', 'unknown')
            reasoning_effort = data.get('experiment_setting', {}).get('reasoning_effort', 'unknown')
            
            model_name = model_name + '-' + reasoning_effort
            
            # If model name is still unknown, try to extract from filename
            if model_name == 'unknown':
                filename = os.path.basename(file_path)
                # Parse filename to extract model name
                # Format: experiment_results*_*<model_name>_wo_<timestamp>_results.jsonl
                parts = filename.replace('.jsonl', '').split('_wo_')
                if len(parts) >= 2:
                    model_part = parts[0]
                    # Extract model name (everything after the last underscore before _wo_)
                    model_name = model_part.split('_')[-1] if '_' in model_part else model_part
            
            if model_name not in model_results:
                model_results[model_name] = []
            
            # Process each theorem result
            for theorem_name, theorem_data in data.get('results', {}).items():
                result = {
                    'theorem_name': theorem_name,
                    'theorem_statement': theorem_data.get('theoremStatement', ''),
                    'category': theorem_data.get('category', 'unknown'),
                    'brute_force': theorem_data.get('brute_force', False),
                    'candidates': theorem_data.get('candidates', [])
                }
                model_results[model_name].append(result)
    
    return model_results

def compute_pass_at_k(candidates, k):
    """Compute pass@k metric for a list of candidates"""
    if not candidates:
        return 0.0
    
    # Count correct solutions
    correct_count = sum(1 for c in candidates if c.get('is_correct', False))
    n = len(candidates)
    
    if k > n:
        k = n
    
    if correct_count == 0:
        return 0.0
    
    # pass@k = 1 - C(n-correct, k) / C(n, k)
    # where C(n,k) is binomial coefficient
    
    if correct_count >= k:
        return 1.0
    
    try:
        numerator = math.comb(n - correct_count, k)
        denominator = math.comb(n, k)
        return 1.0 - (numerator / denominator)
    except:
        return 0.0

def has_correct_proof(candidates):
    """Check if there's at least one correct proof"""
    return any(c.get('is_correct', False) for c in candidates)

def analyze_results(results, model_name):
    """Analyze results and compute all requested metrics for a specific model"""
    
    # Group by different criteria
    analyses = {
        'all_statements': results,
        'by_category': {},
        'brute_force_true': [r for r in results if r['brute_force']],
        'brute_force_false': [r for r in results if not r['brute_force']]
    }
    
    # Group by category
    for result in results:
        category = result['category']
        if category not in analyses['by_category']:
            analyses['by_category'][category] = []
        analyses['by_category'][category].append(result)
    
    # Compute metrics for each group
    metrics_data = []
    
    # All statements
    group_results = analyses['all_statements']
    if group_results:
        correct_count = sum(1 for r in group_results if has_correct_proof(r['candidates']))
        total_count = len(group_results)
        pass_at_1 = sum(compute_pass_at_k(r['candidates'], 1) for r in group_results) / total_count
        pass_at_5 = sum(compute_pass_at_k(r['candidates'], 5) for r in group_results) / total_count
        
        sum_ratio = 0
        
        for r in group_results:
            compiled_lines_count = 0
            total_lines_count = 0
            for c in r['candidates']:
                compiled_lines_count += c['compiled_lines'] if c['compiled_lines'] is not None else 0
                total_lines_count += c['proof'].count('\n') + 1 if c['compiled_lines'] is not None else 0

            ratio = compiled_lines_count / total_lines_count if total_lines_count > 0 else 0
            sum_ratio += ratio
            
        avg_compiled_ratio = sum_ratio / total_count if total_count > 0 else 0
        
        
        metrics_data.append({
            'model': model_name,
            'group_type': 'all_statements',
            'group_name': 'all',
            'total_theorems': total_count,
            'theorems_with_correct_proof': correct_count,
            'percentage_with_correct_proof': (correct_count / total_count) * 100,
            'pass_at_1': pass_at_1,
            'pass_at_5': pass_at_5,
            'avg_compiled_ratio': avg_compiled_ratio
        })
    
    # By category
    for category, group_results in analyses['by_category'].items():
        if group_results:
            correct_count = sum(1 for r in group_results if has_correct_proof(r['candidates']))
            total_count = len(group_results)
            pass_at_1 = sum(compute_pass_at_k(r['candidates'], 1) for r in group_results) / total_count
            pass_at_5 = sum(compute_pass_at_k(r['candidates'], 5) for r in group_results) / total_count
            
            sum_ratio = 0
        
            for r in group_results:
                compiled_lines_count = 0
                total_lines_count = 0
                for c in r['candidates']:
                    compiled_lines_count += c['compiled_lines'] if c['compiled_lines'] is not None else 0
                    total_lines_count += c['proof'].count('\n') + 1 if c['compiled_lines'] is not None else 0

                ratio = compiled_lines_count / total_lines_count if total_lines_count > 0 else 0
                sum_ratio += ratio
                
            avg_compiled_ratio = sum_ratio / total_count if total_count > 0 else 0
            
            metrics_data.append({
                'model': model_name,
                'group_type': 'category',
                'group_name': category,
                'total_theorems': total_count,
                'theorems_with_correct_proof': correct_count,
                'percentage_with_correct_proof': (correct_count / total_count) * 100,
                'pass_at_1': pass_at_1,
                'pass_at_5': pass_at_5,
                'avg_compiled_ratio': avg_compiled_ratio
            })
    
    # Brute force = True
    group_results = analyses['brute_force_true']
    if group_results:
        correct_count = sum(1 for r in group_results if has_correct_proof(r['candidates']))
        total_count = len(group_results)
        pass_at_1 = sum(compute_pass_at_k(r['candidates'], 1) for r in group_results) / total_count
        pass_at_5 = sum(compute_pass_at_k(r['candidates'], 5) for r in group_results) / total_count
        
        sum_ratio = 0
        
        for r in group_results:
            compiled_lines_count = 0
            total_lines_count = 0
            for c in r['candidates']:
                compiled_lines_count += c['compiled_lines'] if c['compiled_lines'] is not None else 0
                total_lines_count += c['proof'].count('\n') + 1 if c['compiled_lines'] is not None else 0

            ratio = compiled_lines_count / total_lines_count if total_lines_count > 0 else 0
            sum_ratio += ratio
            
        avg_compiled_ratio = sum_ratio / total_count if total_count > 0 else 0
        
        metrics_data.append({
            'model': model_name,
            'group_type': 'brute_force',
            'group_name': 'true',
            'total_theorems': total_count,
            'theorems_with_correct_proof': correct_count,
            'percentage_with_correct_proof': (correct_count / total_count) * 100,
            'pass_at_1': pass_at_1,
            'pass_at_5': pass_at_5,
            'avg_compiled_ratio': avg_compiled_ratio
        })
    
    # Brute force = False
    group_results = analyses['brute_force_false']
    if group_results:
        correct_count = sum(1 for r in group_results if has_correct_proof(r['candidates']))
        total_count = len(group_results)
        pass_at_1 = sum(compute_pass_at_k(r['candidates'], 1) for r in group_results) / total_count
        pass_at_5 = sum(compute_pass_at_k(r['candidates'], 5) for r in group_results) / total_count
        
        sum_ratio = 0
        
        for r in group_results:
            compiled_lines_count = 0
            total_lines_count = 0
            for c in r['candidates']:
                compiled_lines_count += c['compiled_lines'] if c['compiled_lines'] is not None else 0
                total_lines_count += c['proof'].count('\n') + 1 if c['compiled_lines'] is not None else 0

            ratio = compiled_lines_count / total_lines_count if total_lines_count > 0 else 0
            sum_ratio += ratio
            
        avg_compiled_ratio = sum_ratio / total_count if total_count > 0 else 0
        
        metrics_data.append({
            'model': model_name,
            'group_type': 'brute_force',
            'group_name': 'false',
            'total_theorems': total_count,
            'theorems_with_correct_proof': correct_count,
            'percentage_with_correct_proof': (correct_count / total_count) * 100,
            'pass_at_1': pass_at_1,
            'pass_at_5': pass_at_5,
            'avg_compiled_ratio': avg_compiled_ratio
        })
    
    return metrics_data

def main():
    # Set the directory path where your JSONL files are located
    directory_path = input("Enter the directory path containing the JSONL files: ").strip()
    
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist!")
        return
    
    # Load all results organized by model
    print("Loading results from all files...")
    model_results = load_results_from_directory(directory_path)
    
    if not model_results:
        print("No results found!")
        return
    
    print(f"Found results for {len(model_results)} models")
    for model, results in model_results.items():
        print(f"  {model}: {len(results)} theorem results")
    
    # Analyze results for each model
    all_metrics_data = []
    
    for model_name, results in model_results.items():
        print(f"\nComputing metrics for {model_name}...")
        metrics_data = analyze_results(results, model_name)
        all_metrics_data.extend(metrics_data)
    
    # Create DataFrame
    df = pd.DataFrame(all_metrics_data)
    
    # Save to CSV files
    output_dir = directory_path
    
    # All metrics in one file (all models combined)
    all_metrics_file = os.path.join(output_dir, "theorem_proving_metrics_all_models.csv")
    df.to_csv(all_metrics_file, index=False)
    print(f"\nAll metrics saved to: {all_metrics_file}")
    
    # Separate files by group type (all models combined)
    for group_type in df['group_type'].unique():
        group_df = df[df['group_type'] == group_type]
        group_file = os.path.join(output_dir, f"theorem_proving_metrics_{group_type}_all_models.csv")
        group_df.to_csv(group_file, index=False)
        print(f"{group_type} metrics (all models) saved to: {group_file}")
    
    # Separate files for each model
    for model_name in df['model'].unique():
        model_df = df[df['model'] == model_name]
        model_file = os.path.join(output_dir, f"theorem_proving_metrics_{model_name.replace('/', '_').replace('-', '_')}.csv")
        model_df.to_csv(model_file, index=False)
        print(f"{model_name} metrics saved to: {model_file}")
        
        # Also create separate files by group type for each model
        for group_type in model_df['group_type'].unique():
            model_group_df = model_df[model_df['group_type'] == group_type]
            model_group_file = os.path.join(output_dir, f"theorem_proving_metrics_{model_name.replace('/', '_').replace('-', '_')}_{group_type}.csv")
            model_group_df.to_csv(model_group_file, index=False)
    
    # Print summary for each model
    print("\n" + "="*70)
    print("SUMMARY BY MODEL")
    print("="*70)
    
    for model_name in sorted(df['model'].unique()):
        model_df = df[df['model'] == model_name]
        print(f"\n{model_name.upper()}")
        print("-" * len(model_name))
        
        for _, row in model_df.iterrows():
            print(f"\n  {row['group_type'].upper()}: {row['group_name']}")
            print(f"    Total theorems: {row['total_theorems']}")
            print(f"    Theorems with correct proof: {row['theorems_with_correct_proof']} ({row['percentage_with_correct_proof']:.1f}%)")
            print(f"    Pass@1: {row['pass_at_1']:.3f}")
            print(f"    Pass@5: {row['pass_at_5']:.3f}")
    
    # Print comparison table for all statements
    print("\n" + "="*70)
    print("MODEL COMPARISON - ALL STATEMENTS")
    print("="*70)
    all_statements_df = df[df['group_type'] == 'all_statements'].sort_values('pass_at_1', ascending=False)
    print(f"{'Model':<25} {'Total':<8} {'Correct':<8} {'%Correct':<10} {'Pass@1':<8} {'Pass@5':<8}")
    print("-" * 70)
    for _, row in all_statements_df.iterrows():
        print(f"{row['model']:<25} {row['total_theorems']:<8} {row['theorems_with_correct_proof']:<8} {row['percentage_with_correct_proof']:<10.1f} {row['pass_at_1']:<8.3f} {row['pass_at_5']:<8.3f}")


if __name__ == "__main__":
    main()