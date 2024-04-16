"""
This script redacts the MTurk worker and assignment IDs in the data.csv file.
Only used to share the dataset.
"""

import pandas as pd

# Define the redaction function
def redact_string(s):
    if len(s) > 8:
        return s[:4] + '*' * (len(s) - 8) + s[-4:]
    else:
        return s

# Read the CSV file into a DataFrame
df = pd.read_csv('data.csv')

# Apply the redaction function to the specified columns
df['participant.mturk_assignment_id'] = df['participant.mturk_assignment_id'].apply(redact_string)
df['participant.mturk_worker_id'] = df['participant.mturk_worker_id'].apply(redact_string)

# Write the DataFrame back to a new CSV file
df.to_csv('data.csv', index=False)