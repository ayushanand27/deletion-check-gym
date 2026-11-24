### Real LLMs (single-step, 40 public cases, temperature 0)
| Agent | Mean reward (95% CI) | Accuracy | False 'complete' | Perfect |
| --- | --- | --- | --- | --- |
| openai/gpt-oss-120b | 1.00 (1.00 to 1.00) | 100% | 0/40 | 40/40 |
| openai/gpt-oss-20b | 0.89 (0.69 to 1.00) | 98% | 1/40 | 38/40 |
| qwen/qwen3.8-27b | 0.54 (0.20 to 0.84) | 82% | 2/40 | 32/40 |

### By category
| Category | openai/gpt-oss-120b | openai/gpt-oss-20b | qwen/qwen3.8-27b |
| --- | --- | --- | --- |
| all_clear | 1.00 | 1.00 | 1.00 |
| audit_deleted | 1.00 | 1.00 | 1.00 |
| ingestion_failed | 1.00 | 1.00 | 1.00 |
| missing_record | 1.00 | 0.00 | -1.07 |
| mixed_violation_and_unknown | 1.00 | 0.96 | -0.67 |
| still_present | 1.00 | 1.00 | 1.00 |
| unknown_evidence | 1.00 | 1.00 | 1.00 |
