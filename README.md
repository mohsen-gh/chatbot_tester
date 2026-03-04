# Chatbot Tester (Compact Overview)

Lightweight framework for evaluating a chatbot API against conversation tests. It
checks intent accuracy, keyword/fuzzy matches, and latency, producing both raw
and summary reports. The included Dockerized mock server simulates responses and
errors.

---

## Setup & run

1. **Start mock chatbot:** `docker compose up -d` (stops with `docker compose down`).
2. **Install Python deps:**
   ```bash
   uv sync    # or pip install -e .
   ```
3. **Run tests:**
   ```bash
   uv run tester/run_tests.py --dataset tester/data/test_cases.json --runs 3
   ```
   **Available Options:** 
   - `--dataset`: Path to the input JSON dataset containing test cases. *(Default: `tester/data/test_cases.json`)*
   - `--runs`: Number of times to execute the entire test suite (useful for testing LLM variability). *(Default: `1`)*
   - `--base-url`: The base URL of the target Chatbot API. *(Default: `http://localhost:8080`)*
   - `--output`: File path where the final summary JSON report will be saved. *(Default: `tester/data/report/report.json`)*
   - `--fuzzy-thresh`: The minimum similarity score (0.0 to 1.0) required for the fuzzy string matching fallback to pass. *(Default: `0.6`)*
   - `--verbose`: Enables detailed `DEBUG` level logging for deeper visibility into test execution.
4. **Results:** `report_raw.json` for all turns; `report.json` for summary.

---

## Architecture & decisions

```
chatbot_tester
├── chatbot/
│   ├── chatbot.py
│   ├── Dockerfile
│   └── schema.py
├── tester/
│   ├── run_tests.py
│   ├── data
│   │   ├── report/
│   │   └── test_cases.json
│   ├── schemas.py
│   ├── test_engine.py
│   └── utils/
│       ├── chat_client.py
│       ├── json_utils.py
│       ├── log_manager.py
│       └── text/
│           ├── intent_matcher.py
│           └── response_matcher.py
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── uv.lock
```
### Clean Architecture Principles Considered

**Chatbot Service** (mock server for testing)

To test the evaluation tool without needing a real AI model, this project includes a simple mock FastAPI server. It works by matching keywords in the user's message to return appropriate responses for the 10 topics in the test_cases.json dataset. This ensures the evaluator has a reliable baseline to check against.

To make sure the evaluation tool actually works in real-world conditions, the mock server intentionally misbehaves. It occasionally changes the expected intent, removes keywords from the response, or lowers its confidence score. It also randomly throws network errors like a 500 Internal Server Error or a 1-minute timeout. This controlled randomness proves that the evaluator can properly catch bad answers, handle API failures without crashing, and accurately report inconsistent behavior when tests are run multiple times.

**Tester Service** (main testing framework)

This is the core engine of the project, responsible for running the test dataset against the chatbot API and generating the final performance metrics. It is structured around clean code principles: it enforces a strict separation of concerns, uses small, single-responsibility functions and classes, and relies on clear, meaningful naming conventions. Strong type hinting is used throughout to ensure maintainability and developer clarity. 

Key responsibilities include:
- **Test Orchestration:** Reads the dataset sequentially and maintains conversation state across multiple turns using unique session IDs.
- **Robust Validation:** Evaluates both intent accuracy (with format normalization) and response quality, utilizing keyword matching with a fallback to semantic similarity. 
- **Resiliency & Aggregation:** Handles network failures and API timeouts gracefully. It aggregates metrics across multiple runs (`--runs N`) to calculate overall pass rates and detect unstable LLM behavior.
- **Reporting:** Outputs a quick-read console summary alongside a summary JSON and a detailed, actionable raw JSONL report for deeper analysis. 
- **CLI Configuration:** Runs locally via a flexible command-line interface, allowing easy configuration of the target API URL, input datasets, and the number of execution runs.

### Tester Project Files

**Core Engine**
- `run_tests.py` – CLI entry point; parses arguments and invokes TestEngine
- `test_engine.py` – Main orchestrator; streams test cases, runs iterations, aggregates results

**Schema**
- `schemas.py` – Pydantic models for requests, responses, input json data and json results and report

**Utilities** (`utils/`)
- `chat_client.py` – Synchronous HTTP client; posts queries to `/chat` endpoint
- `json_utils.py` – Streaming JSON reader/appender (ijson) and  serializer for large datasets
- `log_manager.py` – Setting up logger for the app

**Smart Matching** (`utils/text/`)
- `intent_matcher.py` – Normalizes intent strings (case, hyphens, spaces); matches against expected intents
- `response_matcher.py` – Dual-mode validation: direct keyword match + fuzzy-matching fallback with adjustable threshold.

**Sample Data** (`data/`)
- `test_cases.json` – A sample test case json file to be used as an input for the system.
- `report/` – A directory that reports will be stored by default.

---

## Assumptions

- Chat API POST `/chat` with `user_id` and `message`; returns
  `{response,intent,confidence}`.
- Tests defined in `tester/data/test_cases.json` as `{test_id,conversation}`.
- Intent matching normalized but exact; keywords matched case-insensitive with fallback to Fuzzy matching.
- Latency Calculation: Average latency is calculated exclusively using successful API responses. Timeouts and 500 Internal Server Errors are treated as failed test turns (impacting the pass rate metrics) rather than skewing the latency calculation with artificial 60-second ceilings."
- The input dataset could be huge. The framework supports streaming at both ends: **streaming JSON input** for loading test cases and **streaming raw output** for writing results. Rather than loading entire files into memory, it consumes input incrementally (record by record) and persists output incrementally (turn by turn).

  1. Streaming JSON input: large `.json` datasets can be processed one object at a time and converted into `TestCase`, keeping memory usage low.
  2. Streaming raw output: each `TurnResult` is appended immediately to `raw_output.jsonl`, so long runs stay memory-safe and already-written results remain available even if the process stops mid-run.
---

## Trade‑offs & limitations

- **Sync calls:** simpler but sequential; no parallelism.
- **No context:** Evaluations are performed on a strictly per-turn basis. The evaluator does not currently look at the entire conversation history context to judge the final turn, though it does maintain the **user_id** session for the chatbot's benefit.
- **Error reporting** is basic (string in result).
- **Static tests:** lacks dynamic generation.
- **Response Validation & Semantic Similarity:** The challenge allows for keyword matching or semantic similarity. I implemented a robust, case-insensitive substring matcher, combined with a lightweight fuzzy-matching fallback using Python's built-in difflib. While true semantic evaluation (e.g., using sentence-transformers or OpenAI embeddings) would better handle complex LLM paraphrasing, I intentionally opted against it to keep the dependency tree light, avoid heavy GPU/CPU overhead, and ensure the evaluation suite runs instantly in any CI/CD environment without external API keys."

---

## Future ideas

- **Parallel Execution:** Implement asynchronous batching (e.g., using `asyncio.gather`) to run independent test cases or multiple runs concurrently. This would drastically reduce the total execution time for large evaluation datasets.
- **HTML/CSV Reports:** Expand the reporting module to generate user-friendly HTML dashboards for QA teams, and CSV exports for easier integration with external BI tools or spreadsheets.
- **Plugin Matchers:** Refactor the validation logic to support pluggable, strategy-based matchers. This would allow developers to easily swap in advanced text-similarity models (like Sentence-Transformers or LLM-as-a-judge) without modifying the core evaluation engine.
- **Resilient API Calls (Retry Logic):** Implement a retry mechanism with exponential backoff in the ChatClient. This would prevent transient network issues or temporary 502 Bad Gateway / 429 Too Many Requests errors from falsely failing a test turn, separating true functional regressions from temporary infrastructure hiccups.

---

## Quick commands

| Action | Command |
|--------|---------|
| Start server | `docker compose up -d` |
| Stop server | `docker compose down` |
| Run once | `uv run tester/run_tests.py` |
| Run 5 times | `uv run tester/run_tests.py --runs 5` |


---

*See individual modules for more details.*
