# Autonomous Code Review Agent

try the agent : https://codereviewagent.streamlit.app/

A small, beginner-friendly AI agent that reviews a **Git diff** or **Python
source file** and produces a structured **Markdown review report**.

It is built with [LangGraph](https://langchain-ai.github.io/langgraph/) for the
workflow, [LangChain](https://python.langchain.com/) for the LLM integration,
[Pydantic](https://docs.pydantic.dev/) for structured output, and works with
OpenAI, Groq, or OpenRouter.

The workflow is intentionally simple:

```
START -> Review Node -> Report Node -> END
```

- **Review Node** – sends the code to the LLM and asks for structured findings.
- **Report Node** – formats those findings into a Markdown report.

## What it finds

For each issue it reports a severity (**Critical / High / Medium / Low**), the
file and line (when known), a category (Bug, Security, Performance, Code
Quality), a plain-language explanation, and a suggested fix.

## Safety and scope

This first version is **read-only**:

- Submitted code is treated as untrusted input and is **never executed**.
- Source files are **never modified**.
- No commits are created and no pull requests are merged.
- Findings are **AI-generated suggestions that require human verification**.
  The report says so explicitly.

## Project structure

```
autonomous-code-review-agent/
├── code_review_agent/
│   ├── __init__.py
│   └── graph.py
├── app.py
├── sample.diff
├── review.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

Requires **Python 3.10+** (tested on 3.13).

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
```

## Configure your API key

Open `.env` and set at least `LLM_API_KEY`. Pick one of these profiles:

**OpenAI**

```env
LLM_API_KEY=sk-...
LLM_BASE_URL=
LLM_MODEL=gpt-4o-mini
```

**Groq**

```env
LLM_API_KEY=gsk_...
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
```

**OpenRouter**

```env
LLM_API_KEY=sk-or-...
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
```

`.env` is git-ignored, so your key is never committed.

## Run it

Review the bundled sample diff:

```bash
python review.py sample.diff -o review.md
```

Or review any file (a diff, or a plain Python file):

```bash
python review.py path\to\change.diff
python review.py path\to\module.py --model gpt-4o
```

Options:

- `-o, --output FILE` – write the report to a file instead of stdout.
- `--model NAME` – override the model from `.env` for a single run.

## Run the web UI

A small Streamlit UI is included. It lets you **paste a code snippet** or
**upload a `.py` / `.diff` file**, then shows the review in the page (with a
download button for the Markdown report).

```bash
streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) and opens it in
your browser. Paste or upload your code, then click **Review code**. The
optional **Model** field in the sidebar overrides `LLM_MODEL` for that run.

The UI uses the exact same read-only workflow as the CLI, so the same safety
guarantees apply: nothing is executed, nothing is modified, and every finding
is labeled as an AI suggestion.

### Expected output

The report looks like this:

```markdown
# Code Review Report

## Summary
A brief summary of the code changes.

## Findings

### [HIGH] Incorrect comparison operator
- File: example.py
- Line: 5
- Category: Bug
- Explanation: The comparison may use object identity
  instead of checking value equality.
- Recommendation: Use == instead of is where appropriate.

## What Looks Good
- Positive observations about the code.

## Next Steps
- Suggested fixes and tests.
```

## Error handling

The CLI exits gracefully (with a clear message) when:

- the input file is missing or is a directory (exit code 1),
- the input file is empty (exit code 1),
- no API key is configured (exit code 2),
- the LLM/API call fails (exit code 3).

## How it works (for beginners)

1. `review.py` reads your file and calls `review_diff()` in `graph.py`.
2. `graph.py` compiles a two-node LangGraph `StateGraph`.
3. The **review node** calls the LLM with `with_structured_output(ReviewResult)`,
   so the model must return data matching the Pydantic model — no fragile
   text parsing.
4. The **report node** turns that structured data into Markdown.
5. The finished report is printed or written to your chosen file.

## Limitations and next steps

- The model only sees the diff you provide; it does not read the whole repo.
- Line numbers are only reported when they can be inferred from the diff.
- No tests are executed and no code is changed.
- Ideas for later: review whole directories, add a GitHub Actions workflow,
  or post findings as PR comments (still without auto-merging).
