from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json, math
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH

METRICS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


NAN_RETRY_ROUNDS = 3


def _finite_or_none(value):
    """A metric value as a finite float in [0, 1], or None when RAGAS could not compute it (NaN/missing)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return min(1.0, max(0.0, value))


def _build_evaluators():
    """The evaluator LLM and embeddings, explicit so the report can name the models actually called."""
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from config import EVALUATOR_MODEL, EVALUATOR_EMBEDDING_MODEL
    llm = ChatOpenAI(model=EVALUATOR_MODEL, temperature=0, timeout=120, max_retries=5)
    embeddings = OpenAIEmbeddings(model=EVALUATOR_EMBEDDING_MODEL, check_embedding_ctx_length=False)
    return llm, embeddings, [llm.model_name, embeddings.model]


def _evaluator_answer(answer: str) -> str:
    """Punctuation-only normalisation of the answer sent to RAGAS.

    ragas 0.1.22 faithfulness keeps only segments that end with "." before extracting statements, so bullet
    lines without a final period are silently dropped (an all-bullet answer gives 0 statements -> NaN).
    Ending every non-empty line with "." makes the metric see the whole answer; words are unchanged.
    """
    lines = []
    for line in str(answer).splitlines():
        line = line.rstrip()
        lines.append(line if not line.strip() or line.endswith(".") else line + ".")
    return "\n".join(lines)


def _run_ragas(rows: list[int], questions, answers, contexts, ground_truths, llm, embeddings) -> list[dict]:
    """One RAGAS pass over the given row indices; returns one {metric: float|None} dict per row, in order."""
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from ragas.run_config import RunConfig
    from datasets import Dataset

    dataset = Dataset.from_dict({
        "question": [questions[i] for i in rows], "answer": [_evaluator_answer(answers[i]) for i in rows],
        "contexts": [list(contexts[i]) for i in rows], "ground_truth": [ground_truths[i] for i in rows],
    })
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                      llm=llm, embeddings=embeddings, raise_exceptions=False,
                      run_config=RunConfig(timeout=180, max_retries=5, max_wait=30, max_workers=8))
    df = result.to_pandas()
    if len(df) != len(rows):
        raise ValueError(f"RAGAS returned {len(df)} rows for {len(rows)} inputs")
    return [{m: _finite_or_none(row.get(m)) for m in METRICS} for _, row in df.iterrows()]


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS (4 metrics) with an explicit evaluator LLM + embedding model.

    Returns {"per_question": [EvalResult, ...] (same order and length as the inputs), <metric means>,
             "metadata": {"evaluator_models": [llm_model, embedding_model], "nan_retry_rounds": int}}.
    RAGAS returns NaN when a judge call fails or its output cannot be parsed. Those rows are re-evaluated
    (up to NAN_RETRY_ROUNDS times); a metric still NaN afterwards raises ValueError — no fake score.
    """
    n = len(questions)
    if not (len(answers) == len(contexts) == len(ground_truths) == n) or n == 0:
        raise ValueError("questions, answers, contexts and ground_truths must be non-empty and the same length")

    llm, embeddings, evaluator_models = _build_evaluators()
    scores = _run_ragas(list(range(n)), questions, answers, contexts, ground_truths, llm, embeddings)
    rounds = 0
    while rounds < NAN_RETRY_ROUNDS:
        missing = [i for i, row in enumerate(scores) if any(v is None for v in row.values())]
        if not missing:
            break
        rounds += 1
        print(f"  RAGAS: {len(missing)} row(s) with NaN metrics, re-evaluating (round {rounds})")
        retried = _run_ragas(missing, questions, answers, contexts, ground_truths, llm, embeddings)
        for i, row in zip(missing, retried):
            scores[i] = {m: scores[i][m] if scores[i][m] is not None else row[m] for m in METRICS}

    unresolved = {i: [m for m, v in row.items() if v is None] for i, row in enumerate(scores)
                  if any(v is None for v in row.values())}
    if unresolved:
        raise ValueError(f"RAGAS could not score rows {unresolved} after {rounds} retry round(s)")

    per_question = [
        EvalResult(question=questions[i], answer=answers[i], contexts=list(contexts[i]),
                   ground_truth=ground_truths[i], **scores[i])
        for i in range(n)
    ]
    aggregate = {m: sum(row[m] for row in scores) / n for m in METRICS}
    return {**aggregate, "per_question": per_question,
            "metadata": {"evaluator_models": evaluator_models, "nan_retry_rounds": rounds,
                         "answer_normalisation": "line-final period added for RAGAS segmentation"}}


_DIAGNOSTIC_TREE = {
    "faithfulness": ("LLM hallucinating", "Tighten prompt, lower temperature"),
    "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25"),
    "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
    "answer_relevancy": ("Answer doesn't match question", "Improve prompt template"),
}


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    scored = []
    for r in eval_results:
        values = {m: getattr(r, m) for m in METRICS}
        worst_metric = min(values, key=values.get)  # chỉ số thấp nhất của câu hỏi này
        scored.append((sum(values.values()) / len(values), worst_metric, values[worst_metric], r))

    scored.sort(key=lambda item: item[0])  # trung bình tăng dần: tệ nhất trước
    failures = []
    for avg, worst_metric, worst_score, r in scored[:bottom_n]:
        diagnosis, fix = _DIAGNOSTIC_TREE[worst_metric]
        failures.append({
            "question": r.question,
            "answer": r.answer,
            "ground_truth": r.ground_truth,
            "avg_score": round(avg, 4),
            "worst_metric": worst_metric,
            "score": round(worst_score, 4),
            "diagnosis": diagnosis,
            "suggested_fix": fix,
        })
    return failures


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
