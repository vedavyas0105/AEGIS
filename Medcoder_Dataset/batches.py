import pandas as pd

# Load the dataset
file_path = 'medcoder.csv'

df = pd.read_csv(file_path)

# Ask user for the number of complaints to convert
try:
    n = int(input(f'Enter the number of complaints to convert out of {len(df)} complaints: '))
except ValueError:
    print("Please enter a valid number.")
    exit()

# Limit the dataframe to the number of complaints requested
df_limited = df.head(n)

folder = 'batches'

# Batch size
batch_size = 10

# Calculate number of batches
num_batches = (len(df_limited) + batch_size - 1) // batch_size

# Split and save batches
for i in range(num_batches):
    batch_df = df_limited.iloc[i*batch_size:(i+1)*batch_size]
    batch_df.to_csv(f"{folder}/batch_{i+1}.csv", index=False)
    print(f'Saved batch_{i+1}.csv with {len(batch_df)} complaints')