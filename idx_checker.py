import pandas as pd

# Load your CSV file (replace 'solution.csv' with the actual file path)
df = pd.read_csv('solution.csv', header=None, names=['col1', 'col2'])

# Function to return the indices of rows where a particular value occurs
def get_row_indices(group):
    return group.index.tolist()

# Group by 'col1', then for each 'col1' group, group by 'col2' and collect row indices
result = df.groupby('col1').apply(lambda x: x.groupby('col2').apply(get_row_indices)).reset_index()

# Rename columns for better clarity
result.columns = ['col1', 'col2_value', 'row_indices']

# Display the result
print(result)

# Optionally, save the result to a new CSV file
result.to_csv('row_indices.csv', index=False)
