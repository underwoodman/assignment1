import pandas as pd
from py2neo import Graph

class MedicalQASystem:
    def __init__(self, uri, auth):
        self.graph = Graph(uri, auth=auth)
        self.load_entities()
        
    def load_entities(self):
        # Load disease names for entity recognition
        try:
            df = pd.read_csv('disease3.csv', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv('disease3.csv', encoding='gbk')
        self.disease_names = set(df.iloc[:, 0].astype(str).tolist())
        print(f"Loaded {len(self.disease_names)} disease entities.")

    def get_intent_and_entity(self, question):
        found_entity = None
        for disease in self.disease_names:
            if disease in question:
                found_entity = disease
                break # Simple matching, take first found
        
        intent = None
        
        # Keyword mappings from reference logic
        intent_keywords = {
            "HAS_SYMPTOM": ['症状', '表象', '现象', '症候', '表现'],
            "HAS_Symptom_inv": ['可能', '导致', '引起', '为什么', '怎么回事', '因为', '咋回事'], # Inverse: Symptom -> Disease
            "HAS_Complication": ['并发症', '并发', '一起发生', '一同发生', '伴随'],
            "HAS_Drug": ['药', '药品', '用药', '胶囊', '口服液', '药片'],
            "HAS_Treatment": ['治疗', '治法', '疗法', '怎么治', '怎么办'],
            "NEED_Money": ['钱', '费用', '多少钱', '价格', '花费'],
            "Cure_Period": ['周期', '时间', '多久', '多长时间', '天数']
        }
        
        for key, keywords in intent_keywords.items():
            for kw in keywords:
                if kw in question:
                    intent = key
                    break
            if intent:
                break
                
        return intent, found_entity

    def generate_cypher(self, intent, entity):
        if not entity:
            return None, "未识别到疾病名称"
            
        cypher = ""
        if intent == "HAS_SYMPTOM":
            cypher = f"MATCH (d:Disease {{name: '{entity}'}})-[:HAS_SYMPTOM]->(n) RETURN n.name"
        elif intent == "HAS_Complication":
            cypher = f"MATCH (d:Disease {{name: '{entity}'}})-[:HAS_Complication]->(n) RETURN n.name"
        elif intent == "HAS_Drug":
            cypher = f"MATCH (d:Disease {{name: '{entity}'}})-[:HAS_Drug]->(n) RETURN n.name"
        elif intent == "HAS_Treatment":
            cypher = f"MATCH (d:Disease {{name: '{entity}'}})-[:HAS_Treatment]->(n) RETURN n.name"
        elif intent == "NEED_Money":
            cypher = f"MATCH (d:Disease {{name: '{entity}'}})-[:NEED_Money]->(n) RETURN n.name"
        elif intent == "Cure_Period":
            cypher = f"MATCH (d:Disease {{name: '{entity}'}})-[:Cure_Period]->(n) RETURN n.name"
        # Add more mappings as needed
        else:
            return None, "未识别到具体的意图 (如: 症状, 药品, 并发症等)"
            
        return cypher, None

    def query(self, question):
        intent, entity = self.get_intent_and_entity(question)
        
        if not entity:
             # Try inverse symptom lookup logic from reference
             # Reference used specific keywords to trigger inverse lookup
             # Simplified here for clarity
             return "抱歉，我没有在问题中找到已知的疾病名称。"
             
        if not intent:
            return f"识别到疾病 '{entity}'，但请具体询问其症状、药方或并发症等。"
            
        cypher, error = self.generate_cypher(intent, entity)
        if error:
            return error
            
        print(f"Generated Cypher: {cypher}")
        try:
            results = self.graph.run(cypher).data()
            if not results:
                return "未找到相关信息。"
            
            # Format answers
            answers = [list(r.values())[0] for r in results]
            return f"关于 {entity} 的查询结果: " + ", ".join(answers)
        except Exception as e:
            return f"查询出错: {str(e)}"

if __name__ == "__main__":
    # Initialize system
    qa = MedicalQASystem("bolt://localhost:7687", ("neo4j", "password"))
    
    print("=== 医疗知识图谱问答系统 (输入 'exit' 退出) ===")
    while True:
        q = input("\n请输入问题 (例如: 感冒吃什么药?): ")
        if q == "exit":
            break
        answer = qa.query(q)
        print("回答:", answer)
