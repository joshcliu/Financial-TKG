import torch
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from pathlib import Path
import random

def generate_entity_name(entity_id, entity_types=None):
    """Generate a meaningful name for an entity based on its ID and type"""
    # Base name for the entity
    base_name = f"Entity_{entity_id}"
    
    # If we have entity types, use them to create more meaningful names
    if entity_types and entity_id in entity_types:
        entity_type = entity_types[entity_id]
        base_name = f"{entity_type}_{entity_id}"
    
    return base_name

def load_entities(file_path):
    """Load entity mappings from the entity2id.txt file and generate meaningful names"""
    entities = {}
    entity_types = {}
    
    # First pass: load basic entity information
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                entity_id = int(parts[1])
                entities[entity_id] = generate_entity_name(entity_id)
                
                # If entity type is available (format: name, id, type)
                if len(parts) >= 3:
                    entity_types[entity_id] = parts[2]
    
    # Second pass: update names with types if available
    if entity_types:
        for entity_id in entities:
            entities[entity_id] = generate_entity_name(entity_id, entity_types)
    
    return entities, entity_types

def load_relations(file_path):
    """Load relation mappings from the relation2id.txt file"""
    relations = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                relation_name = parts[0]
                relation_id = int(parts[1])
                relations[relation_id] = relation_name
    return relations

def load_triples(file_path, entity_map, relation_map, limit=None):
    """Load triples (head, relation, tail, timestamp) from the test.txt file"""
    triples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
                
            parts = line.strip().split('\t')
            if len(parts) >= 4:  # Now expecting at least 4 parts including timestamp
                head_id = int(parts[0])
                relation_id = int(parts[1])
                tail_id = int(parts[2])
                timestamp = int(parts[3])
                
                # Skip if any ID is not in the mappings
                if head_id not in entity_map or tail_id not in entity_map or relation_id not in relation_map:
                    continue
                
                # Map IDs to names
                head_name = entity_map.get(head_id)
                relation_name = relation_map.get(relation_id)
                tail_name = entity_map.get(tail_id)
                
                triples.append((head_name, relation_name, tail_name, timestamp))
    return triples

def analyze_entity_patterns(triples):
    """Analyze patterns in the triples to generate more meaningful entity names"""
    # Count incoming and outgoing edges for each entity
    in_edges = {}
    out_edges = {}
    relation_counts = {}
    
    for head, relation, tail, _ in triples:
        # Count outgoing edges
        if head not in out_edges:
            out_edges[head] = set()
        out_edges[head].add(relation)
        
        # Count incoming edges
        if tail not in in_edges:
            in_edges[tail] = set()
        in_edges[tail].add(relation)
        
        # Count relation frequencies
        if relation not in relation_counts:
            relation_counts[relation] = 0
        relation_counts[relation] += 1
    
    # Generate role-based names
    entity_roles = {}
    for entity in set(list(in_edges.keys()) + list(out_edges.keys())):
        in_rels = in_edges.get(entity, set())
        out_rels = out_edges.get(entity, set())
        
        # Determine entity role based on relation patterns
        if len(in_rels) > len(out_rels):
            role = "Consumer"
        elif len(out_rels) > len(in_rels):
            role = "Provider"
        else:
            role = "Node"
        
        entity_roles[entity] = role
    
    return entity_roles

def create_temporal_knowledge_graph(triples):
    """Create a NetworkX graph from triples with temporal information"""
    G = nx.DiGraph()
    
    # Analyze entity patterns to generate meaningful names
    entity_roles = analyze_entity_patterns(triples)
    
    # Add edges with relationship and temporal attributes
    for head, relation, tail, timestamp in triples:
        # Add role information to node attributes
        if head not in G:
            G.add_node(head, role=entity_roles.get(head, "Unknown"))
        if tail not in G:
            G.add_node(tail, role=entity_roles.get(tail, "Unknown"))
            
        G.add_edge(head, tail, relationship=relation, timestamp=timestamp)
    
    # Print unique relationship types and temporal range
    relationship_types = set(d['relationship'] for u, v, d in G.edges(data=True))
    timestamps = [d['timestamp'] for u, v, d in G.edges(data=True)]
    min_time = min(timestamps)
    max_time = max(timestamps)
    
    print(f"Available relationship types in the graph ({len(relationship_types)}):")
    for rel in sorted(relationship_types):
        print(f"- {rel}")
    
    print(f"\nTemporal range: {min_time} to {max_time}")
    
    # Count edges per relationship type
    rel_counts = {}
    for u, v, d in G.edges(data=True):
        rel = d['relationship']
        rel_counts[rel] = rel_counts.get(rel, 0) + 1
    
    print("\nNumber of edges per relationship type:")
    for rel, count in sorted(rel_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{rel}: {count} edges")
    
    return G

def create_temporal_subgraph(G, start_time, end_time):
    """Create a subgraph containing only edges within the specified time range"""
    temporal_edges = [(u, v) for u, v, d in G.edges(data=True) 
                     if start_time <= d['timestamp'] <= end_time]
    return G.edge_subgraph(temporal_edges).copy()

def plot_temporal_knowledge_graph(G, title, filename, pos=None, time_range=None):
    """Plot a knowledge graph with edge labels showing the specific relations and temporal information"""
    plt.figure(figsize=(20, 16))
    
    if pos is None:
        # Use a better layout algorithm for larger graphs
        if len(G) < 50:
            pos = nx.spring_layout(G, seed=42, k=0.5)
        else:
            pos = nx.kamada_kawai_layout(G)
    
    # Calculate node sizes based on degree centrality
    node_sizes = [300 + 100 * G.degree(node) for node in G.nodes()]
    
    # Get node colors based on roles
    node_colors = []
    for node in G.nodes():
        role = G.nodes[node].get('role', 'Unknown')
        if role == 'Provider':
            node_colors.append('lightgreen')
        elif role == 'Consumer':
            node_colors.append('lightcoral')
        else:
            node_colors.append('lightblue')
    
    # Draw nodes with role-based colors
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, alpha=0.8, 
                          node_color=node_colors, edgecolors='black')
    
    # Draw edges with curves to avoid overlap
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7, 
                          arrows=True, arrowsize=15, arrowstyle='-|>', connectionstyle='arc3,rad=0.1')
    
    # Draw labels with smaller font and wrapping for long names
    node_labels = {}
    for node in G.nodes():
        role = G.nodes[node].get('role', 'Unknown')
        # Wrap long node names
        if len(str(node)) > 20:
            node_labels[node] = '\n'.join([str(node)[:20], str(node)[20:40]])
        else:
            node_labels[node] = f"{node}\n({role})"
    
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10, 
                           font_family='sans-serif', font_weight='bold')
    
    # Create edge labels with the specific relation names and timestamps
    edge_labels = {}
    for u, v, data in G.edges(data=True):
        # Use abbreviated relation names if too long
        relation = data['relationship']
        timestamp = data['timestamp']
        if len(str(relation)) > 15:
            relation = str(relation)[:12] + '...'
        edge_labels[(u, v)] = f"{relation}\n(t={timestamp})"
    
    # Draw edge labels with the relation names and timestamps
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, alpha=0.8)
    
    # Add time range to title if provided
    if time_range:
        title = f"{title}\nTime Range: {time_range[0]} to {time_range[1]}"
    
    plt.title(title, fontsize=20)
    plt.axis('off')
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(f"visualizations/{filename}.png", dpi=300, bbox_inches='tight')
    plt.show()

def main():
    # Create results directory if it doesn't exist
    Path("visualizations").mkdir(exist_ok=True)
    
    # Load entity and relation mappings
    print("Loading entity and relation mappings...")
    entity_map, entity_types = load_entities("SupplyChain/entity2id.txt")
    relation_map = load_relations("SupplyChain/relation2id.txt")
    
    print(f"Loaded {len(entity_map)} entities and {len(relation_map)} relations")
    
    # Load triples from test.txt (limit to first 5000 for efficiency)
    print("Loading triples from test.txt...")
    triples = load_triples("SupplyChain/test.txt", entity_map, relation_map, limit=5000)
    
    print(f"Loaded {len(triples)} triples")
    
    # Create temporal knowledge graph
    print("Creating temporal knowledge graph...")
    G = create_temporal_knowledge_graph(triples)
    
    print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Get temporal range
    timestamps = [d['timestamp'] for u, v, d in G.edges(data=True)]
    min_time = min(timestamps)
    max_time = max(timestamps)
    
    # Create a visualization of the entire temporal graph
    print("\nCreating visualization of the temporal graph...")
    plot_temporal_knowledge_graph(
        G,
        "Temporal Knowledge Graph",
        "temporal_kg",
        time_range=(min_time, max_time)
    )

if __name__ == "__main__":
    main() 