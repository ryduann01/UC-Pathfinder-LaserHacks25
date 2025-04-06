from flask import Flask, render_template, request, jsonify
import pandas as pd
import re
from data_processing import tag_to_discipline, assign_major_discipline

app = Flask(__name__)

# Load Data
gpa_df = pd.read_csv("Combined_UC_Majors_UTF8.csv")
gpa_df["normalized_major"] = gpa_df["major_name"].apply(lambda x: re.sub(r'[^a-zA-Z0-9]', '', str(x)).lower())
salary_df = pd.read_csv("UCI_Earnings_By_Major_Combined_CLEAN_FIXED.csv", names=["label", "2yr", "5yr", "10yr", "major"], skiprows=1)
clubs_df = pd.read_csv("ClubData.csv", encoding='cp1252')

#Normalize Text to easily compare
def normalize(text):
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

#easily grab GPA range from data
def parse_gpa_range(gpa_range):
    if pd.isna(gpa_range) or "masked" in str(gpa_range).lower():
        return None
    try:
        low, high = map(float, gpa_range.split(" - "))
        return f"{low:.2f} - {high:.2f}"
    except:
        return None

#Group and sort majors and campuses
@app.route('/')
def index():
    grouped = (
        gpa_df.groupby("major_name")["campus"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
        .rename(columns={"campus": "campuses"})
    )
    majors = grouped.to_dict(orient="records")
    return render_template("websiteTemplate.html", majors=majors)

#Input Desired Schools and major, and get the avg GPAs, UCI salary, and clubs
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    campuses = [c.strip().upper() for c in data['campuses'].split(",")]
    major = normalize(data['major'])

    # GPA & Admit Rate Search
    gpa_matches = gpa_df[
        (gpa_df["campus"].str.upper().isin(campuses)) &
        (gpa_df["normalized_major"] == major)
    ]
 
    gpa_results = []
    for _, row in gpa_matches.iterrows():
        gpa_results.append({
            "campus": row["campus"],
            "major": row["major_name"],
            "gpa_range": parse_gpa_range(row["admit_gpa_range"]) or "Not available",
            "admit_rate": row["admit_rate"] if pd.notna(row["admit_rate"]) else "Not available"
        })

    # Salary Search
    salary_info = []
    for _, row in salary_df.iterrows():
        if "Median" not in str(row.get("label", "")):
            continue
        if normalize(row.get("major", "")) != major:
            continue
        salary_info.append({
            "label": "Median",
            "y2": row.get("2yr", "N/A"),
            "y5": row.get("5yr", "N/A"),
            "y10": row.get("10yr", "N/A")
        })

    # Club Recommendations
    user_discipline = assign_major_discipline(data['major'])

    def split_tags(tag_string):
        return [tag.strip().upper() for tag in str(tag_string).split(',') if tag.strip()]

    related_clubs = []
    general_clubs = []
    seen_names = set()

    for _, row in clubs_df.iterrows():
        tags = split_tags(row["Tags"])
        club_name = row["Club or Program"]

        if club_name in seen_names:
            continue

        has_discipline_match = any(tag in tag_to_discipline and user_discipline in tag_to_discipline[tag] for tag in tags)
        only_general = all(tag in ["GENERAL", "LEADERSHIP", "LEADERSHIP, GENERAL", "GENERAL, MULTICULTURAL"] for tag in tags)

        if has_discipline_match:
            related_clubs.append({"name": club_name,"desc": row["Purpose and Services"],"url": row["Website"] if pd.notna(row["Website"]) else ""})
            seen_names.add(club_name)
        elif only_general:
            general_clubs.append({"name": club_name, "desc": row["Purpose and Services"]})
            seen_names.add(club_name)

    related_clubs.extend(general_clubs)

    return jsonify({
        "gpa": gpa_results,
        "salary": salary_info,
        "related_clubs": related_clubs
    })

#Input a desired GPA and get majors that have high salaries based on your GPA
@app.route('/roi', methods=['POST'])
def roi():
    data = request.json
    user_gpa = float(data.get('gpa', 0))
    roi_majors = []

    uci_gpa = gpa_df[gpa_df["campus"].str.upper() == "UCI"].copy()
    uci_gpa["normalized_major"] = uci_gpa["major_name"].apply(normalize)

    seen = set()
    for _, row in salary_df.iterrows():
        if "Median" not in str(row.get("label", "")):
            continue

        norm_major = normalize(row.get("major", ""))
        if norm_major in seen:
            continue
        seen.add(norm_major)

        try:
            salary_clean = int(str(row.get("5yr", "")).replace("$", "").replace(",", ""))
        except:
            continue

        match = uci_gpa[uci_gpa["normalized_major"] == norm_major]
        if match.empty:
            continue

        for _, m in match.iterrows():
            admit_range = parse_gpa_range(m["admit_gpa_range"])
            if not admit_range:
                continue
            try:
                low, high = map(float, admit_range.split(" - "))
            except:
                continue

            if user_gpa >= low + 0.05 and salary_clean >= 50000:
                roi_majors.append({
                    "major": m["major_name"],
                    "campus": m["campus"],
                    "gpa_range": admit_range,
                    "salary": row.get("5yr", "")
                })

    roi_majors.sort(key=lambda x: int(str(x['salary']).replace('$','').replace(',','')), reverse=True)
    roi_majors = roi_majors[:5]

    return jsonify({"high_roi": roi_majors})

if __name__ == '__main__':
    app.run(debug=True)
