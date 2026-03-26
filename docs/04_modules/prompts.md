# Module: prompts

**Responsibility:** LLM System Prompts - Prompt templates for different agents

## Entry Points

- prompts/classify_prompt_example.txt → Intent classification
- prompts/default_prompt_example.txt → Default reply agent
- prompts/price_prompt_example.txt → Price negotiation agent
- prompts/tech_prompt_example.txt → Technical expert agent

## Key Files

- prompts/classify_prompt_example.txt → Intent classification prompt template
- prompts/default_prompt_example.txt → Default reply prompt template
- prompts/price_prompt_example.txt → Price negotiation prompt template
- prompts/tech_prompt_example.txt → Technical expert prompt template

## Constraints

- Templates are examples; actual prompts loaded from env/config
- Each agent type has specialized prompt
- Prompts guide LLM response style and constraints

## Scope Table

| Layer | Item | Description |
|-------|------|-------------|
| Implementation | prompts/*.txt | Prompt template files |
| Consumer | XianyuAgent.py | Loads and customizes prompts for LLM |
