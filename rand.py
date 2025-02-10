import json
import random

# Daftar kata kunci per kategori dengan variasi
keywords = {
    "ai": [
        "AI", "machine learning", "neural networks", "deep learning", "convolutional neural networks",
        "recurrent neural networks", "generative adversarial networks", "reinforcement learning", "transfer learning",
        "explainable AI", "cognitive computing", "edge AI", "speech recognition", "computer vision", "natural language processing",
        "algorithmic bias", "predictive analytics", "autonomous systems", "smart automation", "data science", "big data analytics",
        "quantum computing in AI", "AI ethics", "AI governance", "autonomous vehicles", "robotics", "swarm intelligence",
        "federated learning", "self-supervised learning", "semi-supervised learning", "AI in healthcare", "AI in finance",
        "AI in education", "AI in manufacturing", "AI in agriculture", "AI in cybersecurity", "AI in transportation",
        "AI-powered chatbots", "virtual assistants", "emotion recognition", "pattern recognition", "data mining",
        "knowledge graphs", "AI in gaming", "augmented intelligence", "adaptive algorithms", "edge computing",
        "multi-agent systems", "unsupervised learning", "AI in retail", "AI in logistics", "AI-powered recommendation systems",
        "neural architecture search"
    ],
    "crypto": [
        "blockchain", "smart contracts", "NFT", "DeFi", "DAO", "cryptocurrency", "Bitcoin", "Ethereum", "Ripple",
        "Litecoin", "stablecoins", "crypto wallet", "cryptographic algorithms", "public ledger", "mining", "crypto exchanges",
        "staking", "proof of work", "proof of stake", "consensus mechanism", "distributed ledger technology", "initial coin offering",
        "tokenomics", "crypto regulation", "hash rate", "block size", "block time", "decentralized finance", "layer 2 solutions",
        "scalability", "sidechains", "forks", "merkle tree", "crypto arbitrage", "digital identity", "smart contract auditing",
        "crypto lending", "yield farming", "DeFi protocols", "token burn", "crypto derivatives", "decentralized applications",
        "privacy coins", "Zcash", "Monero", "blockchain interoperability", "non-fungible token", "crypto custody", "gas fees",
        "block explorer", "proof of authority", "staking pools", "crypto index funds", "sharding", "lightning network",
        "oracles", "crypto taxation", "blockchain consensus", "crypto market cap", "digital scarcity", "block reward", "node operation"
    ],
    "fraud_detection": [
        "fraud detection", "identify fraudulent transactions", "anomaly detection", "behavioral analytics", "risk assessment",
        "transaction monitoring", "fraud detection algorithms", "real-time monitoring", "pattern recognition", "biometric authentication",
        "multi-factor authentication", "fraud prevention strategies", "zero-knowledge proofs", "regulatory compliance", "cybersecurity protocols",
        "forensic analysis", "data mining techniques", "suspicious activity detection", "predictive modeling", "fraud risk scoring",
        "user verification", "credit card fraud", "identity theft detection", "insider threat detection", "automated alerts",
        "fraud investigation", "machine learning for fraud", "adaptive algorithms", "historical data analysis", "fraudulent behavior trends",
        "transaction pattern analysis", "network analysis", "cluster analysis", "social network analysis", "risk-based authentication",
        "digital forensics", "security analytics", "anomaly scoring", "heuristic analysis", "fraudulent claim detection", "insurance fraud",
        "financial anomaly detection", "emergency fraud protocols", "rule-based detection", "fraud signal processing", "data integrity checks",
        "automated fraud reporting", "behavior prediction", "behavioral biometrics", "AI in fraud detection", "unsupervised fraud detection",
        "fraud lifecycle management", "fraud simulation", "cyber fraud analysis", "transaction anomaly analytics", "cross-channel fraud detection"
    ]
}

# Frasa tambahan untuk variasi pertanyaan
extra_phrases = [
    "in the future", "impact on economy", "challenges faced", "advantages and disadvantages", "real-world applications",
    "security concerns", "scalability issues", "role in financial markets", "integration with IoT", "comparison with traditional systems",
    "future predictions", "ethical concerns", "adoption by enterprises", "potential for mass adoption", "under current regulations",
    "and its societal impact", "in emerging markets", "driving innovation", "and its disruptive potential", "in the digital age",
    "in remote work settings", "and its evolution", "in competitive markets", "and its influence on policy", "in the context of globalization",
    "for sustainable development", "and emerging trends", "under economic pressures", "with advanced technology", "amid rapid technological change",
    "in high-growth sectors", "with regulatory challenges", "across diverse industries", "and its environmental impact", "amid increasing digitalization",
    "in relation to cybersecurity", "with significant ROI", "in rapidly evolving markets", "during economic downturns", "with stakeholder impact",
    "in data-driven environments", "in a post-pandemic world", "in highly competitive landscapes", "with innovative solutions",
    "in multi-cloud environments", "and its long-term implications", "considering privacy laws", "under geopolitical pressures",
    "in the age of digital transformation", "in the context of disruptive technologies", "in evolving regulatory landscapes",
    "across global markets", "with a focus on sustainability", "amid market disruptions", "in the sphere of digital transformation",
    "with evolving consumer demands"
]

# Starter untuk struktur pertanyaan
starters = [
    "What is", "How does", "Why is", "Can you explain", "What are the benefits of", "How can", "What makes",
    "What are the features of", "How does", "What is the purpose of", "Why should we use", "What are the risks of",
    "What are the future prospects of", "Discuss the role of", "Analyze the impact of", "Explain the concept of", "Define",
    "Outline", "Describe", "Examine", "Investigate", "Evaluate", "Consider", "Summarize", "Compare", "Assess", "Illustrate",
    "Highlight", "Delve into", "Interpret", "Demonstrate", "Review", "Detail", "Clarify", "Critique", "Elucidate", "Explore",
    "Debate", "Justify", "Probe", "Reflect on", "Question", "Unpack", "Deconstruct", "Scrutinize", "Audit", "Monitor", "Chart",
    "Map out", "Frame", "Identify", "Showcase", "Dissect", "Unravel", "Catalog", "Distill", "Enumerate", "Trace",
    "Outline the evolution of"
]

# Konteks tambahan untuk variasi pertanyaan
contexts = [
    "in today's world", "for businesses", "for individuals", "in technology", "in modern society", "in academia",
    "in the global market", "in developing countries", "in the digital revolution", "in smart cities", "across industries",
    "in the public sector", "in urban areas", "in remote regions", "in competitive environments", "in high-stakes scenarios",
    "under extreme conditions", "in digital ecosystems", "in the context of AI-driven solutions", "with emerging digital trends",
    "in a globalized economy", "across technological frontiers", "in interconnected systems", "under market volatility",
    "in high-security environments", "on a local scale", "in emerging technologies", "within regulatory frameworks",
    "in disruptive innovation", "in digital marketplaces", "amid evolving consumer behaviors", "in economic downturns",
    "in volatile markets", "under changing political climates", "in decentralized networks", "across national borders",
    "in complex systems", "within multinational corporations", "in hybrid work environments", "in post-pandemic recovery",
    "within sustainable frameworks", "in dynamic business environments", "in tech startups", "in global trade",
    "across public and private sectors", "in real-time applications", "in advanced research labs", "in next-generation networks",
    "in collaborative platforms"
]

# Fungsi untuk menghasilkan pertanyaan acak berdasarkan topik
def generate_random_question(topic):
    random_starter = random.choice(starters)
    random_keyword = random.choice(keywords[topic])
    random_extra = random.choice(extra_phrases)
    random_context = random.choice(contexts)
    return f"{random_starter} {random_keyword} {random_extra} {random_context}?"

# Fungsi untuk menghasilkan sejumlah pertanyaan acak per topik
def generate_questions_per_topic(count):
    questions = {
        "ai": [generate_random_question("ai") for _ in range(count)],
        "crypto": [generate_random_question("crypto") for _ in range(count)],
        "fraud_detection": [generate_random_question("fraud_detection") for _ in range(count)]
    }
    return questions

# Jumlah pertanyaan yang ingin dihasilkan per topik
question_count_per_topic = 500

if __name__ == "__main__":
    questions_by_topic = generate_questions_per_topic(question_count_per_topic)
    with open("random_questions.json", "w") as f:
        json.dump(questions_by_topic, f, indent=2)
    print(f"{question_count_per_topic} pertanyaan acak per topik telah disimpan di random_questions.json")
