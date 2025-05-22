def sum_chart_counts(stats_text):
    # Initialize total count
    total_count = 0
    
    # Split the text by lines and process each line
    lines = stats_text.strip().split('\n')
    
    # Skip the header lines
    data_lines = lines[2:]  # Skip the first two lines
    
    # Process each line containing chart data
    for line in data_lines:
        # Extract the count from the line
        if '(' in line:  # Make sure we're looking at a data line
            # Split by whitespace and extract the count
            parts = line.split()
            count = int(parts[1])  # The count should be the second item
            total_count += count
    
    return total_count

# The provided statistics text
stats_text = """Output Mark Type Statistics:
------------------------------
bar              4732 ( 19.55%)
boxplot          2949 ( 12.19%)
line             3397 ( 14.04%)
pie              6896 ( 28.49%)
point            1910 (  7.89%)
rect             4317 ( 17.84%)"""

# Calculate the total
total = sum_chart_counts(stats_text)
print(f"Total chart count: {total}")