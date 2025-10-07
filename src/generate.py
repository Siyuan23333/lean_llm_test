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
import random

from tqdm import tqdm
import litellm
from litellm import acompletion

load_dotenv()
litellm.set_verbose = False
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

system_prompt_w_context_template = """You are an expert Lean 4 theorem prover. Your task is to generate formal proofs in **Lean 4 syntax** given a formalized mathematical statement and its code context.

### Guidelines:
- Generate **only** the proof terms that are after ":="
- Your proof must follow Lean 4 syntax and be strict adherence to Lean 4 conventions
- Ensure the indentation are correct for Lean 4
- When sequentially rewritting or applying theorems, write them in separate lines and each line with a tactic
- Use tactics, term-mode proofs, or a combination as appropriate
{additional_guidelines}

### Generation format:
```lean
[**only** formalized proof after ":=" that are syntactically correct Lean 4 code]
```
"""


whole_proof_prompt_w_context_template = """Lean 4 Whole Proof Generation Task

### Code Context:
{src_context}

### Theorem Statement:
{theorem_statement}

{hints_section}
Based on the code context and other information, generate a whole formalized proof that complete the proof of the given statement while ensuring strict adherence to Lean4 syntax and conventions.
"""


system_prompt_wo_context_template = """You are an expert Lean 4 theorem prover. Your task is to generate formal proofs in **Lean 4 syntax** given a formalized mathematical statement.

### Guidelines:
- Generate **only** the proof terms that are after ":="
- Your proof must follow Lean 4 syntax and be strict adherence to Lean 4 conventions
- Your proof should not contain any additional explanations or comments
- Ensure the indentation are correct for Lean 4
- When sequentially rewritting or applying theorems, write them in separate lines and each line with a tactic
- Use tactics, term-mode proofs, or a combination as appropriate
{additional_guidelines}

### Generation format:
```lean
[**only** formalized proof after ":=" that are syntactically correct Lean 4 code]
```
"""


whole_proof_prompt_wo_context_template = """Lean 4 Whole Proof Generation Task

### Theorem Statement:
{theorem_statement}

{hints_section}
Based on the provided context, generate a whole formalized proof that complete the proof of the given statement while ensuring strict adherence to Lean4 syntax and conventions.
"""


def load_dataset(dataset_path):
    tasks = []
    with open(dataset_path) as f:
        for line in f.readlines():
            task = json.loads(line)
            tasks.append(task)
    return tasks


def extract_proof_from_response(response: str) -> str:
        """Extract the proof from the model's response."""
        proof = response
        
        # Remove common markdown code block markers
        if proof.startswith("```"):
            lines = proof.split('\n')
            if len(lines) > 1:
                proof = '\n'.join(lines[1:-1]) if lines[-1].strip() == "```" else '\n'.join(lines[1:])
        
        # Remove ":=" prefix if present
        if proof.startswith(":= "):
            proof = proof[3:].strip()
        
        return proof
      
      
async def timed_completion(system_prompt, prompt, gen_config):
    model = gen_config['model']
    temperature = gen_config['temperature']
    max_tokens = gen_config['max_tokens']
    timeout = gen_config['timeout']
    reasoning_effort = gen_config['reasoning_effort']
    
    start_time = time.time()
    try:
        if reasoning_effort == "None":
            response = await acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                drop_params=True
            )
        else:
            response = await acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                reasoning_effort=reasoning_effort,
                drop_params=True
            )
        end_time = time.time()
        return {
            'response': response,
            'duration': end_time - start_time,
            'success': True
        }
    except Exception as e:
        end_time = time.time()
        return {
            'response': e,
            'duration': end_time - start_time,
            'success': False
        }


async def generate(system_prompt: str, prompt: str, gen_config: dict) -> list[str]:
    """
    Generate proofs using litellm.

    Args:
        prompts: List of prompts to generate proofs for.
        gen_config: Generation parameters passed to litellm.

    Returns:
        List of lists of generated proofs, one list per prompt.
    """
    n_candidates = gen_config['n_candidates']
    batch_size = gen_config.get('batch_size', 3)
  
    candidates = []
    durations = []
    prompt_tokens = []
    completion_tokens = []
    total_tokens = []
        
    for i in range(0, n_candidates, batch_size):
        batch_candidates = []
        batch_durations = []
        batch_prompt_tokens = []
        batch_completion_tokens = []
        batch_total_tokens = []
        current_batch_size = min(batch_size, n_candidates - i)
        try:
            tasks = []
            for _ in range(current_batch_size):
                task = timed_completion(system_prompt, prompt, gen_config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Error in generation: {result}")
                    batch_candidates.append("")
                    batch_durations.append(0)
                    batch_prompt_tokens.append(0)
                    batch_completion_tokens.append(0)
                    batch_total_tokens.append(0)
                elif not result['success'] or isinstance(result['response'], Exception):
                    logger.warning(f"Error in generation: {result['response']}")
                    batch_candidates.append("")
                    batch_durations.append(result['duration'])
                    batch_prompt_tokens.append(0)
                    batch_completion_tokens.append(0)
                    batch_total_tokens.append(0)
                elif result['response'].choices[0].message.content is None:
                    logger.warning("Received None response, appending empty proof")
                    batch_candidates.append("")
                    batch_durations.append(result['duration'])
                    batch_prompt_tokens.append(result['response'].usage.prompt_tokens if result['response'].usage else 0)
                    batch_completion_tokens.append(result['response'].usage.completion_tokens if result['response'].usage else 0)
                    batch_total_tokens.append(result['response'].usage.total_tokens if result['response'].usage else 0)
                else:
                    proof = extract_proof_from_response(result['response'].choices[0].message.content)
                    batch_candidates.append(proof)
                    batch_durations.append(result['duration'])
                    batch_prompt_tokens.append(result['response'].usage.prompt_tokens)
                    batch_completion_tokens.append(result['response'].usage.completion_tokens)
                    batch_total_tokens.append(result['response'].usage.total_tokens)
            
            candidates.extend(batch_candidates)
            durations.extend(batch_durations)
            prompt_tokens.extend(batch_prompt_tokens)
            completion_tokens.extend(batch_completion_tokens)
            total_tokens.extend(batch_total_tokens)
                
        except Exception as e:
            logger.error(f"Batch generation error: {e}")
            candidates.extend([""] * current_batch_size)
            durations.extend([0] * current_batch_size)
            prompt_tokens.extend([0] * current_batch_size)
            completion_tokens.extend([0] * current_batch_size)
            total_tokens.extend([0] * current_batch_size)
        
        if i + batch_size < n_candidates:
            await asyncio.sleep(3)
        
    logger.info(f"Generated {len(candidates)} candidates")
    
    return candidates, durations, prompt_tokens, completion_tokens, total_tokens


def generate_hint_for_false_attempts(statement_data: Dict, max_attempts: int = 3, seed: int = None) -> str:
    statement_idx = statement_data["statement_idx"]
    false_attempts = statement_data["false_attempts"]
    
    if seed is not None:
        random.seed(seed + statement_idx)
    
    num_attempts = min(len(false_attempts), max_attempts)
    selected_attempts = random.sample(false_attempts, num_attempts)
    
    prompt_parts = []
    for i, attempt in enumerate(selected_attempts, 1):
        proof = attempt["proof"]
        error_message = attempt["error_message"]
        if error_message is None:
            error_message = "No error message available"
        
        prompt_parts.append(f"False Attempt {i}:")
        prompt_parts.append(proof)
        prompt_parts.append(f"Error Message: {error_message}")
        prompt_parts.append("")
    
    if prompt_parts and prompt_parts[-1] == "":
        prompt_parts.pop()
    
    return "\n".join(prompt_parts) 


if __name__ == "__main__":
    allowed_hints = ["proof_idea", "goal_state", "false_attempts", "useful_theorems", "None"]
    
    used_hints = "None"
    used_context = "False"
    # model_name = "gemini-2.5-flash-preview-05-20"
    # model_name = "claude-sonnet-4-20250514"
    # model_name="o4-mini"
    # model_name = "deepseek-chat"
    # model_name = "deepseek-reasoner"
    model_name = "gpt-4o"
    
    if model_name.startswith("claude"):
        provider = "anthropic"
        model = provider + "/" + model_name
    elif model_name.startswith("gemini"):
        provider = "gemini"
        model = provider + "/" + model_name
    elif model_name.startswith("deepseek"):
        provider = "deepseek"
        model = provider + "/" + model_name   
    else:
        model = model_name
    
    gen_config = {
        'model': model,
        'temperature': 0.6,
        'max_tokens': 2048,
        'n_candidates': 6,
        'timeout': 60,
        'batch_size': 6,
        'reasoning_effort': "None"
    }
    
    print(f"Using model: {model}")
    print(f"OpenAI API key: {os.environ.get('OPENAI_API_KEY', 'Not set')}")
    print(f"Anthropic API key: {os.environ.get('ANTHROPIC_API_KEY', 'Not set')}")
    print(f"DeepSeek API key: {os.environ.get('DEEPSEEK_API_KEY', 'Not set')}")
    print(f"Gemini API key: {os.environ.get('GEMINI_API_KEY', 'Not set')}")
    print(f"Generation config: {gen_config}")
    print(f"Used hints: {used_hints}")
    
    allowed_reasoning_efforts = ["None", "low", "medium", "high", "disable"]
    if gen_config['reasoning_effort'] not in allowed_reasoning_efforts:
        raise ValueError(f"Reasoning effort must be one of {allowed_reasoning_efforts}, but got {gen_config['reasoning_effort']}")
    if gen_config['reasoning_effort'] != "None" and not litellm.supports_reasoning(model=model):
        raise ValueError(f"Model {model} does not support reasoning effort, but got {gen_config['reasoning_effort']}")
    
    tasks = load_dataset("/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f.jsonl")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    w_or_wo = "wo" if used_context == "False" else "w"
    output_filename = f"experiment_results_{model_name}_{w_or_wo}_{timestamp}_generation.jsonl"
    
    results = []
    
    if used_context == "True":
        system_prompt_template = system_prompt_w_context_template
        whole_proof_prompt_template = whole_proof_prompt_w_context_template
    else:
        system_prompt_template = system_prompt_wo_context_template
        whole_proof_prompt_template = whole_proof_prompt_wo_context_template
    
    if used_hints not in allowed_hints:
        raise ValueError(f"Used hints must be one of {allowed_hints}, but got {used_hints}")
    
    if used_hints == "proof_idea":
        raw_hints = load_dataset("/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f_proof_ideas.jsonl")
        hints = [r['proof_idea'] for r in raw_hints]
        additional_guidelines = "- Follow the provided proof idea as a guideline for generating the formal proof"
        hints_section_template = "### Proof Idea:\n{hint}\n"
    elif used_hints == "goal_state":
        raw_hints = load_dataset("/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f_goal_states.jsonl")
        hints = [r['goal_state'] for r in raw_hints]
        additional_guidelines = "- Generate a complete proof based on the current goal state"
        hints_section_template = "### Initial Goal State:\n{hint}\n"
    elif used_hints == "false_attempts":
        # raw_hints = load_dataset(f"/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f_{model_name}_false_attempts.jsonl")
        raw_hints = load_dataset(f"/Users/siyuange/Documents/lean_llm_test/data/minif2f/minif2f_{model_name}-disable_false_attempts.jsonl")
        hints = [generate_hint_for_false_attempts(r, max_attempts=3) for r in raw_hints]
        additional_guidelines = "- Previous **false** attempts are provided\n- **Avoid** the error made in the false attempts"
        hints_section_template = "### Previous False Attempts:\n{hint}\n"
    else:
        hints = None
        additional_guidelines = ""
        hints_section_template = None
    
    for idx, task in tqdm(enumerate(tasks)):
        context = task['srcContext']
        theorem = task['theoremStatement']
        
        system_prompt = system_prompt_template.format(
            additional_guidelines=additional_guidelines
        )
            
        if hints_section_template is None or hints is None or hints[idx] is None:
            hints_section = ""
        else:
            hints_section = hints_section_template.format(hint=hints[idx])
        
        prompt = whole_proof_prompt_template.format(
            src_context=context,
            theorem_statement=theorem + ":= ",
            hints_section=hints_section
        )
        
        candidates, durations, prompt_tokens, completion_tokens, total_tokens = asyncio.run(generate(system_prompt, prompt, gen_config))
        
        result = {
            'statement_idx': idx,
            'candidates': candidates,
            'durations': durations,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
        }
        
        results.append(result)
    
    setting = {
        'model': model_name,
        'n_candidates': gen_config['n_candidates'],
        'temperature': gen_config['temperature'],
        'max_tokens': gen_config['max_tokens'],
        'timeout': gen_config['timeout'],
        'reasoning_effort': gen_config['reasoning_effort'],
        "generation": "whole_proof",
        "used_context": used_context,
        'used_hints': used_hints,
        'dataset': "minif2f.jsonl",
        'total_tasks': len(tasks),
        'timestamp': timestamp,
    }  
    
    with open(output_filename, "w") as f:
        f.write(json.dumps({"experiment_setting": setting}) + '\n')
        f.write(json.dumps({"generation_results": results}) + '\n')
        
    print(f"Results saved to {output_filename}")
    
    
    
    
    
    
    