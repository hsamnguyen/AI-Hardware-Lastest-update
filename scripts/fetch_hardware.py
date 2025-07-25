import json
import os
import re
import feedparser  # For RSS
from datetime import datetime  # For date handling

# RSS sources for AI hardware (expand as needed)
RSS_SOURCES = [
    "https://nvidianews.nvidia.com/rss",  # NVIDIA hardware news
    "https://ai.googleblog.com/feeds/posts/default",  # Google AI (TPU/hardware)
    "https://arxiv.org/rss/cs.AR"  # arXiv Computer Architecture (hardware for AI)
]

# Keyword mappings for inferring fields (expand as needed)
HARDWARE_TYPES = {
    "gpu": "GPU",
    "tpu": "TPU",
    "asic": "ASIC",
    "quantum": "Quantum Chip",
    "edge": "Edge Device",
    "fpga": "FPGA"
}
SIGNIFICANCE_KEYWORDS = {
    "training": "Faster Training",
    "inference": "Improved Inference",
    "energy": "Energy Efficiency",
    "power": "Lower Power Consumption",
    "speed": "Higher Performance",
    "scalability": "Better Scalability"
}

# Function to infer hardware type and significance from text
def infer_fields(text):
    text_lower = text.lower()
    hardware_type = "Unknown"
    for key, value in HARDWARE_TYPES.items():
        if key in text_lower:
            hardware_type = value
            break
    
    significance = "Unknown"
    for key, value in SIGNIFICANCE_KEYWORDS.items():
        if key in text_lower:
            significance = value
            break
    
    return hardware_type, significance

# Function to fetch and parse from all RSS sources
def fetch_from_rss():
    new_developments = []
    for url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:  # Latest 5 per source
            if 'ai' in entry.title.lower() or 'artificial intelligence' in entry.get('description', '').lower() or 'hardware' in entry.title.lower():
                title = entry.title
                link = entry.link
                date_str = entry.published[:10] if 'published' in entry else datetime.today().strftime('%Y-%m-%d')
                description = entry.summary[:150] + '...' if 'summary' in entry else title
                company = re.search(r'(NVIDIA|Google|Intel|AMD|arXiv)', title + description, re.IGNORECASE)
                company = company.group(1) if company else "Unknown"
                hardware_type, significance = infer_fields(title + ' ' + description)
                new_developments.append({
                    "name": title,
                    "company": company,
                    "date": date_str,
                    "description": description,
                    "hardware_type": hardware_type,
                    "significance": significance,
                    "link": link
                })
    return new_developments

# Main function
def main():
    new_developments = fetch_from_rss()

    # Read old data
    data_path = 'data/hardware_data.json'
    existing = []
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            existing = json.load(f)

    # Add new if not duplicate (based on link)
    added = False
    for dev in new_developments:
        if not any(d['link'] == dev['link'] for d in existing):
            existing.append(dev)
            added = True

    # Sort by date descending and limit
    existing.sort(key=lambda x: x['date'], reverse=True)
    existing = existing[:50]

    # Write new JSON
    with open(data_path, 'w') as f:
        json.dump(existing, f, indent=2)

    if not added:
        print("No new developments, skip update.")
        return

    # Create Markdown table
    table = "| Development Name | Company | Date | Description | Hardware Type | Significance for AI | Link |\n"
    table += "|------------------|---------|------|-------------|---------------|---------------------|------|\n"
    for d in existing:
        table += f"| {d['name']} | {d['company']} | {d['date']} | {d['description']} | {d['hardware_type']} | {d['significance']} | [Link]({d['link']}) |\n"

    # Update README
    with open('README.md', 'r') as f:
        content = f.read()
    updated = re.sub(r'<!-- hardware-table-start -->.*<!-- hardware-table-end -->', 
                     f'<!-- hardware-table-start -->\n{table}<!-- hardware-table-end -->', 
                     content, flags=re.DOTALL)
    with open('README.md', 'w') as f:
        f.write(updated)

if __name__ == "__main__":
    main()