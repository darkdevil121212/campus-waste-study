from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_FILE = "data/responses.db"

def get_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            department TEXT,
            year TEXT,
            segregates_waste TEXT,
            frequency TEXT,
            wet_dry_knowledge TEXT,
            common_mistakes TEXT,
            barriers TEXT,
            awareness_score INTEGER,
            bin_availability TEXT,
            suggestions TEXT,
            food_waste_disposal TEXT,
            reusable_container_use TEXT,
            plastic_separation_confidence TEXT,
            recycling_education_rating TEXT,
            waste_stream_improvement TEXT,
            participated_collections TEXT,
            peer_encouragement TEXT,
            main_nonsegregation_reason TEXT,
            e_waste_disposal_knowledge TEXT,
            visible_bin_rating INTEGER
        )
    ''')

    existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(responses)")]
    extra_columns = [
        ("food_waste_disposal", "TEXT"),
        ("reusable_container_use", "TEXT"),
        ("plastic_separation_confidence", "TEXT"),
        ("recycling_education_rating", "TEXT"),
        ("waste_stream_improvement", "TEXT"),
        ("participated_collections", "TEXT"),
        ("peer_encouragement", "TEXT"),
        ("main_nonsegregation_reason", "TEXT"),
        ("e_waste_disposal_knowledge", "TEXT"),
        ("visible_bin_rating", "INTEGER")
    ]
    for col_name, col_type in extra_columns:
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE responses ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/survey")
def survey():
    return render_template("survey.html")

@app.route("/submit", methods=["POST"])
def submit():
    conn = get_db()
    conn.execute('''
        INSERT INTO responses (
            timestamp, department, year, segregates_waste, frequency,
            wet_dry_knowledge, common_mistakes, barriers,
            awareness_score, bin_availability, suggestions,
            food_waste_disposal, reusable_container_use,
            plastic_separation_confidence, recycling_education_rating,
            waste_stream_improvement, participated_collections,
            peer_encouragement, main_nonsegregation_reason,
            e_waste_disposal_knowledge, visible_bin_rating
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        request.form.get("department"),
        request.form.get("year"),
        request.form.get("segregates_waste"),
        request.form.get("frequency"),
        request.form.get("wet_dry_knowledge"),
        ", ".join(request.form.getlist("common_mistakes")),
        ", ".join(request.form.getlist("barriers")),
        int(request.form.get("awareness_score", 5)),
        request.form.get("bin_availability"),
        request.form.get("suggestions", ""),
        request.form.get("food_waste_disposal"),
        request.form.get("reusable_container_use"),
        request.form.get("plastic_separation_confidence"),
        request.form.get("recycling_education_rating"),
        request.form.get("waste_stream_improvement"),
        request.form.get("participated_collections"),
        request.form.get("peer_encouragement"),
        request.form.get("main_nonsegregation_reason"),
        request.form.get("e_waste_disposal_knowledge"),
        int(request.form.get("visible_bin_rating", 5))
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("thank_you"))

@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/classifier")
def classifier():
    return render_template("classifier.html")

@app.route("/api/stats")
def api_stats():
    conn = get_db()
    rows = conn.execute("SELECT * FROM responses").fetchall()
    conn.close()

    if not rows:
        return jsonify({"total": 0})

    total = len(rows)

    seg_counts = {}
    freq_counts = {}
    dept_counts = {}
    barrier_counts = {}
    year_counts = {}
    bin_counts = {}

    for r in rows:
        def count(d, k): d[k] = d.get(k, 0) + 1

        count(seg_counts,  r["segregates_waste"] or "Unknown")
        count(freq_counts, r["frequency"] or "Unknown")
        count(dept_counts, r["department"] or "Unknown")
        count(year_counts, r["year"] or "Unknown")
        count(bin_counts,  r["bin_availability"] or "Unknown")

        for b in (r["barriers"] or "").split(", "):
            if b.strip():
                count(barrier_counts, b.strip())

    avg_awareness = sum(r["awareness_score"] or 5 for r in rows) / total

    return jsonify({
        "total": total,
        "segregation": seg_counts,
        "frequency": freq_counts,
        "departments": dept_counts,
        "avg_awareness": round(avg_awareness, 2),
        "barriers": barrier_counts,
        "year": year_counts,
        "bin_availability": bin_counts
    })

@app.route("/api/responses")
def api_responses():
    conn = get_db()
    rows = conn.execute("SELECT * FROM responses ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/classify", methods=["POST"])
def classify():
    item = request.json.get("item", "").lower().strip()
    waste_db = {
        "banana":    ("Wet / Organic",    "#22c55e", "Banana peels decompose naturally — perfect for composting."),
        "apple":     ("Wet / Organic",    "#22c55e", "Fruit waste goes to the green/wet bin."),
        "food":      ("Wet / Organic",    "#22c55e", "Food scraps belong in the wet/organic waste bin."),
        "vegetable": ("Wet / Organic",    "#22c55e", "Vegetable waste is organic and compostable."),
        "rice":      ("Wet / Organic",    "#22c55e", "Cooked or uncooked rice is organic waste."),
        "leaves":    ("Wet / Organic",    "#22c55e", "Fallen leaves are organic — green bin!"),
        "egg":       ("Wet / Organic",    "#22c55e", "Eggshells go to the organic bin."),
        "tea":       ("Wet / Organic",    "#22c55e", "Tea leaves and uncoated bags are organic waste."),
        "paper":     ("Dry / Recyclable", "#3b82f6", "Clean paper is 100% recyclable."),
        "newspaper": ("Dry / Recyclable", "#3b82f6", "Newspapers can be recycled directly."),
        "bottle":    ("Dry / Recyclable", "#3b82f6", "Rinse bottles before putting them in the dry bin."),
        "plastic":   ("Dry / Recyclable", "#3b82f6", "Clean dry plastics are recyclable."),
        "glass":     ("Dry / Recyclable", "#3b82f6", "Glass bottles and jars go to dry/recyclable bin."),
        "cardboard": ("Dry / Recyclable", "#3b82f6", "Flatten cardboard boxes before recycling."),
        "can":       ("Dry / Recyclable", "#3b82f6", "Metal cans are recyclable — rinse them first!"),
        "metal":     ("Dry / Recyclable", "#3b82f6", "Most metals are recyclable."),
        "notebook":  ("Dry / Recyclable", "#3b82f6", "Old notebooks go to dry bin after removing spirals."),
        "battery":   ("Hazardous",        "#ef4444", "Batteries contain toxic chemicals — use designated drop-offs."),
        "medicine":  ("Hazardous",        "#ef4444", "Expired medicines must go to pharmacy take-back points."),
        "paint":     ("Hazardous",        "#ef4444", "Paints are chemical waste — take to a hazardous drop-off."),
        "chemical":  ("Hazardous",        "#ef4444", "Lab chemicals must follow your institution's disposal protocol."),
        "syringe":   ("Hazardous",        "#ef4444", "Sharps go into dedicated sharps containers only."),
        "bulb":      ("Hazardous",        "#ef4444", "CFL bulbs contain mercury — dispose at e-waste collection points."),
        "phone":     ("E-Waste",          "#a855f7", "Old phones go to e-waste collection drives."),
        "laptop":    ("E-Waste",          "#a855f7", "Laptops contain valuable metals — always e-waste them."),
        "charger":   ("E-Waste",          "#a855f7", "Cables and chargers are e-waste."),
        "computer":  ("E-Waste",          "#a855f7", "Computers must go to certified e-waste recyclers."),
        "keyboard":  ("E-Waste",          "#a855f7", "Electronic peripherals are e-waste."),
        "wire":      ("E-Waste",          "#a855f7", "Electric wires are e-waste."),
    }
    for keyword, (category, color, tip) in waste_db.items():
        if keyword in item:
            return jsonify({"category": category, "color": color, "tip": tip, "found": True})
    return jsonify({
        "category": "Unknown", "color": "#6b7280",
        "tip": "We couldn't classify this. When in doubt, check with your campus waste management team.",
        "found": False
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
