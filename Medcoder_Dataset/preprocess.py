import pandas as pd

df = pd.read_csv(r'original_dataset\diagnosis.csv')

df_part = df[['Diagnosis', 'ICD10']]

df_part.to_csv('testing.csv', index=False)

print("Done")