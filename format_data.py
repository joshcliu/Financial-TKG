import os
import pandas as pd
import numpy as np

# Create output directory if it doesn't exist
os.makedirs('SupplyChain', exist_ok=True)

# Read the data files
pre_500_data = pd.read_csv('transformed_data/order_jd_pre_500_transformed.txt', 
                          sep='\t', 
                          header=None,
                          names=['src', 'rel', 'dst', 'timestamp', 'meta'])

post_500_data = pd.read_csv('transformed_data/order_jd_post_500_transformed.txt',
                           sep='\t',
                           header=None,
                           names=['src', 'rel', 'dst', 'timestamp', 'meta'])

e2e_data = pd.read_csv('transformed_data/order_e2e_post_500_transformed.txt',
                       sep='\t',
                       header=None,
                       names=['src', 'rel', 'dst', 'timestamp', 'meta'])

# Combine all data
all_data = pd.concat([pre_500_data, post_500_data, e2e_data])

# Get unique entities and relations
unique_entities = np.unique(np.concatenate([all_data['src'].unique(), all_data['dst'].unique()]))
unique_relations = all_data['rel'].unique()

# Write entity2id.txt
with open('SupplyChain/entity2id.txt', 'w') as f:
    for i, entity in enumerate(unique_entities):
        f.write(f"{entity}\t{i}\n")

# Write relation2id.txt
with open('SupplyChain/relation2id.txt', 'w') as f:
    for i, relation in enumerate(unique_relations):
        f.write(f"{relation}\t{i}\n")

# Write stat.txt
with open('SupplyChain/stat.txt', 'w') as f:
    f.write(f"{len(unique_entities)}\t{len(unique_relations)}\n")

# Sort by timestamp
all_data = all_data.sort_values('timestamp')

# Split data into train (80%), valid (10%), test (10%)
train_size = int(len(all_data) * 0.8)
valid_size = int(len(all_data) * 0.1)

train_data = all_data[:train_size]
valid_data = all_data[train_size:train_size+valid_size]
test_data = all_data[train_size+valid_size:]

# Write train.txt
train_data.to_csv('SupplyChain/train.txt', sep='\t', header=False, index=False)

# Write valid.txt
valid_data.to_csv('SupplyChain/valid.txt', sep='\t', header=False, index=False)

# Write test.txt
test_data.to_csv('SupplyChain/test.txt', sep='\t', header=False, index=False)

print("Data formatting completed!")
print(f"Number of entities: {len(unique_entities)}")
print(f"Number of relations: {len(unique_relations)}")
print(f"Number of training samples: {len(train_data)}")
print(f"Number of validation samples: {len(valid_data)}")
print(f"Number of test samples: {len(test_data)}") 