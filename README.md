# GCP Data Engineer Exam Preparation

A Streamlit application for studying the **Google Cloud Professional Data Engineer** certification exam. It loads a curated dataset of multiple-choice questions extracted from an official exam-prep PDF and provides browsing, timed practice quizzes, and statistics over the question bank.

---

## Features

- **Browse Questions** — full-text search and topic filtering across all 307 questions.
- **Practice Quiz** — configurable quiz (10–50 questions) with optional topic scoping (BigQuery, Database, Cloud Storage, Data Processing). Mixes single-choice and multi-choice questions automatically.
- **Image Support** — diagrams referenced by questions or specific answer options are rendered inline.
- **Statistics Dashboard** — question distribution by topic, community-vote consensus levels, correct-answer distribution, and image coverage.
- **Multi-exam ready** — drop additional exam JSONs into `output/` and they appear in the sidebar selector.

---

## Project Structure

```
GCP_Data_Engineer_prep/
├── app.py                  # Streamlit UI (Browse / Quiz / Statistics / About pages)
├── extract_pdf.py          # Offline tool: PDF -> structured JSON + images
├── requirements.txt        # Runtime dependencies (app only, not extractor)
├── exams/                  # Source PDFs (input to extract_pdf.py)
│   └── Questions_Professional_Data_engineer.pdf
├── output/                 # Extracted question banks (consumed by app.py)
│   └── Data Engineer.json
├── extracted_images/       # Images extracted from PDFs, named <question>_<idx>.<ext>
└── README.md
```

### Data flow

```
exams/*.pdf  --extract_pdf.py-->  output/<Exam Name>.json + extracted_images/*
                                          │
                                          ▼
                                       app.py  --streamlit run-->  Browser UI
```

The extraction is a **one-off offline step**. The app only reads the JSON and images — it doesn't touch the PDFs.

---

## Requirements

- Python 3.10 or newer (Python 3.14 supported via the unpinned dependency ranges).
- The runtime dependencies in `requirements.txt`:
  - `streamlit>=1.40.0`
  - `pandas>=2.3.0`
  - `matplotlib>=3.9.0`
- For re-running the PDF extractor only: `PyMuPDF` (not in `requirements.txt` to keep the deployed app slim).

---

## Installation

```bash
git clone https://github.com/MarianGO96/GCP_Data_Engineer_prep.git
cd GCP_Data_Engineer_prep

# Create and activate a virtual environment (optional but recommended)
python3 -m venv env
source env/bin/activate          # macOS / Linux
# .\env\Scripts\activate         # Windows

# Install runtime dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

---

## Usage

The sidebar always shows:
- The **selected exam** (auto-discovered from JSON files in `output/`).
- **Total questions** in the selected bank.
- A **navigation radio** for the four pages.

### 1. Browse Questions
- Free-text search over the question text.
- Topic filter (keyword-based; questions not matching a known topic appear under "All").
- Each question expands to show options; click "Show correct answer" to reveal the answer plus the community-vote distribution.

### 2. Practice Quiz
- Slider for number of questions (10–50).
- Optional **topic multiselect** — quiz draws only from questions matching the selected topic keywords. Empty selection = all questions.
- Click **Start New Quiz** to begin. Navigate with **Previous** / **Next** / **Finish Quiz**.
- After finishing, you get a score, a passing-threshold visualization (70%), a results table colour-coded by correctness, and a per-question review with your answer vs. the correct answer.

### 3. Statistics
- Bar chart of question counts by topic.
- Bar chart of community-consensus tiers (Strong / Moderate / Split / Highly Debated).
- Pie chart of correct-answer distribution (A/B/C/D/Multi).
- Pie chart showing how many questions have associated images.

### 4. About
Static description of the app and its data sources.

---

## Re-extracting Questions from a PDF

Only needed if you want to refresh the question bank from a new or updated PDF.

```bash
# Install the extra dependency (not in requirements.txt)
pip install PyMuPDF

# Place the PDF in exams/ then run:
python extract_pdf.py "Questions_Professional_Data_engineer.pdf"
# or, with no argument, it picks the first PDF found in exams/
python extract_pdf.py
```

The script writes:
- `output/<sanitized_name>.json` — list of questions with text, options, correct answer, community votes, and image refs.
- `extracted_images/<question>_<index>.<ext>` — images embedded in the PDF (very small images <20px are skipped).

**Case-study questions are skipped** — the parser detects the phrase "case study" and excludes those blocks.

### JSON schema (per question)

```jsonc
{
  "question_number": 42,
  "question_text": "...",
  "answers": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "correct_answer": "B",                 // or "ABC" for multi-answer
  "Community vote distribution": "B (78%) C (22%)",
  "images": ["extracted_images/42_0.png"]
}
```

Images named with a letter suffix (e.g. `44_a.png`, `44_b.png`) are treated by the app as **answer-specific** images and rendered next to that option.

---

## Deployment (Streamlit Community Cloud)

1. Push the repo to GitHub.
2. Sign in at [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Pick the repo, branch `main`, and main file `app.py`.
4. Click **Deploy**.

**Tips:**
- If the build fails on dependency install, check the Python version in **Advanced settings** — Streamlit Cloud may default to a Python version newer than your pins support. Either bump the pins or pin the runtime to Python 3.12.
- The deployed app reads from `output/` and `extracted_images/` directly, so any new exam JSON committed to the repo appears automatically after redeploy.

---

## Known Limitations

- **Topic detection is keyword-based.** A question is tagged "BigQuery" only if the literal word appears; questions phrased around features (e.g. "partitioned tables") may end up under "Other".
- **Quiz results are not persisted.** Every quiz is independent; closing the tab discards history.
- **Case-study questions are excluded** by design (the extractor drops them).

---

## Tech Stack

- **Streamlit** — UI and state management.
- **pandas / matplotlib** — tables and statistics charts.
- **PyMuPDF (fitz)** — PDF parsing and image extraction (offline only).

---

## License & Disclaimer

Provided for **educational purposes only**. All exam content is sourced from publicly available preparation materials and is intended to support personal study for the Google Cloud Professional Data Engineer certification. This project is not affiliated with or endorsed by Google.
