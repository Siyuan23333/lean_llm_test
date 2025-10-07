from litellm import cost_per_token

data = [
    (618.3238, 314.3757),
    (418.6598, 383.3866),
    (352.3361, 377.3805),
    (272.2746, 444.3675)
]



# model_name = "gemini-2.5-flash-preview-05-20"
# model_name = "anthropic/claude-sonnet-4-20250514"
# model_name="o4-mini"
# model_name = "deepseek/deepseek-chat"
# model_name = "deepseek-reasoner"
model_name = "gpt-4o"

for i in range(len(data)):

    prompt_tokens = round(data[i][0])
    completion_tokens = round(data[i][1])
    prompt_tokens_cost_usd_dollar, completion_tokens_cost_usd_dollar = cost_per_token(
      model=model_name,
      prompt_tokens=prompt_tokens,
      completion_tokens=completion_tokens
    )

    print(prompt_tokens_cost_usd_dollar + completion_tokens_cost_usd_dollar)