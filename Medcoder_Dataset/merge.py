import pandas as pd

# Load CSVs
pred_df = pd.read_csv(r"..\Medcoder_Evaluation\medcoder_stage_6.csv")
ref_df = pd.read_csv("100.csv")

# Normalize complaints
pred_df['chief_complaint'] = pred_df['chief_complaint'].str.lower().str.strip()
ref_df['Diagnosis'] = ref_df['Diagnosis'].str.lower().str.strip()

# Merge using INNER join to keep only common complaints
merged_df = pred_df.merge(ref_df, how='inner', left_on='chief_complaint', right_on='Diagnosis')

# Compare predicted and actual ICD codes
merged_df['code_match'] = merged_df['final_predicted_icd_code'] == merged_df['ICD10']

# 🔁 Remove duplicate complaints (keep the first occurrence)
merged_df = merged_df.drop_duplicates(subset='chief_complaint', keep='first')

# Save to CSV
merged_df.to_csv("comparison_common_only.csv", index=False)

print("✅ Merged and deduplicated file saved as 'merged_icd_comparison_common_only_deduped.csv'.")