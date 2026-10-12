from __future__ import annotations

"""Phase C: Production Guardrails — Presidio PII + NeMo Guardrails + P95 Latency."""

import asyncio
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ADVERSARIAL_SET_PATH, GUARDRAILS_CONFIG_DIR, LATENCY_BUDGET_P95_MS, PRESIDIO_LANGUAGE


# ─── Task 9a: Presidio PII Detection ─────────────────────────────────────────

def setup_presidio():
    """Khởi tạo Presidio engine với custom Vietnamese PII recognizers. (Đã implement sẵn)

    Custom recognizers thêm vào:
        VN_CCCD  — số CCCD 12 chữ số hoặc CMND 9 chữ số
        VN_PHONE — số điện thoại Việt Nam (0[3-9]xxxxxxxx)

    Các recognizers mặc định đã có sẵn: EMAIL, PHONE_NUMBER (international), ...
    """
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
    from presidio_anonymizer import AnonymizerEngine

    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[
            Pattern("CCCD 12 digits", r"\b\d{12}\b", 0.9),
            Pattern("CMND 9 digits",  r"\b\d{9}\b",  0.7),
        ],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern("VN mobile", r"\b0[3-9]\d{8}\b", 0.9)],
    )

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)

    analyzer  = AnalyzerEngine(registry=registry)
    anonymizer = AnonymizerEngine()
    return analyzer, anonymizer


# Identifier-type entities that block a request. spaCy's English NER entities (PERSON, LOCATION, NRP, DATE_TIME,
# ORGANIZATION) are left out on purpose: on Vietnamese policy questions they misfire ("v2024" as a date,
# "VPN"/"MFA" as names) and would block clean questions; personal-data requests without an identifier are
# the NeMo input rail's job.
PII_ENTITY_TYPES = {
    "VN_CCCD", "VN_PHONE", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IBAN_CODE",
    "US_SSN", "US_PASSPORT", "US_BANK_NUMBER", "US_DRIVER_LICENSE", "IP_ADDRESS", "CRYPTO",
}
PII_MIN_SCORE = 0.5


def pii_scan(text: str, analyzer=None, anonymizer=None) -> dict:
    """Task 9a: Quét PII trong văn bản bằng Presidio (một lần analyze), thay PII bằng <TYPE>.

    Returns:
        {
          "has_pii":    bool,
          "entities":   [{"type": str, "text": str, "score": float, "start": int, "end": int}],
          "anonymized": str,   # text với PII được thay bằng <TYPE>
        }
    """
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()

    found = [r for r in analyzer.analyze(text=text, language=PRESIDIO_LANGUAGE)
             if r.entity_type in PII_ENTITY_TYPES and r.score >= PII_MIN_SCORE]
    if not found:
        return {"has_pii": False, "entities": [], "anonymized": text}

    entities = [{"type": r.entity_type, "text": text[r.start:r.end], "score": round(float(r.score), 3),
                 "start": r.start, "end": r.end}
                for r in sorted(found, key=lambda r: (r.start, -r.score))]
    anonymized = anonymizer.anonymize(text=text, analyzer_results=found).text
    return {"has_pii": True, "entities": entities, "anonymized": anonymized}


# ─── Task 9b + 11: NeMo Guardrails ───────────────────────────────────────────

def setup_nemo_rails():
    """Khởi tạo NeMo Guardrails từ guardrails/config.yml. (Đã implement sẵn)

    Config directory: guardrails/
        config.yml  — model + rails config
        rails.co    — câu từ chối Colang 1.0; built-in self-check flows được bật trong YAML
    """
    from nemoguardrails import RailsConfig, LLMRails
    config = RailsConfig.from_path(GUARDRAILS_CONFIG_DIR)
    rails  = LLMRails(config)
    return rails


def _rail_stopped(result) -> bool:
    """Read the rails' own decision from the generation log (never infer it from words in the text)."""
    log = getattr(result, "log", None)
    return any(getattr(rail, "stop", False) for rail in (getattr(log, "activated_rails", None) or []))


async def check_input_rail(text: str, rails=None) -> dict:
    """Task 9b: Kiểm tra input qua NeMo input rails (self check input: topic + jailbreak + injection).

    Returns:
        {
          "allowed":        bool,
          "blocked_reason": str | None,
          "response":       str,          # NeMo's raw response
        }
    """
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": text}],
        options={"rails": ["input"], "log": {"activated_rails": True}},
    )
    blocked = _rail_stopped(result)
    return {
        "allowed": not blocked,
        "blocked_reason": "nemo_input_rail" if blocked else None,
        "response": result.response[0]["content"],
    }


async def check_output_rail(question: str, answer: str, rails=None) -> dict:
    """Task 11: Kiểm tra câu trả lời (đã có) qua NeMo output rails, trong ngữ cảnh question + answer.

    Self-check này chặn PII/thông tin mật; nó không thay RAGAS faithfulness hay kiểm tra factual accuracy.

    Returns:
        {
          "safe":           bool,
          "flagged_reason": str | None,
          "final_answer":   str,          # answer gốc nếu an toàn, câu từ chối của rail nếu bị chặn
        }
    """
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": question},
                  {"role": "assistant", "content": answer}],
        options={"rails": ["output"], "log": {"activated_rails": True}},
    )
    flagged = _rail_stopped(result)
    return {
        "safe": not flagged,
        "flagged_reason": "nemo_output_rail" if flagged else None,
        "final_answer": result.response[0]["content"] if flagged else answer,
    }


# ─── Task 10: Adversarial Test Suite ─────────────────────────────────────────

def run_adversarial_suite(adversarial_set: list[dict], rails=None,
                           analyzer=None, anonymizer=None) -> list[dict]:
    """Task 10: Chạy các input qua guard stack (Presidio → NeMo input) trong MỘT event loop, so với expected.

    Input đã bị Presidio chặn thì không gửi tiếp sang NeMo (không tốn LLM call, không lộ PII ra model).

    Returns:
        list of {
          "id": int, "category": str, "input": str,
          "expected": "blocked"|"allowed",
          "actual":   "blocked"|"allowed",
          "blocked_by": str | None,       # "presidio" | "nemo_input" | None
          "passed": bool,
        }
    """
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def _run_all() -> list[dict]:
        rows = []
        for item in adversarial_set:
            blocked_by = None
            if pii_scan(item["input"], analyzer, anonymizer)["has_pii"]:
                blocked_by = "presidio"
            elif not (await check_input_rail(item["input"], rails))["allowed"]:
                blocked_by = "nemo_input"
            actual = "blocked" if blocked_by else "allowed"
            rows.append({
                "id": item["id"], "category": item["category"], "input": item["input"],
                "expected": item["expected"], "actual": actual, "blocked_by": blocked_by,
                "passed": actual == item["expected"],
            })
        return rows

    rows = asyncio.run(_run_all())
    print(f"Guard suite: {sum(r['passed'] for r in rows)}/{len(rows)} passed")
    return rows


# ─── Task 12: P95 Latency Measurement ────────────────────────────────────────

def measure_p95_latency(test_inputs: list[str], n_runs: int = 20,
                         rails=None, analyzer=None, anonymizer=None) -> dict:
    """Task 12: Đo tuần tự hai INPUT layers (Presidio rồi NeMo input), không phải latency end-to-end.

    Một event loop; 2 lượt warm-up thật cho mỗi layer (không tính); sau đó đúng n_runs mẫu (xoay vòng input),
    luôn đo CẢ hai layer. perf_counter, giữ milliseconds thô; summarize_latency() tính percentile tuyến tính.
    """
    from src.experiment_support import summarize_latency
    if not test_inputs or n_runs < 1:
        raise ValueError("Need inputs and n_runs >= 1")
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()
    warmup_runs = 2

    async def _measure() -> list[dict]:
        for i in range(warmup_runs):
            text = test_inputs[i % len(test_inputs)]
            pii_scan(text, analyzer, anonymizer)
            await check_input_rail(text, rails)
        samples = []
        for i in range(n_runs):
            text = test_inputs[i % len(test_inputs)]
            t0 = time.perf_counter()
            pii_scan(text, analyzer, anonymizer)
            t1 = time.perf_counter()
            await check_input_rail(text, rails)
            t2 = time.perf_counter()
            pii_ms, nemo_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
            samples.append({"presidio_ms": pii_ms, "nemo_input_ms": nemo_ms,
                            "input_guard_ms": pii_ms + nemo_ms})
        return samples

    return summarize_latency(asyncio.run(_measure()), warmup_runs=warmup_runs)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "c", *sys.argv[1:]]))
