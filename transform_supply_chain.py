import pandas as pd
import numpy as np
from datetime import datetime
import os

def create_entity_mappings():
    """Create mappings for all entities (SKUs, DCs, RDCs, etc.) to unique integer IDs."""
    entity_id = 0
    entity_mappings = {}
    
    # Process order files for SKU-DC pairs
    order_files = [
        'order_jd_pre_500.csv',
        'order_jd_post_500.csv',
        'order_e2e_pre_500.csv',
        'order_e2e_post_500.csv'
    ]
    
    for file in order_files:
        try:
            df = pd.read_csv(os.path.join('E2E Supply Chain Data', file))
            if 'sku_dc_pair_index' in df.columns:
                for pair in df['sku_dc_pair_index'].unique():
                    sku_key = f"SKU_{pair}"
                    dc_key = f"DC_{pair}"
                    if sku_key not in entity_mappings:
                        entity_mappings[sku_key] = entity_id
                        entity_id += 1
                    if dc_key not in entity_mappings:
                        entity_mappings[dc_key] = entity_id
                        entity_id += 1
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
    
    # Process stock data
    try:
        stock_df = pd.read_csv(os.path.join('E2E Supply Chain Data', 'stock.csv'))
        for col in stock_df.columns:
            if col != 'item_sku_id' and col not in entity_mappings:
                entity_mappings[col] = entity_id
                entity_id += 1
    except Exception as e:
        print(f"Error processing stock.csv: {str(e)}")
    
    # Process RDC sales data
    try:
        rdc_df = pd.read_csv(os.path.join('E2E Supply Chain Data', 'rdc_sales_1320.csv'))
        for col in rdc_df.columns:
            if col != 'row' and col not in entity_mappings:
                entity_mappings[col] = entity_id
                entity_id += 1
    except Exception as e:
        print(f"Error processing rdc_sales_1320.csv: {str(e)}")
    
    return entity_mappings

def convert_timestamp(date_str):
    """Convert date string to timestamp integer."""
    try:
        dt = datetime.strptime(date_str, '%m/%d/%y')
        return int(dt.timestamp() / (24 * 3600))
    except:
        return 0

def transform_data(input_file, output_file, entity_mappings):
    """Transform supply chain data into FinDKG format."""
    try:
        # Read the input CSV file
        df = pd.read_csv(input_file)
        
        # Define relation types
        relations = {
            'order': 0,
            'inventory': 1,
            'demand': 2,
            'stock_level': 3,
            'sales': 4,
            'supply': 5
        }
        
        # Prepare output data
        output_data = []
        
        # Process based on file type
        if 'order' in input_file:
            # Process order files
            if 'sku_dc_pair_index' in df.columns:
                for _, row in df.iterrows():
                    sku_dc_pair = row['sku_dc_pair_index']
                    timestamp = convert_timestamp(row['complete_tm'])
                    
                    sku_key = f"SKU_{sku_dc_pair}"
                    dc_key = f"DC_{sku_dc_pair}"
                    
                    if sku_key in entity_mappings and dc_key in entity_mappings:
                        sku_id = entity_mappings[sku_key]
                        dc_id = entity_mappings[dc_key]
                        
                        # Create order edge (SKU -> DC)
                        output_data.append([
                            sku_id,
                            relations['order'],
                            dc_id,
                            timestamp,
                            0
                        ])
                        
                        # Create inventory edge (DC -> SKU)
                        output_data.append([
                            dc_id,
                            relations['inventory'],
                            sku_id,
                            timestamp,
                            0
                        ])
                        
                        # Create demand edge (DC -> SKU)
                        output_data.append([
                            dc_id,
                            relations['demand'],
                            sku_id,
                            timestamp,
                            0
                        ])
        
        elif 'stock.csv' in input_file:
            # Process stock data
            for _, row in df.iterrows():
                sku_id = row['item_sku_id']
                for col in df.columns:
                    if col != 'item_sku_id':
                        try:
                            timestamp = convert_timestamp(col)
                            value = float(row[col])
                            
                            # Create stock level edge
                            output_data.append([
                                entity_mappings.get(f"SKU_{sku_id}", entity_mappings.get(sku_id)),
                                relations['stock_level'],
                                entity_mappings.get(col),
                                timestamp,
                                value
                            ])
                        except (ValueError, KeyError):
                            continue
        
        elif 'rdc_sales' in input_file:
            # Process RDC sales data
            for _, row in df.iterrows():
                rdc_id = row['row']
                for col in df.columns:
                    if col != 'row':
                        try:
                            timestamp = int(col)  # RDC sales uses numeric timestamps
                            value = float(row[col])
                            
                            # Create sales edge
                            output_data.append([
                                entity_mappings.get(rdc_id),
                                relations['sales'],
                                entity_mappings.get(col),
                                timestamp,
                                value
                            ])
                        except (ValueError, KeyError):
                            continue
        
        # Write to output file
        with open(output_file, 'w') as f:
            for row in output_data:
                f.write('\t'.join(map(str, row)) + '\n')
        
        print(f"Successfully processed {input_file}")
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")

def main():
    # Create output directory if it doesn't exist
    output_dir = "transformed_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create entity mappings
    print("Creating entity mappings...")
    entity_mappings = create_entity_mappings()
    
    # Save entity mappings
    mapping_file = os.path.join(output_dir, "entity_mappings.txt")
    with open(mapping_file, 'w') as f:
        for entity, id_ in entity_mappings.items():
            f.write(f"{entity}: {id_}\n")
    
    # Process each CSV file
    input_dir = "E2E Supply Chain Data"
    for filename in os.listdir(input_dir):
        if filename.endswith('.csv'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_transformed.txt")
            
            print(f"Processing {filename}...")
            transform_data(input_file, output_file, entity_mappings)

if __name__ == "__main__":
    main() 