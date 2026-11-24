### Real LLMs (single-step, 30 hard cases, temperature 0)
| Agent | Mean reward (95% CI) | Accuracy | False 'complete' | Perfect |
| --- | --- | --- | --- | --- |
| openai/gpt-oss-120b | 1.00 (1.00 to 1.00) | 100% | 0/30 | 30/30 |
| openai/gpt-oss-20b | 1.00 (1.00 to 1.00) | 100% | 0/30 | 30/30 |
| qwen/qwen3.8-27b | 0.73 (0.33 to 1.00) | 93% | 2/30 | 28/30 |

### By category
| Category | openai/gpt-oss-120b | openai/gpt-oss-20b | qwen/qwen3.8-27b |
| --- | --- | --- | --- |
| buried_audit_deleted | 1.00 | 1.00 | 1.00 |
| injected_note | 1.00 | 1.00 | 1.00 |
| injected_note_unresolved | 1.00 | 1.00 | -1.00 |
| stale_clean_fresh_present | 1.00 | 1.00 | 1.00 |
| stale_present_fresh_clean | 1.00 | 1.00 | 1.00 |
| stale_unknown_fresh_clean | 1.00 | 1.00 | 1.00 |
