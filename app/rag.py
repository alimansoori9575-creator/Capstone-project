import os
import re
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Resolve absolute paths based on the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")
DB_PATH = os.path.join(BASE_DIR, "chroma_db")

def setup_chroma():
    """Initializes ChromaDB with a local PersistentClient and SentenceTransformers."""
    client = chromadb.PersistentClient(path=DB_PATH)
    emb_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    col_fixed = client.get_or_create_collection(
        name="ola_fixed_chunks", 
        metadata={"hnsw:space": "cosine"}, 
        embedding_function=emb_fn
    )
    col_sentence = client.get_or_create_collection(
        name="ola_sentence_chunks", 
        metadata={"hnsw:space": "cosine"}, 
        embedding_function=emb_fn
    )
    return client, col_fixed, col_sentence

def chunk_fixed_size(text, chunk_size=150, overlap=30):
    """Chunking Strategy 1: Fixed size with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def chunk_sentences(text):
    """Chunking Strategy 2: Sentence-based."""
    sentences = re.split(r'(?<=\.)\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def index_documents():
    """Reads the documents and indexes them using both strategies."""
    print(f"Checking folder: {KB_DIR}")
    if not os.path.exists(KB_DIR):
        print(f"❌ ERROR: The directory '{KB_DIR}' does not exist!")
        return

    files = [f for f in os.listdir(KB_DIR) if f.endswith(".txt")]
    print(f"Found {len(files)} text files to index.")
    
    if len(files) == 0:
        print(f"❌ ERROR: No '.txt' files found in '{KB_DIR}'. Check file extensions or location.")
        return

    _, col_fixed, col_sentence = setup_chroma()
    
    for filename in files:
        doc_id = filename.replace(".txt", "")
        file_path = os.path.join(KB_DIR, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
        if not content:
            print(f"⚠️ Warning: '{filename}' is empty, skipping.")
            continue

        # 1. Index Fixed Chunks
        fixed_chunks = chunk_fixed_size(content)
        if fixed_chunks:
            col_fixed.upsert(
                documents=fixed_chunks,
                metadatas=[{"source_doc": doc_id}] * len(fixed_chunks),
                ids=[f"{doc_id}_fixed_{i}" for i in range(len(fixed_chunks))]
            )
            
        # 2. Index Sentence Chunks
        sentence_chunks = chunk_sentences(content)
        if sentence_chunks:
            col_sentence.upsert(
                documents=sentence_chunks,
                metadatas=[{"source_doc": doc_id}] * len(sentence_chunks),
                ids=[f"{doc_id}_sentence_{i}" for i in range(len(sentence_chunks))]
            )
        print(f" Indexed '{filename}' -> ({len(fixed_chunks)} fixed chunks, {len(sentence_chunks)} sentence chunks)")
        
    print(f"✅ Total indexed in Fixed collection: {col_fixed.count()} chunks")
    print(f"✅ Total indexed in Sentence collection: {col_sentence.count()} chunks")

def mock_grounded_generation(query, collection_name, threshold=0.45):
    """Task 4: Grounded Generation with MOCK_LLM and calibrated fallback."""
    _, col_fixed, col_sentence = setup_chroma()
    col = col_fixed if collection_name == "ola_fixed_chunks" else col_sentence
    
    if col.count() == 0:
        raise ValueError(f"Collection '{collection_name}' is empty. Cannot run queries.")

    results = col.query(query_texts=[query], n_results=3)
    
    if not results["distances"] or len(results["distances"][0]) == 0:
        return "I don't know. (No matching context found)", 0.0, []

    top_distance = results["distances"][0][0]
    top_similarity = 1.0 - top_distance
    
    if top_similarity < threshold:
        return f"I don't know. (Threshold triggered: Similarity {top_similarity:.3f} < {threshold})", top_similarity, []
        
    retrieved_context = " | ".join(results["documents"][0])
    answer = f"[MOCK_LLM GENERATION] Using context: '{retrieved_context[:60]}...', the answer is generated."
    return answer, top_similarity, results["metadatas"][0]

def evaluate_metrics():
    """Task 4 & 5: Calibration measurement and Precision/Recall evaluation."""
    test_queries = {
        "in_scope": [
            ("What is the resolution time for a Critical priority ticket?", "sla-by-severity"),
            ("How long do wallet refunds take to process?", "refund-compensation-policy"),
            ("Can I get a refund for a driver cancellation?", "service-credit-policy"),
            ("What triggers the repeat-complaint protocol?", "repeat-complaint-handling"),
            ("Who handles media attention escalations?", "escalation-matrix")
        ],
        "out_scope": [
            ("What is the recipe for chocolate cake?", None),
            ("How do I fix my broken lawnmower?", None)
        ]
    }
    
    print("\n--- TASK 4: CALIBRATING THE 'I DON'T KNOW' THRESHOLD ---")
    for q_type, queries in test_queries.items():
        print(f"\nEvaluating {q_type.upper()} queries:")
        for q_text, _ in queries:
            _, sim, _ = mock_grounded_generation(q_text, "ola_sentence_chunks", threshold=0.0)
            print(f"  Query: '{q_text}' -> Top-1 Similarity: {sim:.3f}")
            
    print("\n--- TASK 5: CHUNKING STRATEGY EVALUATION (Precision@3 / Recall@3) ---")
    collections = ["ola_fixed_chunks", "ola_sentence_chunks"]
    
    for coll in collections:
        print(f"\nCollection: {coll}")
        total_p = 0
        total_r = 0
        
        for q_text, expected_doc in test_queries["in_scope"]:
            _, _, metadatas = mock_grounded_generation(q_text, coll, threshold=0.0)
            
            retrieved_docs = list(set([m["source_doc"] for m in metadatas]))
            relevant_docs_in_top_3 = 1 if expected_doc in retrieved_docs else 0
            
            p_at_3 = relevant_docs_in_top_3 / 3.0
            r_at_3 = relevant_docs_in_top_3 / 1.0 
            
            print(f"  Query: '{q_text[:40]}...' | Expected: {expected_doc} | Retrieved: {retrieved_docs}")
            print(f"    -> Precision@3: {p_at_3:.2f} (1/3) | Recall@3: {r_at_3:.2f} (1/1)")
            
            total_p += p_at_3
            total_r += r_at_3
            
        print(f"  AVG Precision@3: {total_p/5:.2f} | AVG Recall@3: {total_r/5:.2f}")

if __name__ == "__main__":
    index_documents()
    evaluate_metrics()