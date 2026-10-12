from __future__ import annotations

"""Phase A: RAGAS Production Evaluation — 50q, 3 distributions, cluster analysis."""

import json
import os
import re
import sys
from dataclasses import asdict, dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, ANSWERS_PATH, ARTIFACTS_DIR
from src.experiment_support import write_json

Distribution = str  # "factual" | "multi_hop" | "adversarial"

DIAGNOSTIC_TREE = {
    "faithfulness":      ("LLM hallucinating", "Tighten system prompt, lower temperature"),
    "context_recall":    ("Missing relevant chunks", "Improve chunking or add BM25"),
    "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
    "answer_relevancy":  ("Answer doesn't match question", "Improve prompt template"),
}


@dataclass
class RagasResult:
    question_id: int
    distribution: Distribution
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    @property
    def avg_score(self) -> float:
        return (self.faithfulness + self.answer_relevancy +
                self.context_precision + self.context_recall) / 4

    @property
    def worst_metric(self) -> str:
        scores = {
            "faithfulness":      self.faithfulness,
            "answer_relevancy":  self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall":    self.context_recall,
        }
        return min(scores, key=scores.get)


# ─── Đã implement sẵn ────────────────────────────────────────────────────────

@dataclass
class RagasEvaluation:
    """Task 2 output: measured rows plus model identifiers reported by m4."""
    results: list[RagasResult]
    evaluator_models: list[str]

def load_test_set_50q(path: str = TEST_SET_PATH) -> list[dict]:
    """Load 50q test set với 3 distributions."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_answers(path: str = ANSWERS_PATH) -> list[dict]:
    """Load pre-generated answers từ setup_answers.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"answers_50q.json không tìm thấy tại {path}\n"
            "→ Chạy trước: python scripts/setup_answers.py --live"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict]) -> dict:
    """Provided exporter: preserve the student-produced Task 3 rows verbatim."""
    per_dist: dict[str, dict] = {}
    for dist in ["factual", "multi_hop", "adversarial"]:
        subset = [r for r in results if r.distribution == dist]
        if subset:
            per_dist[dist] = {
                "count": len(subset),
                "faithfulness":      sum(r.faithfulness for r in subset) / len(subset),
                "answer_relevancy":  sum(r.answer_relevancy for r in subset) / len(subset),
                "context_precision": sum(r.context_precision for r in subset) / len(subset),
                "context_recall":    sum(r.context_recall for r in subset) / len(subset),
                "avg_score":         sum(r.avg_score for r in subset) / len(subset),
            }

    report = {
        "total_questions": len(results),
        "per_question": [asdict(r) for r in results],
        "per_distribution": per_dist,
        "failure_clusters": clusters,
        "bottom_10": bottom,
    }
    return report


def save_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict],
                        path: str = os.path.join(ARTIFACTS_DIR, "ragas_50q.json")) -> None:
    write_json(path, build_phase_a_report(results, clusters, bottom))



# ─── Tasks 1-4: Sinh viên implement ──────────────────────────────────────────

METRIC_NAMES = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
DISTRIBUTIONS = ("factual", "multi_hop", "adversarial")
_REFUSAL_MARKERS = ("không tìm thấy", "không có thông tin", "không đề cập", "không được nêu", "không rõ")


def group_by_distribution(test_set: list[dict]) -> dict[str, list[dict]]:
    """Task 1: Nhóm 50 câu hỏi theo 3 distributions (giữ nguyên thứ tự và nội dung từng câu).

    Returns:
        {"factual": [...], "multi_hop": [...], "adversarial": [...]}
    """
    groups: dict[str, list[dict]] = {d: [] for d in DISTRIBUTIONS}
    for item in test_set:
        distribution = item.get("distribution")
        if distribution not in groups:
            raise ValueError(f"id={item.get('id')}: unknown distribution {distribution!r}")
        groups[distribution].append(item)
    return groups


def _metric_value(record, name: str) -> float:
    """One metric of an m4 row (object or mapping) as a finite float in [0, 1]; NaN is never replaced by a fake score."""
    value = record.get(name) if isinstance(record, dict) else getattr(record, name, None)
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"m4 returned a non-numeric {name}: {value!r}") from None
    if value != value or not 0.0 <= value <= 1.0:
        raise ValueError(f"m4 returned an invalid {name}: {value!r}")
    return value


def run_ragas_50q(answers: list[dict]) -> RagasEvaluation:
    """Task 2: Chạy RAGAS 4 metrics (src.m4_eval.evaluate_ragas) trên toàn bộ answers, giữ đúng thứ tự.

    Returns RagasEvaluation(results, evaluator_models) — model lấy từ metadata m4 trả về, không đoán JUDGE_MODEL.
    """
    try:
        from src.m4_eval import evaluate_ragas
    except ImportError as exc:
        raise ValueError("Missing src/m4_eval.py; cannot declare its actual evaluator models") from exc

    questions = [a["question"] for a in answers]
    ans_texts = [a["answer"] for a in answers]
    contexts = [list(a["contexts"]) for a in answers]
    ground_truths = [a["ground_truth"] for a in answers]

    raw = evaluate_ragas(questions, ans_texts, contexts, ground_truths)
    per_question = list(raw.get("per_question") or [])
    if len(per_question) != len(answers):
        raise ValueError(f"m4 returned {len(per_question)} rows for {len(answers)} answers")
    evaluator_models = list((raw.get("metadata") or {}).get("evaluator_models") or [])
    if not evaluator_models:
        raise ValueError("m4 metadata.evaluator_models is missing")

    results = [
        RagasResult(
            question_id=a["id"], distribution=a["distribution"],
            question=a["question"], answer=a["answer"],
            contexts=list(a["contexts"]), ground_truth=a["ground_truth"],
            **{name: _metric_value(row, name) for name in METRIC_NAMES},
        )
        for a, row in zip(answers, per_question)
    ]
    return RagasEvaluation(results, evaluator_models)


_NUMBER = re.compile(r"(\d+(?:[.,]\d+)*)(\s*triệu)?", re.IGNORECASE)
_PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")


def _values(text: str) -> dict[float, str]:
    """Numeric values in the text -> their spelling. "1.200.000" = 1200000, "5 triệu" = 5000000."""
    found: dict[float, str] = {}
    for digits, million in _NUMBER.findall(text or ""):
        digits = digits.rstrip(".,")
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", digits):
            value = float(digits.replace(".", ""))
        else:
            try:
                value = float(digits.replace(",", "."))
            except ValueError:
                continue
        if million:
            value, digits = value * 1_000_000, digits + " triệu"
        found.setdefault(value, digits)
    return found


def _present(value: float, values) -> bool:
    """A small value also counts as present in millions: the "5" of "5-50 triệu" matches "5.000.000"."""
    return value in values or (value < 1000 and value * 1_000_000 in values)


_DERIVED = re.compile(r"(?:=|≈|→|tổng[^\d=]{0,15}|còn lại[^\d]{0,5})\s*(\d+(?:[.,]\d+)*)", re.IGNORECASE)
_SUPERSEDED = ("đã thay thế", "phiên bản cũ", "hết hiệu lực", "thay thế hoàn toàn phiên bản")


def _derived_values(r: RagasResult, operands: set[float], percents: set[float]) -> set[float]:
    """Reference values that are inputs from the question or one arithmetic step away from question/context values
    (sum, difference, count x amount, explicit percentage), so not facts the retriever should have found."""
    derived = set(_values(r.question)) | set(_values(" ".join(_DERIVED.findall(r.ground_truth))))
    pool = sorted(operands)
    for i, x in enumerate(pool):
        for y in pool[i + 1:]:
            derived |= {x + y, y - x}
            if x <= 100 < y:                       # count x amount, e.g. 2 nights x 1.200.000
                derived.add(x * y)
            if x in percents:                      # 85% x 12.000.000
                derived.add(x * y / 100)
    return derived


_VERSION = re.compile(r"(?:\bv|phiên bản\s+)(\d+(?:\.\d+)*)", re.IGNORECASE)
_OLD_MARKERS = ("đã thay thế", "bị thay thế", "hết hiệu lực", " cũ")


_INFERENCE_MARKERS = ("suy ra", "khoảng", "tương đương", "ước tính", "giả sử", "có thể hiểu")


def _context_overlap(answer: str, contexts: list[str]) -> float:
    """Share of the answer's words that also appear in the contexts (1.0 = restated word for word)."""
    words = re.findall(r"\w+", (answer or "").lower())
    context_words = set(re.findall(r"\w+", " ".join(contexts).lower()))
    return sum(w in context_words for w in words) / len(words) if words else 0.0


def _diagnose(r: RagasResult) -> tuple[str, str]:
    """Diagnosis from the row's own evidence: reference facts found (or not) in contexts and answer, values of a
    superseded policy repeated in the answer, abstention, and the metric profile.

    Reference numbers that are inputs from the question, results of arithmetic ("= 17", "Tổng: ...") or policy
    version labels ("v2.0") are not counted as facts the retriever or the generator should have reproduced.
    """
    answer_lower = (r.answer or "").lower()
    context_values = _values(" ".join(r.contexts))
    answer_values = _values(r.answer)
    question_values = set(_values(r.question))
    version_labels = {float(v) for v in _VERSION.findall(r.ground_truth) if v.replace(".", "").isdigit()}
    reference = {v: s for v, s in _values(r.ground_truth).items() if v not in version_labels}
    percents = {float(p.replace(",", ".")) for p in _PERCENT.findall(" ".join([r.question, *r.contexts]))}
    derived = _derived_values(r, question_values | set(context_values), percents)
    facts = [v for v in sorted(reference) if not _present(v, derived)]
    facts_not_retrieved = [reference[v] for v in facts if not _present(v, context_values)]
    facts_not_answered = [reference[v] for v in facts if not _present(v, answer_values)]
    derived_not_answered = [reference[v] for v in sorted(reference) if _present(v, derived)
                            and not _present(v, question_values) and not _present(v, answer_values)]
    abstained = any(marker in answer_lower for marker in _REFUSAL_MARKERS)

    sentences = re.split(r"(?<=[.!?])\s+", r.ground_truth)
    old_text = " ".join(s for s in sentences if any(m in s.lower() for m in _OLD_MARKERS))
    current_text = " ".join(s for s in sentences if not any(m in s.lower() for m in _OLD_MARKERS))
    old_values = set(_values(old_text)) - set(_values(current_text)) - version_labels
    asks_old = bool(_VERSION.search(r.question)) or " cũ" in r.question.lower()
    repeated_old = sorted(v for v in old_values if v in answer_values) if not asks_old else []
    labels_unnamed = (sorted({f"v{v}" for v in _VERSION.findall(r.ground_truth)})
                      if version_labels and not _VERSION.search(r.answer or "") else [])

    scores = (f"F={r.faithfulness:.2f} AR={r.answer_relevancy:.2f} "
              f"CP={r.context_precision:.2f} CR={r.context_recall:.2f}")

    if abstained and facts_not_retrieved:
        return (f"Retrieval miss: part of the answer abstains ('không tìm thấy/không có thông tin') and reference "
                f"facts {facts_not_retrieved[:5]} are not in the top-{len(r.contexts)} contexts ({scores}).",
                "Retrieval: decompose the question into one sub-query per asked item and merge the contexts "
                "(or raise rerank top_k), so the chunk holding these facts is retrieved.")
    if abstained:
        return (f"Generation abstains on part of the question although the reference facts are in the contexts "
                f"({scores}).",
                "Generation: answer each asked item the context states; reserve 'Không tìm thấy' for items it lacks.")
    if repeated_old:
        return (f"Version conflict: the answer repeats the superseded rule (value(s) {[_fmt(v) for v in repeated_old]}) "
                f"next to or instead of the current one; both versions are in the retrieved contexts ({scores}).",
                "Index effective date/status metadata, filter or down-rank superseded versions, and instruct the "
                "generator to apply the current version and name it when versions disagree.")
    if r.distribution == "multi_hop" and facts_not_retrieved:
        return (f"Multi-hop gap: the contexts cover only part of the reasoning chain; reference facts "
                f"{facts_not_retrieved[:5]} were not retrieved ({scores}).",
                "Retrieval: one sub-query per hop and merge the contexts, or return parent chunks instead of "
                "256-character children.")
    overlap = _context_overlap(r.answer, r.contexts)
    inferred = any(marker in answer_lower for marker in _INFERENCE_MARKERS)
    if (not facts_not_answered and not derived_not_answered and not inferred and overlap >= 0.9
            and (r.faithfulness < 0.7 or r.context_recall < 0.5)):
        return (f"No factual error found: the answer restates the retrieved context almost word for word "
                f"({overlap:.0%} of its words are in the contexts) and has every reference value, yet the evaluator "
                f"scored it low ({scores}); treat as evaluator inconsistency, scores of this row varied across runs.",
                "Evaluation: re-score with several RAGAS runs (or a second evaluator) and alert only on rows that "
                "stay low; keep the answer and pipeline unchanged for this row.")
    if not facts_not_answered and not derived_not_answered and r.faithfulness < 0.7 and r.context_recall >= 0.75:
        return (f"No factual error found: the answer reaches every reference value from inputs present in the "
                f"contexts; RAGAS faithfulness marks the computed statements (totals, percentages) as unsupported "
                f"because the results are not written in the contexts ({scores}).",
                "Evaluation: add an arithmetic check (recompute from context values) or a custom metric for derived "
                "values; generation: show the formula with the cited context values so each step is attributable.")
    if not facts_not_answered and not derived_not_answered and r.faithfulness < 0.7:
        return (f"Answer reaches the reference values, but the rule it uses is not stated in the contexts: the "
                f"model inferred it from an example instead of a retrieved rule ({scores}).",
                "Retrieval: retrieve the chunk that states the rule (parent chunk / neighbouring child); "
                "generation: forbid extrapolating rules from examples.")
    if facts_not_answered or derived_not_answered:
        return (f"Answer omits or miscomputes reference values {(facts_not_answered + derived_not_answered)[:5]} "
                f"although the needed inputs are retrieved ({scores}).",
                "Generation: list every asked item and compute step by step from the context values; "
                "check the answer covers each part of the question.")
    if r.context_precision < 0.5:
        return (f"Correct answer, but the supporting chunk is ranked below unrelated chunks ({scores}).",
                "Rerank: keep only chunks above a score threshold and filter by document/topic metadata.")
    if labels_unnamed and r.answer_relevancy < 0.8:
        return (f"No factual error found: the answer states the current rule but not the policy version "
                f"{labels_unnamed} the reference anchors on; only answer_relevancy is low ({scores}).",
                "Prompt: name the applicable policy version when a topic has several versions; re-run RAGAS to "
                "separate a real relevancy gap from metric noise on short Vietnamese answers.")
    if r.answer_relevancy < 0.6:
        return (f"No factual error found; only answer_relevancy is low: the answer restates context or adds side "
                f"details beyond the asked item ({scores}).",
                "Prompt: answer the asked item in the first sentence, then give only the needed details.")
    diagnosis, fix = DIAGNOSTIC_TREE[r.worst_metric]
    return f"{diagnosis} (weakest metric {r.worst_metric}; {scores}).", fix


def _fmt(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") if value == int(value) else f"{value:g}"


def bottom_10(results: list[RagasResult]) -> list[dict]:
    """Task 3: 10 câu có avg_score thấp nhất (tăng dần), chẩn đoán theo nội dung từng câu.

    Returns:
        [{"rank": 1, "question_id": ..., "distribution": ...,
          "question": ..., "avg_score": ..., "worst_metric": ...,
          "diagnosis": ..., "suggested_fix": ...}, ...]
    """
    rows = []
    for rank, r in enumerate(sorted(results, key=lambda r: r.avg_score)[:10], start=1):
        diagnosis, fix = _diagnose(r)
        rows.append({
            "rank": rank,
            "question_id": r.question_id,
            "distribution": r.distribution,
            "question": r.question,
            "avg_score": round(r.avg_score, 4),
            "worst_metric": r.worst_metric,
            "diagnosis": diagnosis,
            "suggested_fix": fix,
        })
    return rows


def cluster_analysis(results: list[RagasResult]) -> dict:
    """Task 4: Matrix worst_metric × distribution (đếm mọi câu); nhóm yếu nhất = avg_score trung bình thấp nhất.

    Tổng matrix theo cột chỉ là kích thước nhóm 20/20/10, không đo chất lượng; nhóm rỗng bị bỏ qua.
    """
    matrix = {metric: {d: 0 for d in DISTRIBUTIONS} for metric in DIAGNOSTIC_TREE}
    for r in results:
        matrix[r.worst_metric][r.distribution] += 1

    means = {}
    for d in DISTRIBUTIONS:
        subset = [r.avg_score for r in results if r.distribution == d]
        if subset:
            means[d] = sum(subset) / len(subset)
    if not means:
        return {"matrix": matrix, "distribution_avg_scores": {}, "dominant_failure_distribution": None,
                "dominant_failure_metric": None, "insight": "No measured rows to analyse."}

    weakest = min(means, key=means.get)
    dominant_metric = max(matrix, key=lambda m: sum(matrix[m].values()))
    metric_means = {m: sum(getattr(r, m) for r in results) / len(results) for m in METRIC_NAMES}
    lowest_metrics = sorted(metric_means.items(), key=lambda kv: kv[1])[:2]
    insight = (f"Weakest distribution by mean avg_score is '{weakest}' ("
               + ", ".join(f"{d}={means[d]:.3f}" for d in sorted(means, key=means.get))
               + f"). '{dominant_metric}' is the most frequent worst metric "
               f"({sum(matrix[dominant_metric].values())}/{len(results)} questions); lowest metric means: "
               + ", ".join(f"{m}={v:.3f}" for m, v in lowest_metrics)
               + f". First lever: {DIAGNOSTIC_TREE[dominant_metric][1]}.")
    return {"matrix": matrix, "distribution_avg_scores": {d: round(v, 4) for d, v in means.items()},
            "dominant_failure_distribution": weakest, "dominant_failure_metric": dominant_metric,
            "insight": insight}


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "a", *sys.argv[1:]]))
