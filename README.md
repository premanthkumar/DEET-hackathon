# Resume-to-DEET Instant Registration System
### *with Automated Job Vacancy Discovery*

> **AI-powered platform** that converts any resume into a completed DEET profile and continuously discovers verified job vacancies from employer career pages.

---

## 🚀 Quick Start (Windows)

```bash
# 1. First-time setup (installs everything)
setup.bat

# 2. Start the server
run.bat

# 3. Open in browser
http://localhost:5000
```

**Requirements:** Python 3.10+ — [Download here](https://www.python.org/downloads/) *(check "Add to PATH")*

---

## 📁 Project Structure

```
iridescent-cosmic/
│
├── app.py                    # Flask API entry point (all routes)
├── config.py                 # Configuration constants
├── database.py               # SQLite CRUD helpers
├── requirements.txt          # Python dependencies
├── setup.bat                 # One-click Windows setup
├── run.bat                   # Quick server launcher
│
├── modules/
│   ├── ocr_engine.py         # PDF/image text extraction (pdfplumber + Tesseract)
│   ├── nlp_extractor.py      # NLP pipeline (spaCy + regex rules)
│   ├── confidence_scorer.py  # Per-field confidence scoring (0.0–1.0)
│   ├── job_scraper.py        # Career page web scraper (BeautifulSoup)
│   ├── job_classifier.py     # ML job category classifier (TF-IDF + LR)
│   ├── deduplicator.py       # Cosine similarity duplicate detector
│   ├── employer_verifier.py  # Domain trust scorer (DNS + WHOIS)
│   └── scheduler.py          # APScheduler automated crawl jobs
│
├── templates/
│   ├── index.html            # Landing page + resume upload
│   ├── preview.html          # Editable DEET profile preview
│   └── jobs.html             # Job discovery board
│
├── static/
│   ├── css/style.css         # Dark-mode design system
│   └── js/
│       ├── main.js           # Shared utilities (upload, toast, demo)
│       ├── preview.js        # Profile form editor logic
│       └── jobs.js           # Job board + crawl trigger
│
└── tests/
    ├── test_nlp_extractor.py     # NLP field extraction tests
    ├── test_confidence_scorer.py # Confidence scoring tests
    ├── test_deduplicator.py      # Duplicate detection tests
    └── test_api.py               # Flask endpoint integration tests
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Landing page (upload UI) |
| `GET`  | `/jobs` | Job discovery board |
| `GET`  | `/preview` | DEET profile editor |
| `POST` | `/api/resume/upload` | Upload resume → returns extracted profile JSON |
| `POST` | `/api/resume/submit` | Save final profile to database |
| `GET`  | `/api/resume/profiles` | List all saved profiles |
| `GET`  | `/api/jobs/list` | Paginated job listing (filter by category, location, search) |
| `POST` | `/api/jobs/crawl` | Trigger immediate job crawl |
| `POST` | `/api/jobs/add` | Manually add job posting |
| `GET`  | `/api/dashboard/stats` | Platform statistics |
| `GET`  | `/api/health` | Health check |

---

## Module 1 — Resume-to-DEET Pipeline

```
Upload (PDF/DOCX/Image)
        │
        ▼
   OCR Engine (ocr_engine.py)
   ├── Native PDF  → pdfplumber
   ├── Scanned PDF → pytesseract
   └── Image       → PIL + pytesseract
        │
        ▼
   NLP Extractor (nlp_extractor.py)
   ├── Section Detection  (regex headers)
   ├── NER                (spaCy en_core_web_sm)
   ├── Pattern Matching   (email, phone, LinkedIn)
   ├── Skills Extraction  (keyword dictionary)
   └── Date Normalization (dateutil)
        │
        ▼
   Confidence Scorer (confidence_scorer.py)
   └── Per-field score 0.0–1.0 → HIGH/MEDIUM/LOW color display
        │
        ▼
   Editable Preview → User reviews → Submit to DB
```

**Extracted fields:** Full Name · Email · Phone · Address · LinkedIn · GitHub · Summary · Education · Skills · Certifications · Work Experience · Projects

---

## Module 2 — Job Vacancy Discovery Pipeline

```
APScheduler (every 6h) or Manual Trigger
        │
        ▼
   Job Scraper (job_scraper.py)
   └── requests + BeautifulSoup per career page
        │
        ▼
   Field Extraction
   ├── Experience level (regex patterns)
   └── Skills required  (keyword matching)
        │
        ▼
   Deduplicator (deduplicator.py)
   ├── Exact: SHA-256 hash of (title+company+location)
   └── Near-dup: TF-IDF cosine similarity ≥ 0.85
        │
        ▼
   Job Classifier (job_classifier.py)
   └── TF-IDF + Logistic Regression (fallback: keyword rules)
        │
        ▼
   Employer Verifier (employer_verifier.py)
   ├── DNS resolution  +0.25
   ├── HTTP reachable  +0.25
   ├── HTTPS           +0.20
   └── Domain age      +0.30 (≥1 yr) / +0.20 (≥180 days)
        │
        ▼
   Save to SQLite → Appear on Job Board
```

---

## 🏋️ Running Tests

```bash
# Activate your venv first
.venv\Scripts\activate.bat

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_nlp_extractor.py -v
python -m pytest tests/test_api.py -v
```

---

## ⚙️ Configuration

Edit `config.py` to customise:

| Setting | Default | Description |
|---------|---------|-------------|
| `CRAWL_INTERVAL_HOURS` | `6` | How often to auto-crawl |
| `DEDUP_COSINE_THRESHOLD` | `0.85` | Near-duplicate sensitivity |
| `MIN_DOMAIN_AGE_DAYS` | `180` | Employer trust threshold |
| `TARGET_CAREER_PAGES` | `[example.com]` | Add your target career page URLs |
| `JOB_CATEGORIES` | 10 categories | DEET classification taxonomy |

### Adding Career Pages

In `config.py`, add entries to `TARGET_CAREER_PAGES`:

```python
{
    "company":          "My Company",
    "url":              "https://mycompany.com/careers",
    "job_selector":     ".job-listing",      # CSS selector for each job block
    "title_selector":   ".job-title",
    "location_selector":".job-location",
    "link_selector":    "a",
},
```

---

## 📊 Evaluation Metrics

| Metric | Target | Method |
|--------|--------|--------|
| Field Extraction F1 | ≥ 85% | Compare vs. gold-labeled test resumes |
| OCR Character Error Rate | ≤ 5% | Known text vs. OCR output |
| Job Discovery Precision | ≥ 90% | Manual audit of scraped jobs |
| Duplicate Detection Rate | ≥ 95% | Injected known-duplicate test set |
| Resume API Latency (p95) | ≤ 5s | End-to-end timing logs |

---

## 💡 Hackathon Innovation Highlights

| Feature | Innovation |
|---------|-----------|
| **Hybrid OCR+NLP** | Falls back from native PDF → scanned OCR → image OCR automatically |
| **Confidence UI** | Color-coded per-field confidence badges guide users to fix weak extractions |
| **Demo Mode** | One-click demo loads a pre-filled profile without needing a real resume |
| **Dual Dedup** | SHA-256 exact + TF-IDF cosine near-duplicate detection |
| **Trust Score** | Multi-factor employer verification (DNS + WHOIS + HTTPS) |
| **Zero-config ML** | Keyword fallback classifier works with zero training data |
| **Auto-scheduler** | Background 6-hour crawl runs without any cron or external service |

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `flask` | REST API and HTML templating |
| `pdfplumber` | Native PDF text extraction |
| `pytesseract` | OCR for scanned documents |
| `spacy` | Named Entity Recognition |
| `scikit-learn` | TF-IDF vectorization + job classifier |
| `beautifulsoup4` | HTML parsing for web scraper |
| `APScheduler` | Background job scheduling |
| `python-whois` | Domain age verification |

---

*Built for the DEET Hackathon — February 2026*
