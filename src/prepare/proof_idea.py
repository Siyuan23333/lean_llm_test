import json
import asyncio
import multiprocessing as mp
from multiprocessing import Pool
import time
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict

from tqdm import tqdm
import litellm
from litellm import acompletion

load_dotenv()
litellm.set_verbose = False
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

nl_math_proof_system_prompt_template = """You are an expert mathematican with knowledge about Lean 4 formalization tool. Your task is to interpret the foramlized statement written in **Lean 4 syntax** and generate a **short** proof idea in **natural language**

### Guidelines:
- Generate only the **natural language** proof idea for the given theorem statement
- Your proof idea do not need to be a complete proof but should outline the main steps or concepts involved
- Your proof idea must be concise and clear, within 3 sentences
- Your proof idea should be easy to implement with Lean 4

### Generation format:
[**only** natural language proof idea]
"""

nl_math_proof_prompt_template = """Natural Language Proof Idea Generation Task

### Formalized Statement:
{theorem_statement}

Based on the mathematical statement formalized in Lean 4 syntax, generate a short proof idea in natural language that outlines the main steps and concepts involved in proving the theorem. Use 2-3 sentences and ensure easy to implement with Lean 4.
"""


def load_dataset(dataset_path: str):
    tasks = []
    with open(dataset_path) as f:
        for line in f.readlines():
            task = json.loads(line)
            tasks.append(task)
    return tasks


def generate_proof_idea(theorem_statement: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
    """
    Generate a natural language proof idea for a given Lean 4 theorem statement
    Args:
        theorem_statement: The Lean 4 formalized theorem statement
        temperature: Control randomness in generation
        
    Returns:
        Natural language proof idea as a string
    """
    try:
        user_prompt = nl_math_proof_prompt_template.format(theorem_statement=theorem_statement)
        
        response = litellm.completion(
            model="gemini/gemini-2.5-flash-preview-05-20",
            messages=[
                {"role": "system", "content": nl_math_proof_system_prompt_template},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort="low",
        )
        
        proof_idea = response.choices[0].message.content
        
        if proof_idea is None or proof_idea.strip() == "":
            print(f"Warning: Generated proof idea is empty for theorem: {response}")
        
        return proof_idea
        
    except Exception as e:
        raise Exception(f"Error generating proof idea: {str(e)}")


def generate_proof_ideas(task_path: str, temperature: float = 0.3) -> List[Dict[str, str]]:
    """
    Generate proof ideas for multiple theorem statements
    
    Args:
        theorem_statements: List of Lean 4 formalized theorem statements
        temperature: Control randomness in generation
        
    Returns:
        List of dictionaries containing theorem statements and their proof ideas
    """
    
    dataset_filename = os.path.basename(task_path)
    output_filename = f"{dataset_filename}_proof_ideas.jsonl"
    
    tasks = load_dataset(task_path)
    
    results = []
    
    for i, task in tqdm(enumerate(tasks), total=len(tasks), desc="Generating proof ideas"):
        statement = task["theoremStatement"]
        try:
            proof_idea = None
            n_tries = 0
            while n_tries < 5 and proof_idea is None:
                proof_idea = generate_proof_idea(statement, temperature)
                n_tries += 1
            results.append({
                "statement_idx": i,
                "proof_idea": proof_idea
            })
        except Exception as e:
            print(f"Error processing theorem {i}: {str(e)}")
            results.append({
                "statement_idx": i,
                "proof_idea": None
            })
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    print(f"Proof ideas saved to {output_filename}")
    
    return results


def generate_proof_ideas_for_null(current_proof_idea_path, dataset_path, temperature = 0.3, max_tokens = 4096):
    """
    Generate proof ideas for theorem statements that currently have null proof ideas
    Args:
        current_proof_ideas: List of dictionaries containing theorem statements and their current proof ideas
        temperature: Control randomness in generation
    """
    
    tasks = load_dataset(dataset_path)
    
    current_proof_ideas = []
    
    with open(current_proof_idea_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            current_proof_ideas.append(item)
    
    for task, item in tqdm(zip(tasks, current_proof_ideas)):
        n_tries = 0
        while item["proof_idea"] is None and n_tries < 3:
            try:
                new_proof_idea = generate_proof_idea(task["theoremStatement"], temperature, max_tokens)
                assert new_proof_idea is not None, "Generated proof idea is None"
                item["proof_idea"] = new_proof_idea
            except Exception as e:
                print(f"Error generating proof idea for theorem {item['statement_idx']}: {str(e)}")
                item["proof_idea"] = None
            n_tries += 1
    
    with open(current_proof_idea_path, 'w', encoding='utf-8') as f:
        for item in current_proof_ideas:
            f.write(json.dumps(item) + "\n")
            
    print(f"New Proof ideas saved back to {current_proof_idea_path}")
    
    
dataset_path = "/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f.jsonl"
# generate_proof_ideas(dataset_path, temperature=0.3)

generate_proof_ideas_for_null(
    "/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f_proof_ideas.jsonl",
    dataset_path,
    temperature=0.1,
    max_tokens=3000
)

