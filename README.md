# Campus Waste Segregation Behavior Study
**Statistical Data Science CS Project**

## Features
- **Landing Page** — Project overview with live response count
- **Survey** — 10-question behavioral survey with progress bar
- **Analytics Dashboard** — 6 live charts (doughnut, bar, pie) powered by Chart.js
- **Waste Classifier** — Type any item to get bin category + tips
- **REST API** — `/api/stats` and `/api/classify` endpoints
- **JSON data storage** — All responses saved in `data/responses.json`

## How to Run

### 1. Install dependencies
```bash
pip install flask
```

### 2. Start the server
```bash
cd campus_waste_study
python app.py
```

### 3. Open your browser
```
http://localhost:5000
```

## Project Structure
```
campus_waste_study/
├── app.py                  ← Flask backend (routes + API)
├── requirements.txt
├── data/
│   └── responses.json      ← Auto-created when first survey submitted
└── templates/
    ├── base.html           ← Navigation + shared layout
    ├── index.html          ← Landing page
    ├── survey.html         ← 10-question survey form
    ├── thank_you.html      ← Post-submission page
    ├── dashboard.html      ← Analytics charts (Chart.js)
    └── classifier.html     ← Waste item classifier
```

## API Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/api/stats` | GET | Returns all aggregated survey statistics |
| `/api/classify` | POST | Classifies a waste item — body: `{"item": "banana"}` |

## Pages
| Route | Description |
|---|---|
| `/` | Home / landing page |
| `/survey` | Fill out the survey |
| `/dashboard` | View live analytics charts |
| `/classifier` | Classify any waste item |
