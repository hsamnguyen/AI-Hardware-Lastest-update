import json
import os
import re
import feedparser  # For RSS
from datetime import datetime

# RSS sources (unchanged)
RSS_SOURCES = [
    "https://nvidianews.nvidia.com/rss",
    "https://ai.googleblog.com/feeds/posts/default",
    "https://arxiv.org/rss/cs.AR",
    "https://www.wired.com/tag/artificial-intelligence/rss",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/"
]

# Updated keywords
HARDWARE_TYPES = {
    "gpu": "GPU",
    "tpu": "TPU",
    "asic": "ASIC",
    "quantum": "Quantum Chip",
    "edge": "Edge Device",
    "fpga": "FPGA",
    "chip": "Chip/Processor",
    "accelerator": "AI Accelerator",
    "semiconductor": "Semiconductor",
    "blackwell": "GPU Accelerator"
}
SIGNIFICANCE_KEYWORDS = {
    "training": "Faster Training",
    "inference": "Improved Inference",
    "energy": "Energy Efficiency",
    "power": "Lower Power Consumption",
    "speed": "Higher Performance",
    "scalability": "Better Scalability",
    "efficiency": "Energy Efficiency",
    "computing": "Enhanced Computing",
    "mi300": "High Performance AI"
}

# Function to infer fields
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

# Function to fetch from RSS
def fetch_from_rss():
    new_developments = []
    min_date = datetime(2025, 1, 1)  # Filter for 2025+
    for url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries:  # Fetch all, no limit
            title_lower = entry.title.lower()
            desc_lower = entry.get('description', entry.get('summary', '')).lower()
            if any(term in title_lower or term in desc_lower for term in ['ai', 'artificial intelligence', 'hardware', 'chip', 'processor', 'accelerator', 'quantum', 'edge device', 'gpu', 'tpu', 'semiconductor', 'blackwell', 'mi300']):
                title = entry.title
                link = entry.link
                date_str = entry.published[:10] if 'published' in entry else datetime.today().strftime('%Y-%m-%d')
                try:
                    entry_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if entry_date < min_date:
                        continue  # Skip old
                except ValueError:
                    continue
                description = entry.summary[:150] + '...' if 'summary' in entry else (entry.description[:150] + '...' if 'description' in entry else title)
                company_match = re.search(r'(NVIDIA|Google|Intel|AMD|WIRED|TechCrunch|VentureBeat|arXiv|HP|Microsoft)', title + description, re.IGNORECASE)
                company = company_match.group(1) if company_match else "Unknown"
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

    data_path = 'data/hardware_data.json'
    existing = []
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            existing = json.load(f)

    added = False
    for dev in new_developments:
        if not any(d['link'] == dev['link'] or (d['name'] == dev['name'] and d['date'] == dev['date']) for d in existing):
            existing.append(dev)
            added = True

    existing.sort(key=lambda x: x['date'], reverse=True)
    existing = existing[:50]

    with open(data_path, 'w') as f:
        json.dump(existing, f, indent=2)

    if not added:
        print("No new developments, skip update.")
        return

    table = "| Development Name | Company | Date | Description | Hardware Type | Significance for AI | Link |\n"
    table += "|------------------|---------|------|-------------|---------------|---------------------|------|\n"
    for d in existing:
        table += f"| {d['name']} | {d['company']} | {d['date']} | {d['description']} | {d['hardware_type']} | {d['significance']} | [Link]({d['link']}) |\n"

    with open('README.md', 'r') as f:
        content = f.read()
    updated = re.sub(r'<!-- hardware-table-start -->.*<!-- hardware-table-end -->', 
                     f'<!-- hardware-table-start -->\n{table}<!-- hardware-table-end -->', 
                     content, flags=re.DOTALL)
    with open('README.md', 'w') as f:
        f.write(updated)

if __name__ == "__main__":
    main()