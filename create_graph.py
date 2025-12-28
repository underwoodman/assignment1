import pandas as pd
from py2neo import Graph, Node, Relationship

def create_medical_graph():
    # Connect to Neo4j - Update details as per your local setup
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
    
    # Read data
    try:
        df = pd.read_csv('disease3.csv', encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv('disease3.csv', encoding='gbk')

    # Clear existing data
    graph.run('MATCH (n) DETACH DELETE n')
    print("Old data cleared.")

    # Define Node Types corresponding to CSV columns
    # Column 0 is Disease Name
    # Columns 1-13 corresponding to properties/relations
    node_name_list = [
        "Alias", "Part", "Age", "Infection", "Insurance",
        "Department", "Checklist", "Symptom", "Complication",
        "Treatment", "Drug", "Period", "Rate", "Money"
    ]
    
    edge_name_list = [
        "HAS_ALIAS", "IS_OF_PART", "IS_OF_AGE", "IS_INFECTIOUS", "In_Insurance",
        "IS_OF_Department", "HAS_Checklist", "HAS_SYMPTOM", "HAS_Complication",
        "HAS_Treatment", "HAS_Drug", "Cure_Period", "Cure_Rate", "NEED_Money"
    ]

    print("Importing nodes and relationships...")
    
    for i in range(len(df)):
        # Create Disease Node
        disease_name = str(df.iloc[i, 0]).strip()
        node_disease = Node("Disease", name=disease_name)
        graph.merge(node_disease, "Disease", "name")  # Use merge to avoid duplicates

        # Iterate over other columns to create related nodes
        for k in range(1, 14):
            cell_value = str(df.iloc[i, k])
            if cell_value == 'nan':
                continue
                
            # Split values by space (assuming space separated based on original code)
            values = cell_value.split()
            
            target_label = node_name_list[k-1]
            relation_type = edge_name_list[k-1]
            
            for val in values:
                val = val.strip()
                if not val:
                    continue
                    
                node_target = Node(target_label, name=val)
                graph.merge(node_target, target_label, "name")
                
                # Create Relationship
                rel = Relationship(node_disease, relation_type, node_target)
                graph.merge(rel)
        
        if i % 10 == 0:
            print(f"Processed {i} diseases...")

    print("Graph construction completed successfully!")

if __name__ == "__main__":
    create_medical_graph()
