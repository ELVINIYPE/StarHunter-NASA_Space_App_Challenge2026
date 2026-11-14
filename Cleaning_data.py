import pandas as pd
from bs4 import BeautifulSoup
import requests

# 1. Send an HTTP GET request to NASA's official Apollo page
url = "https://www.nasa.gov/the-apollo-program/"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    )
}

print(f"Connecting to NASA server: {url}...")
response = requests.get(url, headers=headers)
response.raise_for_status()  # Throws an error if the site blocks or fails

# 2. Parse the raw HTML using BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

# 3. Extract text elements (e.g., all headings or mission summaries)
scraped_data = []

# Find all headings (h2, h3) and paragraphs on the page
for heading in soup.find_all(["h2", "h3"]):
  title = heading.get_text(strip=True)
  # Grab the next paragraph text if available
  next_p = heading.find_next_sibling("p")
  description = next_p.get_text(strip=True) if next_p else "N/A"

  scraped_data.append({"Apollo_Topic": title, "Description": description})

# 4. Clean and structure the data using Pandas
df = pd.DataFrame(scraped_data)
df.drop_duplicates(subset=["Apollo_Topic"], inplace=True)

print("\n--- SUCCESSFULLY PULLED DATA FROM NASA.GOV ---")
print(df.head(10).to_string(index=False))

# 5. Export to CSV for your GitHub repo
output_file = "nasa_apollo_scraped_data.csv"
df.to_csv(output_file, index=False)
print(f"\n[SUCCESS] Cleaned NASA data saved to {output_file}")