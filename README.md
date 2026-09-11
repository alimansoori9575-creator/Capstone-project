# Ola Support Agent - Capstone Project

**Track:** Business Operations / Customer Support (Ola)

This is my final submission for the Ola domain support agent. The entire project is set up to run locally using the `MOCK_LLM` setting, meaning no API keys or paid accounts are needed to test the agent, RAG, or the API.

## 1. Dataset Generation (Part 1)
To make sure the dataset (`data/tickets.json`) is fully reproducible, I used `42` as the random seed in `dataset.py`.

* **Time Range:** I set the resolution time range between 0.5 and 72.0 hours. I figured simple billing questions usually get closed in under an hour, but complex escalations might take a few days to investigate.
* **Distribution:** I used equal weighting to make sure we hit the minimum coverage rules for every category and status. 
  * *Categories:* Billing (9), General Inquiry (7), Product Defect (6), Technical Issue (6), Account Access (12).
  * *Statuses:* Open (11), Resolved (13), In Progress (6), Closed (9), Escalated (1).
* **Escalation Rate:** The random draw resulted in 6 out of 40 tickets being escalated (15.0%), which lands perfectly in the required 10-30% range.

## 2. RAG & Chunking Setup

**Threshold Calibration:**
I tested the top-1 cosine similarity to find a good cutoff for the "I don't know" fallback. 
* My in-scope test queries (like "How long do wallet refunds take?" and "What is the resolution time for a Critical priority ticket?") scored between `0.424` and `0.850`.
* My completely random out-of-scope queries (like asking for a cake recipe or how to fix a lawnmower) scored really low, between `0.033` and `0.086`.
* **Decision:** I set the threshold to `0.30`. It creates a safe buffer so weird user prompts get blocked, but legit policy questions still easily pass through.

**Chunking Strategy:**
I compared fixed-size chunks (`ola_fixed_chunks`) against sentence-based chunking (`ola_sentence_chunks`). Both actually gave me a Recall@3 of 1.00 and a Precision@3 of 0.33. However, I decided to deploy the **sentence-based chunking**. It keeps the vector store slightly smaller (38 chunks vs 41) and avoids cutting sentences in half, which just feels cleaner for text-heavy policy documents.

## 3. Escalation Logic
For the `check_support_ticket_status` tool, I wrote a custom escalation score formula: `(0.6 * escalated_boolean) + (0.4 * normalized_recency)`. The recency part just divides the days open by a 30-day window. If the final score hits `0.60` or higher, the agent flags it for the "Escalate to Tier 2" action. 

## How to Test My Code

Here is how to run the different parts of the capstone.

**1. Test the LangGraph Graph (Memory, Checkpoints, Timeouts)**
```bash
python -m app.graph