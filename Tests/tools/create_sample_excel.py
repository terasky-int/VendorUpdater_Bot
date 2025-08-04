"""
Create sample Excel file for schema enrichment testing
"""

import pandas as pd
import os

# Sample vendor data
data = {
    'id': [1, 2, 3, 4, 5],
    'name': ['HashiCorp', 'UPWind', 'Broadcom', 'AWS', 'Azure'],
    'description': [
        'Infrastructure automation and security tools',
        'Cloud security platform provider', 
        'Enterprise software and infrastructure solutions',
        'Public cloud infrastructure services',
        'Public cloud infrastructure services'
    ],
    'associated_domains': ['', '', '', '', ''],
    'aliases': ['', '', '', '', ''],
    'source': ['core-tskb', 'core-tskb', 'core-tskb', 'core-tskb', 'core-tskb']
}

df = pd.DataFrame(data)
output_path = os.path.join(os.path.dirname(__file__), 'sample_vendors.xlsx')
df.to_excel(output_path, index=False)
print(f"Created sample Excel file: {output_path}")