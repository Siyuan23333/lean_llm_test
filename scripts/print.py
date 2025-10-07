dict = {
    "rank": 1,
    "theorem_name": "mathd_algebra_459",
    "theorem_statement": "theorem mathd_algebra_459 (a b c d : \u211a) (h\u2080 : 3 * a = b + c + d) (h\u2081 : 4 * b = a + c + d) (h\u2082 : 2 * c = a + b + d) (h\u2083 : 8 * a + 10 * b + 6 * c = 24) : \u2191d.den + d.num = 28",
    "proof": "by\n  -- Define S = a + b + c + d\n  let S := a + b + c + d\n  -- From the equations, we can derive:\n  -- 3a = b + c + d, so 4a = S, hence a = S/4\n  -- 4b = a + c + d, so 5b = S, hence b = S/5  \n  -- 2c = a + b + d, so 3c = S, hence c = S/3\n  have ha : a = S / 4 := by\n    have : 4 * a = S := by\n      calc 4 * a = a + 3 * a := by ring\n      _ = a + (b + c + d) := by rw [h\u2080]\n      _ = S := by ring\n    linarith\n  have hb : b = S / 5 := by\n    have : 5 * b = S := by\n      calc 5 * b = b + 4 * b := by ring\n      _ = b + (a + c + d) := by rw [h\u2081]\n      _ = S := by ring\n    linarith\n  have hc : c = S / 3 := by\n    have : 3 * c = S := by\n      calc 3 * c = c + 2 * c := by ring\n      _ = c + (a + b + d) := by rw [h\u2082]\n      _ = S := by ring\n    linarith\n  -- Substitute into the fourth equation to find S\n  have hS : S = 4 := by\n    have : 8 * a + 10 * b + 6 * c = 6 * S := by\n      calc 8 * a + 10 * b + 6 * c = 8 * (S / 4) + 10 * (S / 5) + 6 * (S / 3) := by rw [ha, hb, hc]\n      _ = 2 * S + 2 * S + 2 * S := by ring\n      _ = 6 * S := by ring\n    have : 6 * S = 24 := by rw [\u2190 this, h\u2083]\n    linarith\n  -- Now we can find d\n  have hd : d = 13 / 15 := by\n    calc d = S - a - b - c := by ring\n    _ = 4 - 4/4 - 4/5 - 4/3 := by rw [hS, ha, hb, hc, hS]\n    _ = 4 - 1 - 4/5 - 4/3 := by norm_num\n    _ = 3 - 4/5 - 4/3 := by ring\n    _ = 45/15 - 12/15 - 20/15 := by norm_num\n    _ = 13/15 := by ring\n  -- Finally, show d.den + d.num = 28\n  rw [hd]\n  norm_num",
    "proof_length": 1451,
    "source_file": "experiment_results_claude-sonnet-4-20250514_wo_20250620_040102_results.jsonl",
    "experiment_setting": {
      "model": "claude-sonnet-4-20250514",
      "n_candidates": 6,
      "temperature": 1.0,
      "max_tokens": 2048,
      "timeout": 60,
      "reasoning_effort": "low",
      "generation": "whole_proof",
      "used_context": "False",
      "used_hints": "proof_idea",
      "dataset": "minif2f.jsonl",
      "total_tasks": 244,
      "timestamp": "20250620_040102"
    }
  }

print(dict["experiment_setting"])
print(dict["theorem_statement"])
print(dict["proof"])