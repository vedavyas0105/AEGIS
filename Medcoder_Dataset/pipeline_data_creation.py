import pandas as pd

# Read the diagnoses file
diagnoses_df = pd.read_csv("testing.csv")
diagnoses = diagnoses_df["Diagnosis"].tolist()

# Create one note per diagnosis
notes = [f"note_{i:03d}" for i in range(11, 11 + len(diagnoses))]

df = pd.DataFrame({
    "Document ID": notes,
    "patient_sex": "Unknown",
    "medical_record_text": diagnoses
})

df.to_csv('medcoder.csv', index=False)

print("Done")