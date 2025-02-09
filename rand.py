import json
import random

# Daftar kata kunci berdasarkan kategori dengan tambahan variasi
keywords = {
  "ai": [
    "AI", "machine learning", "neural networks", "deep learning", "convolutional neural networks",
    "generative adversarial networks", "AI ethics", "AI governance", "AI-powered trading",
    "automated decision-making", "AI-driven security", "natural language processing", "computer vision",
    "reinforcement learning", "explainable AI", "predictive analytics", "algorithmic bias",
    "AI in healthcare", "AI in finance", "AI in education", "AI in robotics", "AI in transportation",
    "AI in manufacturing", "AI in customer service", "edge AI", "cognitive computing", "data mining",
    "big data analytics", "AI in cybersecurity", "swarm intelligence", "federated learning",
    "speech recognition", "sentiment analysis", "human-AI interaction", "AI in agriculture",
    "autonomous vehicles", "AI in supply chain", "AI-powered chatbots", "robotic process automation",
    "virtual assistants"
  ],
  "crypto": [
    "blockchain", "smart contracts", "NFT", "DeFi", "DAO", "consensus mechanism", "public ledger",
    "crypto wallet", "Ethereum", "Bitcoin", "staking", "cryptographic algorithms", "tokenomics",
    "crypto regulations", "crypto mining", "crypto exchanges", "initial coin offerings", "stablecoins",
    "Ripple", "Litecoin", "cryptocurrency trading", "digital assets", "mining pools", "proof of work",
    "proof of stake", "hash rate", "merkle tree", "distributed ledger technology", "crypto derivatives",
    "centralized exchange", "decentralized exchange", "smart contract auditing", "layer 2 solutions",
    "blockchain interoperability", "cross-chain technology", "mining difficulty", "digital identity",
    "crypto arbitrage", "crypto lending", "yield farming", "blockchain scalability", "blockchain protocols",
    "cryptographic hash functions", "digital scarcity", "token distribution", "crypto custody solutions",
    "blockchain forks", "permissioned blockchain", "blockchain consensus", "crypto volatility"
  ],
  "fraud_detection": [
    "identify fraudulent transactions", "security concerns", "zero-knowledge proofs", "transparency",
    "game theory in crypto", "privacy coins", "oracles", "anomaly detection", "behavioral analytics",
    "fraud prevention strategies", "biometric authentication", "multi-factor authentication", "risk assessment",
    "transaction monitoring", "fraud detection algorithms", "machine learning based fraud detection",
    "real-time monitoring", "pattern recognition", "cybersecurity protocols", "anti-money laundering",
    "data mining techniques", "forensic analysis", "suspicious activity detection", "predictive modeling",
    "fraud risk scoring", "user verification", "credit card fraud", "identity theft detection",
    "insider threat detection", "automated alerts", "fraud investigation", "regulatory compliance",
    "financial anomaly detection", "behavioral biometrics", "network analysis", "cluster analysis",
    "social network analysis", "risk-based authentication", "data integrity checks", "automated fraud reporting",
    "security analytics", "behavior prediction", "digital forensics", "transaction pattern analysis",
    "fraud analytics software", "rule-based detection", "adaptive algorithms", "historical data analysis",
    "fraudulent behavior trends"
  ]
}

# Frasa tambahan untuk variasi pertanyaan dengan penambahan lebih banyak variasi
extra_phrases = [
    "in the future", "impact on economy", "challenges faced", "advantages and disadvantages",
    "real-world applications", "security concerns", "scalability issues", "role in financial markets",
    "integration with IoT", "comparison with traditional systems", "future predictions", "ethical concerns",
    "adoption by enterprises", "potential for mass adoption", "under current regulations", "and its societal impact",
    "in emerging markets", "driving innovation", "and its disruptive potential", "in the digital age",
    "in remote work settings", "and its evolution", "in competitive markets", "and its influence on policy",
    "in the context of globalization", "for sustainable development", "and emerging trends", "under economic pressures",
    "with advanced technology", "amid rapid technological change", "in high-growth sectors",
    "with regulatory challenges", "across diverse industries", "and its environmental impact",
    "amid increasing digitalization", "in relation to cybersecurity", "with significant ROI",
    "in rapidly evolving markets", "during economic downturns", "with stakeholder impact",
    "in data-driven environments", "in a post-pandemic world", "in highly competitive landscapes"
]

# Starter untuk variasi struktur pertanyaan dengan tambahan starter baru
starters = [
    "What is", "How does", "Why is", "Can you explain", "What are the benefits of",
    "How can", "What makes", "What are the features of", "How does", "What is the purpose of",
    "Why should we use", "What are the risks of", "What are the future prospects of",
    "Discuss the role of", "Analyze the impact of", "Explain the concept of", "Define", "Outline",
    "Describe", "Examine", "Investigate", "Evaluate", "Consider", "Summarize", "Compare", "Assess",
    "Illustrate", "Highlight", "Delve into", "Interpret", "Demonstrate", "Review",
    "Detail", "Clarify", "Critique", "Elucidate", "Explore", "Debate", "Justify", "Probe", "Reflect on", "Question"
]

# Konteks tambahan untuk variasi dengan penambahan context baru
contexts = [
    "in today's world", "for businesses", "for individuals", "in technology",
    "in modern society", "in academia", "in the global market", "in developing countries",
    "in the digital revolution", "in smart cities", "across industries", "in the public sector",
    "in urban areas", "in remote regions", "in competitive environments", "in high-stakes scenarios",
    "under extreme conditions", "in digital ecosystems", "in the context of AI-driven solutions",
    "with emerging digital trends", "in a globalized economy", "across technological frontiers",
    "in interconnected systems", "under market volatility", "in high-security environments"
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

# Hasilkan pertanyaan dan simpan ke file JSON
if __name__ == "__main__":
    questions_by_topic = generate_questions_per_topic(question_count_per_topic)
    with open("random_questions.json", "w") as f:
        json.dump(questions_by_topic, f, indent=2)
    print(f"{question_count_per_topic} pertanyaan acak per topik telah disimpan di random_questions.json")
