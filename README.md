# Ola Domain Support Agent Capstone

**Track Completed:** Ola (Business Operations / Customer Support)

## Dataset Design Choices (Part 1, Task 1)
The support ticket dataset (`data/tickets.json`) was generated deterministically. To reproduce the exact dataset, use the following parameters:

*   **Generator Seed:** `42`
*   **Resolution Time Range:** `0.5` to `72.0` hours. 
    *   *Reasoning:* Simple billing disputes are usually resolved quickly (under an hour), while complex product defects or safety escalations require manual investigation spanning multiple days.
*   **Dataset Size:** 40 records
*   **Category Distribution:** 
   - Billing: 9 records
   - General Inquiry: 7 records
   - Product Defect: 6 records
   - Technical Issue: 6 records
   - Account Access: 12 records
*   **Status Distribution:** 
   - Open: 11 records
   - Resolved: 13 records
   - In Progress: 6 records
   - Closed: 9 records
   - Escalated: 1 records
*   **Escalated Percentage:** 6/40 (15.0%)
(Successfully landed in the 10-30% required band).

## RAG Calibration & Chunking Strategy Evaluation

### 1. Empirical Fallback Threshold Calibration (Task 4)
Top-1 cosine similarity was measured across in-scope and out-of-scope queries:
* **In-Scope Queries:** 
  * "What is the resolution time for a Critical priority ticket?": `0.788`
  * "How long do wallet refunds take to process?": `0.850`
  * "Can I get a refund for a driver cancellation?": `0.631`
  * "What triggers the repeat-complaint protocol?": `0.803`
  * "Who handles media attention escalations?": `0.424`
  * *Range: 0.424 – 0.850*
* **Out-of-Scope Queries:** 
  * "What is the recipe for chocolate cake?": `0.033`
  * "How do I fix my broken lawnmower?": `0.086`
  * *Range: 0.033 – 0.086*

**Chosen Fallback Threshold:** `0.30`. This threshold sits safely between the out-of-scope ceiling (`0.086`) and the in-scope floor (`0.424`), reliably triggering the fallback response on irrelevant prompts.

### 2. Chunking Strategy Comparison (Task 5)
* **Fixed-Size Chunking (`ola_fixed_chunks`):** Average Precision@3 = `0.33`, Average Recall@3 = `1.00` (41 total chunks).
* **Sentence-Based Chunking (`ola_sentence_chunks`):** Average Precision@3 = `0.33`, Average Recall@3 = `1.00` (38 total chunks).

**Deployment Recommendation:** We deploy the **sentence-based chunking strategy (`ola_sentence_chunks`)**. While both strategies attained an identical 1.00 Recall@3, sentence chunking produced complete syntactic thoughts without splitting sentences across chunk boundaries, resulting in a more compact vector store (38 chunks vs 41 chunks) without any retrieval degradation.