import json
import os
import pandas as pd
from pathlib import Path
import numpy as np

def load_jsonl_file(filepath):
    """Load a single JSONL file and return the parsed data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_statement_metrics(statement_data):
    """Calculate metrics for a single theorem statement."""
    candidates = statement_data.get('candidates', [])
    
    if not candidates:
        return None
    
    # Extract metrics from all candidates
    durations = []
    prompt_tokens = []
    completion_tokens = []
    total_tokens = []
    compiled_lines = []
    
    for candidate in candidates:
        if 'duration' in candidate:
            durations.append(candidate['duration'])
        if 'prompt_tokens' in candidate:
            prompt_tokens.append(candidate['prompt_tokens'])
        if 'completion_tokens' in candidate:
            completion_tokens.append(candidate['completion_tokens'])
        if 'total_tokens' in candidate:
            total_tokens.append(candidate['total_tokens'])
        if 'compiled_lines' in candidate:
            compiled_lines.append(candidate['compiled_lines'])
    
    # Calculate averages for this statement
    statement_metrics = {}
    
    if durations:
        statement_metrics['avg_duration'] = np.mean(durations)
    if prompt_tokens:
        statement_metrics['avg_prompt_tokens'] = np.mean(prompt_tokens)
    if completion_tokens:
        statement_metrics['avg_completion_tokens'] = np.mean(completion_tokens)
    if total_tokens:
        statement_metrics['avg_total_tokens'] = np.mean(total_tokens)
    
    # Calculate compiled ratio (compiled_lines > 0 means successful compilation)
    if compiled_lines:
        compiled_ratio = sum(1 for lines in compiled_lines if lines and lines > 0) / len(compiled_lines)
        statement_metrics['compiled_ratio'] = compiled_ratio
    
    return statement_metrics

def process_jsonl_file(filepath):
    """Process a single JSONL file and return aggregated metrics."""
    data = load_jsonl_file(filepath)
    
    # Extract used_hints from experiment_setting
    used_hints = data.get('experiment_setting', {}).get('used_hints', 'Unknown')
    
    # Process all theorem statements
    results = data.get('results', {})
    
    statement_metrics_list = []
    
    for statement_name, statement_data in results.items():
        metrics = calculate_statement_metrics(statement_data)
        if metrics:
            statement_metrics_list.append(metrics)
    
    if not statement_metrics_list:
        return None
    
    # Calculate overall averages across all statements
    overall_metrics = {
        'used_hints': used_hints,
        'avg_duration': np.mean([m['avg_duration'] for m in statement_metrics_list if 'avg_duration' in m]),
        'avg_prompt_tokens': np.mean([m['avg_prompt_tokens'] for m in statement_metrics_list if 'avg_prompt_tokens' in m]),
        'avg_completion_tokens': np.mean([m['avg_completion_tokens'] for m in statement_metrics_list if 'avg_completion_tokens' in m]),
        'avg_total_tokens': np.mean([m['avg_total_tokens'] for m in statement_metrics_list if 'avg_total_tokens' in m]),
        'avg_compiled_ratio': np.mean([m['compiled_ratio'] for m in statement_metrics_list if 'compiled_ratio' in m])
    }
    
    return overall_metrics

def analyze_directory(directory_path, output_csv_path):
    """Analyze all JSONL files in a directory and save results to CSV."""
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    all_results = []
    
    # Process all .jsonl files in the directory
    jsonl_files = list(directory_path.glob("*.jsonl"))
    
    if not jsonl_files:
        raise FileNotFoundError(f"No .jsonl files found in directory: {directory_path}")
    
    print(f"Found {len(jsonl_files)} .jsonl files to process...")
    
    for filepath in jsonl_files:
        print(f"Processing: {filepath.name}")
        try:
            metrics = process_jsonl_file(filepath)
            if metrics:
                all_results.append(metrics)
                print(f"  ✓ Processed successfully (used_hints: {metrics['used_hints']})")
            else:
                print(f"  ⚠ No valid data found in {filepath.name}")
        except Exception as e:
            print(f"  ✗ Error processing {filepath.name}: {e}")
    
    if not all_results:
        raise ValueError("No valid results found in any of the files")
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(all_results)
    
    # Reorder columns as requested
    column_order = [
        'used_hints', 
        'avg_duration',
        'avg_prompt_tokens',
        'avg_completion_tokens', 
        'avg_total_tokens', 
        'avg_compiled_ratio'
    ]
    
    # Only include columns that exist in the data
    available_columns = [col for col in column_order if col in df.columns]
    df = df[available_columns]
    
    # Round numerical values for better readability
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].round(4)
    
    # Save to CSV
    df.to_csv(output_csv_path, index=False)
    
    print(f"\n✓ Results saved to: {output_csv_path}")
    print(f"✓ Processed {len(all_results)} files successfully")
    print("\nSummary of results:")
    print(df.to_string(index=False))
    
    return df

if __name__ == "__main__":
    # Configuration
    model_name = "gpt-4o"
    DIRECTORY_PATH = f"/Users/siyuange/Documents/lean_llm_test/results/results_by_model/{model_name}"  # Change this to your directory path
    OUTPUT_CSV_PATH = f"{model_name}.csv"
    
    results_df = analyze_directory(DIRECTORY_PATH, OUTPUT_CSV_PATH)
    print(f"\n🎉 Analysis complete! Results saved to '{OUTPUT_CSV_PATH}'")