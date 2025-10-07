#!/usr/bin/env python3
"""
Extract theorem statements from a Lean file and convert to JSONL format.
"""

import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional


def read_file(file_path: str) -> str:
    """Read content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {e}")


def extract_statements(lean_content: str) -> List[Dict[str, str]]:
    """
    Alternative extraction method that handles the specific format of your Lean file.
    This method splits on theorem boundaries and processes each complete theorem block.
    """
    statements = []
    
    # Split content by theorem/lemma/def keywords
    parts = re.split(r'\n(?=theorem|lemma|def)', lean_content)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # Check if this part starts with theorem/lemma/def
        match = re.match(r'^(theorem|lemma|def)\s+([a-zA-Z_][a-zA-Z0-9_\']*)', part)
        if not match:
            continue
            
        statement_type = match.group(1)
        theorem_name = match.group(2)
        
        # Find the end of the statement (before := by sorry)
        end_match = re.search(r':=\s*by\s+sorry', part)
        if not end_match:
            continue
            
        # Extract everything from the start to just before :=
        statement_text = part[:end_match.start()].strip()
        
        # Clean up whitespace and newlines
        statement_text = ' '.join(statement_text.split())
        
        statements.append({
            'theoremName': theorem_name,
            'theoremStatement': statement_text
        })
    
    return statements


def create_jsonl(statements: List[Dict[str, str]], src_context: str, output_file: str):
    """Create JSONL file with the extracted statements."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for statement in statements:
                json_obj = {
                    "srcContext": src_context,
                    "theoremStatement": statement['theoremStatement'],
                    "theoremName": statement['theoremName']
                }
                f.write(json.dumps(json_obj, ensure_ascii=False) + '\n')
        print(f"Successfully created {output_file} with {len(statements)} statements.")
    except Exception as e:
        raise Exception(f"Error writing to {output_file}: {e}")


def main():
    lean_file = "/Users/siyuange/Documents/lean_llm_test/miniF2F-lean4/MiniF2F/Test.lean"
    context_file = "/Users/siyuange/Documents/lean_llm_test/miniF2F-lean4/MiniF2F/Minif2fImport.lean"
    output_file = "minif2f.jsonl"
    
    # Read the input files
    print(f"Reading theorem statements from: {lean_file}")
    lean_content = read_file(lean_file)
    
    print(f"Reading source context from: {context_file}")
    src_context = read_file(context_file).strip() + "\nopen BigOperators Real Nat Topology\n"
    
    statements = extract_statements(lean_content)
    
    if not statements:
        print("Warning: No theorem statements found. Check your input file format.")
        return
    
    print(f"Found {len(statements)} theorem statements:")
    for i, stmt in enumerate(statements[:5], 1):  # Show first 5
        print(f"  {i}. {stmt['theoremName']}")
    if len(statements) > 5:
        print(f"  ... and {len(statements) - 5} more")
    
    # Create JSONL file
    print(f"Creating JSONL file: {output_file}")
    create_jsonl(statements, src_context, output_file)
    


if __name__ == "__main__":
    main()