import pandas as pd

# Load the dataset from the CSV file
df = pd.read_csv('all_intersections.csv')

# Remove duplicate rows based on the 'Latitude' and 'Longitude' columns
df_no_duplicates = df.drop_duplicates(subset=['Latitude', 'Longitude'], keep='first')

# Save the deduplicated data to a new CSV file
df_no_duplicates.to_csv('all_intersections_no_duplicates.csv', index=False)

print("Duplicate rows have been removed and the cleaned data is saved as 'all_intersections_no_duplicates.csv'")