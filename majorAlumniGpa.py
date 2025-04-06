import pandas as pd
import re

from data_processing import tag_to_discipline, assign_major_discipline

# Helpers for the actual program
#Make entered in major easily comparable
def normalize(text):
    """Normalize a string: lowercase, remove non-alphanumerics."""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

#Format the GPA range from Combined_UC_Majors dataset
def parse_gpa_range(gpa_range):
    if pd.isna(gpa_range) or "masked" in str(gpa_range).lower():
        return None
    try:
        low, high = map(float, gpa_range.split(" - "))
        return f"{low:.2f} - {high:.2f}"
    except:
        return None
    
#Determine the major's discipline based on the tag mapping
def get_major_discipline(major_str):
    return assign_major_discipline(major_str)


# Load Files
gpa_df = pd.read_csv("Combined_UC_Majors_UTF8.csv")
salary_df = pd.read_csv("UCI_Earnings_By_Major_Combined_CLEAN_FIXED.csv", header=None)
clubs_df = pd.read_csv("ClubData.csv")

# User Input
desired_schools = input("Enter the UC campuses you're interested in (comma-separated, like UCLA,UCI,UCB): ")
desired_major = input("Enter the major you plan to apply to: ")

school_list = [s.strip().upper() for s in desired_schools.split(",")]
major_query = normalize(desired_major)

# GPA Search
gpa_df["normalized_major"] = gpa_df["major_name"].apply(normalize)

matches = gpa_df[
    (gpa_df["campus"].str.upper().isin(school_list)) &
    (gpa_df["normalized_major"] == major_query)
]

if matches.empty:
    print("\nNo GPA data found. Try checking the spelling or try a related major.")
else:
    print("\nAdmit GPA Ranges for Your Selected Majors and Campuses:")
    for _, row in matches.iterrows():
        campus = row["campus"]
        major = row["major_name"]
        gpa_range = parse_gpa_range(row["admit_gpa_range"])
        print(f"\n{campus}")
        print(f"   Major: {major}")
        print(f"   Admit GPA Range: {gpa_range or 'Not available'}")

# Salary Search (UCI Only)
print("\nUCI Salary Data for This Major (if available):")

found = False
for i in range(len(salary_df)):
    row = salary_df.iloc[i]
    major_raw = str(row.iloc[-1])
    
    if normalize(major_raw) == major_query:
        label = str(row.iloc[0])
        y2 = str(row.iloc[1]) if len(row) > 1 else ""
        y5 = str(row.iloc[2]) if len(row) > 2 else ""
        y10 = str(row.iloc[3]) if len(row) > 3 else ""

        if "Median Annual Earnings" in label:
            print(f"   • Median Salary (2 years): {y2}")
            print(f"   • Median Salary (5 years): {y5}")
            print(f"   • Median Salary (10 years): {y10}")
            found = True
        elif "25th" in label:
            print(f"   • 25th Percentile (2 years): {y2}")
            print(f"   • 25th Percentile (5 years): {y5}")
            print(f"   • 25th Percentile (10 years): {y10}")
            found = True
        elif "75th" in label:
            print(f"   • 75th Percentile (2 years): {y2}")
            print(f"   • 75th Percentile (5 years): {y5}")
            print(f"   • 75th Percentile (10 years): {y10}")
            found = True

if not found:
    print("   Not available.")
    
# determine user's discipline
user_discipline = assign_major_discipline(desired_major)


# associate majors from the Combined_UC_Majors data with discipline
# ensure gpa_df has the discipline column before proceeding
# if "discipline" not in gpa_df.columns:
#     gpa_df["discipline"] = gpa_df["major_name"].apply(assign_major_discipline)

# # build unique sorted list of majors in discipline
# related_majors = sorted(gpa_df[gpa_df["discipline"] == user_discipline]["major_name"].unique())
# print("Related Majors in this Discipline:")
# print(", ".join(related_majors))
# print()

# helper to split tags in tags column
def split_tags(tag_string):
    return [tag.strip().upper() for tag in tag_string.split(',') if tag.strip()]

# filter and display leadership/general extracurriculars
extra_tags = ["LEADERSHIP, GENERAL", "GENERAL, MULTICULTURAL", "LEADERSHIP", "GENERAL"]  # Tags to identify leadership/general extracurriculars


extra_clubs = []
extra_club_names = set()
for idx, row in clubs_df.iterrows():
    # check if the entire extra tag string is found within the row's Tags
    for etag in extra_tags:
        if etag in row["Tags"]:
            club_name = row["Club or Program"]
            #avoid duplicates in the extra clubs list
            if club_name not in extra_club_names:
                extra_clubs.append(row)
                extra_club_names.add(club_name)
            break

# filter clubs based on the user's major's discipline
related_clubs = []
related_club_names = set()

for idx, row in clubs_df.iterrows():
    club_tags = split_tags(row["Tags"])  # now returns UPPERCASE tags
    for tag in club_tags:
        if tag in tag_to_discipline and tag_to_discipline[tag] == user_discipline:
            club_name = row["Club or Program"]
            if club_name not in related_club_names and club_name not in extra_club_names:  # Ensure it is not already in the extra clubs list
                related_clubs.append(row)
                related_club_names.add(club_name)
            break

#prints clubs related to the user's major's discipline and extras
print("\nClubs Related to Your Major:")
if related_clubs != []:
    for club in related_clubs:
        print(f" - {club['Club or Program']}: {club['Purpose and Services']}")
else:
    print("No clubs found related to your major's discipline.")

print("\nLeadership, General, and Cultural Extracurriculars:")
if extra_clubs:
    for club in extra_clubs:
        print(f" - {club['Club or Program']}: {club['Purpose and Services']})")
else:
    print("No leadership/general extracurriculars found.")

