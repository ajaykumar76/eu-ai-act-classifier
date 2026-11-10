# EU AI Act Risk-Tier Classifier (with Guardrails and Human Review)

A locally run research prototype that takes a plain-English description of an AI system and proposes an EU AI Act risk tier: **prohibited, high, limited, minimal or out of scope**. It retrieves potentially relevant provisions, asks a local LLM (Llama 3.2 through Ollama) to select a tier and cite provisions, then applies checks that route uncertain or high-consequence answers to human review.

> **Not legal advice and not an official EU AI Act compliance assessment.** The provision summaries in `data/provisions.json` are author-written paraphrases of Regulation (EU) 2024/1689, not the official legal text. Labels were written by the project author, not a lawyer. Verify the current legislation and authoritative guidance before relying on any classification.

The project evaluates the limits of an LLM-assisted GRC triage workflow. Its central question is not whether a small model can replace legal analysis, but whether explicit checks can identify some unsafe or unsupported answers and keep them out of automatic decisions.

## How it works

1. **Retrieve:** Use `all-MiniLM-L6-v2` embeddings and cosine similarity to retrieve the five most relevant provision summaries.
2. **Classify:** Ask a local `llama3.2` model via Ollama to propose a tier and cite only provisions from the retrieved candidate list.
3. **Validate:** Check that citations are from the candidate list, that at least one cited provision matches the proposed tier, and that the model has not selected a lower tier than the top retrieved provision suggests.
4. **Escalate:** Any failed check is flagged for human review. A proposed prohibited-practice classification is always sent for human sign-off.
5. **Evaluate:** Compare three approaches on labelled scenarios: retrieval-only, LLM-only, and LLM plus checks.

The classifier uses five project-defined output labels:
- `prohibited`
- `high`
- `limited`
- `minimal`
- `out_of_scope`

These labels simplify the prototype's triage task. They do not represent a complete legal analysis of every obligation or exception under the Act.

## Repository contents

```
data/
  provisions.json      Author-written paraphrases of selected EU AI Act provisions
  scenarios.json       41 author-written scenarios with gold labels and dev/test split
src/
  01_classify_eval.py  Retrieval, LLM classification, validation checks and evaluation
  inspect_cites.py     Citation inspection helper
reports/
  results_dev*.json    Development experiment outputs
  results_test_final.json
                       Final small test-set output
```

The scenario set contains 30 development examples used during prompt/check development and 11 test examples run once after the final version was selected.

## Setup

Requirements: Python 3.10+, NumPy, Sentence Transformers, and Ollama.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install numpy sentence-transformers ollama
ollama pull llama3.2
```

Run from the repository root:

```powershell
# Retrieval-only baseline; no LLM call
python src\01_classify_eval.py --split dev --no-llm

# Full LLM-assisted development evaluation
python src\01_classify_eval.py --split dev --tag v3

# Test set; the committed final test was run once
python src\01_classify_eval.py --split test --tag final
```

Results are written to `reports/results_<split>_<tag>.json`.

## Evaluation results

The development set was used for prompt and check development. The test set contains only 11 scenarios and was run once after the final version was fixed.

### Development set (n = 30)

| Measure | v1 | v2 | v3 (final) |
|---|---:|---:|---:|
| LLM-only accuracy | 22/30 (73%) | 14/30 (47%) | 20/30 (67%; 95% CI 49–81%) |
| Valid citations | 60% | 97% | 93% |
| Cites a gold provision | 40% | 37% | 57% |
| Automatically decided with checks | — | — | 14/30 (47%) |
| Accuracy on automatically decided cases | — | — | 79% |
| Under-classified among automatically decided cases | — | — | 0 |

### Test set (n = 11; final version)

| Measure | Result |
|---|---:|
| Retrieval-only accuracy | 8/11 (73%; 95% CI 43–90%) |
| LLM-only accuracy | 6/11 (55%; 95% CI 28–79%) |
| LLM outputs rated too low | 3 |
| Valid LLM citations | 11/11 |
| Automatically decided with checks | 5/11 (45%; 95% CI 21–72%) |
| Accuracy on automatically decided cases | 4/5 (80%; 95% CI 38–96%) |
| Under-classified among automatically decided cases | 0 |
| LLM errors caught by a check | 4/5 (80%; 95% CI 38–96%) |

### Interpretation

- On this small test set, retrieval-only accuracy (73%) was higher than LLM-only accuracy (55%). This experiment does not show that the LLM improves classification accuracy.
- The checks routed all three under-classified test answers to human review in this run. This is a result on 11 author-written scenarios, not proof that the guardrails prevent under-classification in real deployments.
- Only 5 of 11 test cases were automatically decided. The remaining cases required review, so this should be treated as a triage aid rather than an autonomous classifier.
- Development results changed substantially between prompt versions. The v2 prompt change reduced accuracy, which is retained in the results to make the iteration visible.

## Limitations

- The dataset is small and author-written: 30 development scenarios and 11 test scenarios.
- Gold labels were assigned by the project author, who is not a legal professional; borderline classifications are contestable.
- Provision summaries are paraphrases and may omit legal conditions or exceptions. Consult Regulation (EU) 2024/1689 and authoritative guidance.
- The test confidence intervals are wide; one case represents about nine percentage points.
- The checks are rule-based safeguards, not a legal validation engine. They can miss errors and can also send correct answers for review.
- The current checks focus particularly on under-classification. Over-classification can still occur.
- Results are specific to the selected model, embedding model, prompts and small dataset. They should not be generalised to production use.

## References

- [Regulation (EU) 2024/1689 — EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
- [European Commission — AI Act](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
- [Sentence Transformers](https://www.sbert.net/)
- [Ollama](https://ollama.com/)
