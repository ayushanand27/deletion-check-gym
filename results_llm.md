## Real LLMs (single-step, 40 public cases, temperature 0)
| Agent | Mean reward (95% CI) | Accuracy | False 'complete' | Perfect |
| --- | --- | --- | --- | --- |
| openai/gpt-oss-120b | 1.00 (1.00 to 1.00) | 100% | 0/40 | 40/40 |
| openai/gpt-oss-20b | 1.00 (1.00 to 1.00) | 100% | 0/40 | 40/40 |
| qwen/qwen3.8-27b | 0.60 (0.30 to 0.90) | 85% | 2/40 | 34/40 |

### By category
| Category | openai/gpt-oss-120b | openai/gpt-oss-20b | qwen/qwen3.8-27b |
| --- | --- | --- | --- |
| all_clear | 1.00 | 1.00 | 1.00 |
| audit_deleted | 1.00 | 1.00 | 1.00 |
| ingestion_failed | 1.00 | 1.00 | 1.00 |
| missing_record | 1.00 | 1.00 | -1.00 |
| mixed_violation_and_unknown | 1.00 | 1.00 | -0.33 |
| still_present | 1.00 | 1.00 | 1.00 |
| unknown_evidence | 1.00 | 1.00 | 1.00 |
