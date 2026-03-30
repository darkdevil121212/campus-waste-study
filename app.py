from flask import Flask, render_template, request, jsonify, redirect, url_for
import json, os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "data/responses.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/survey")
def survey():
    return render_template("survey.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = load_data()
    entry = {
        "id": len(data) + 1,
        "timestamp": datetime.now().isoformat(),
        "department": request.form.get("department"),
        "year": request.form.get("year"),
        "segregates_waste": request.form.get("segregates_waste"),
        "frequency": request.form.get("frequency"),
        "wet_dry_knowledge": request.form.get("wet_dry_knowledge"),
        "common_mistakes": request.form.getlist("common_mistakes"),
        "barriers": request.form.getlist("barriers"),
        "awareness_score": int(request.form.get("awareness_score", 5)),
        "bin_availability": request.form.get("bin_availability"),
        "suggestions": request.form.get("suggestions", "")
    }
    data.append(entry)
    save_data(data)
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
    data = load_data()
    if not data:
        return jsonify({"total": 0})
    total = len(data)
    seg_counts = {}
    freq_counts = {}
    dept_counts = {}
    barrier_counts = {}
    year_counts = {}
    bin_counts = {}
    for r in data:
        v = r.get("segregates_waste","Unknown"); seg_counts[v] = seg_counts.get(v,0)+1
        v = r.get("frequency","Unknown"); freq_counts[v] = freq_counts.get(v,0)+1
        v = r.get("department","Unknown"); dept_counts[v] = dept_counts.get(v,0)+1
        v = r.get("year","Unknown"); year_counts[v] = year_counts.get(v,0)+1
        v = r.get("bin_availability","Unknown"); bin_counts[v] = bin_counts.get(v,0)+1
        for b in r.get("barriers",[]): barrier_counts[b] = barrier_counts.get(b,0)+1
    avg_awareness = sum(r.get("awareness_score",5) for r in data) / total
    return jsonify({"total":total,"segregation":seg_counts,"frequency":freq_counts,
        "departments":dept_counts,"avg_awareness":round(avg_awareness,2),
        "barriers":barrier_counts,"year":year_counts,"bin_availability":bin_counts})

@app.route("/api/classify", methods=["POST"])
def classify():
    item = request.json.get("item","").lower().strip()
    waste_db = {
        "banana":("Wet / Organic","#22c55e","Banana peels decompose naturally — perfect for composting."),
        "apple":("Wet / Organic","#22c55e","Fruit waste goes to the green/wet bin."),
        "food":("Wet / Organic","#22c55e","Food scraps belong in the wet/organic waste bin."),
        "vegetable":("Wet / Organic","#22c55e","Vegetable waste is organic and compostable."),
        "rice":("Wet / Organic","#22c55e","Cooked or uncooked rice is organic waste."),
        "leaves":("Wet / Organic","#22c55e","Fallen leaves are organic — green bin!"),
        "egg":("Wet / Organic","#22c55e","Eggshells go to the organic bin."),
        "tea":("Wet / Organic","#22c55e","Tea leaves and uncoated bags are organic waste."),
        "paper":("Dry / Recyclable","#3b82f6","Clean paper is 100% recyclable."),
        "newspaper":("Dry / Recyclable","#3b82f6","Newspapers can be recycled directly."),
        "bottle":("Dry / Recyclable","#3b82f6","Rinse bottles before putting them in the dry bin."),
        "plastic":("Dry / Recyclable","#3b82f6","Clean dry plastics are recyclable."),
        "glass":("Dry / Recyclable","#3b82f6","Glass bottles and jars go to dry/recyclable bin."),
        "cardboard":("Dry / Recyclable","#3b82f6","Flatten cardboard boxes before recycling."),
        "can":("Dry / Recyclable","#3b82f6","Metal cans are recyclable — rinse them first!"),
        "metal":("Dry / Recyclable","#3b82f6","Most metals are recyclable."),
        "notebook":("Dry / Recyclable","#3b82f6","Old notebooks go to dry bin after removing spirals."),
        "battery":("Hazardous","#ef4444","Batteries contain toxic chemicals — use designated drop-offs."),
        "medicine":("Hazardous","#ef4444","Expired medicines must go to pharmacy take-back points."),
        "paint":("Hazardous","#ef4444","Paints are chemical waste — take to a hazardous drop-off."),
        "chemical":("Hazardous","#ef4444","Lab chemicals must follow your institution's disposal protocol."),
        "syringe":("Hazardous","#ef4444","Sharps go into dedicated sharps containers only."),
        "bulb":("Hazardous","#ef4444","CFL bulbs contain mercury — dispose at e-waste collection points."),
        "phone":("E-Waste","#a855f7","Old phones go to e-waste collection drives."),
        "laptop":("E-Waste","#a855f7","Laptops contain valuable metals — always e-waste them."),
        "charger":("E-Waste","#a855f7","Cables and chargers are e-waste."),
        "computer":("E-Waste","#a855f7","Computers must go to certified e-waste recyclers."),
        "keyboard":("E-Waste","#a855f7","Electronic peripherals are e-waste."),
        "wire":("E-Waste","#a855f7","Electric wires are e-waste."),
    }
    for keyword,(category,color,tip) in waste_db.items():
        if keyword in item:
            return jsonify({"category":category,"color":color,"tip":tip,"found":True})
    return jsonify({"category":"Unknown","color":"#6b7280",
        "tip":"We couldn't classify this. When in doubt, check with your campus waste management team.","found":False})

if __name__ == "__main__":
    app.run(debug=True)
