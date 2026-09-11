# Ola Support Agent - Capstone Project

**Track:** Business Operations / Customer Support (Ola)

This is my final submission for the Ola domain support agent capstone. I built the entire project to run locally using the `MOCK_LLM` setting, so you don't need any API keys, paid accounts, or network access to run my code or test the agent.

## 1. Dataset Generation (Part 1)
To make sure the dataset (`data/tickets.json`) is fully reproducible, I used `42` as the random seed in my `dataset.py` file.

* **Time Range:** I set the resolution time range between 0.5 and 72.0 hours. I figured simple billing questions usually get closed in under an hour, but complex escalations or product defects might take a few days to investigate.
* **Distribution:** I used equal weighting to make sure I hit the minimum coverage rules for every category and status. 
  * *Categories:* Account Access (12), Billing (9), General Inquiry (7), Product Defect (6), Technical Issue (6).
  * *Statuses:* Resolved (13), Open (11), Closed (9), In Progress (6), Escalated (1).
* **Escalation Rate:** My random draw resulted in 6 out of 40 tickets being escalated (15.0%), which lands right in the required 10-30% range.

## 2. RAG & Chunking Setup

**Threshold Calibration:**
I tested the top-1 cosine similarity to find a safe cutoff for the "I don't know" fallback. 
* My in-scope test queries (like "How long do wallet refunds take?") scored between `0.424` and `0.850`.
* My completely random out-of-scope queries (like asking for a cake recipe) scored really low, between `0.033` and `0.086`.
* **Decision:** I set the threshold to `0.30`. It creates a safe buffer so weird user prompts get blocked, but legitimate policy questions still pass through.

**Chunking Strategy:**
I compared fixed-size chunks (`ola_fixed_chunks`) against sentence-based chunking (`ola_sentence_chunks`). Both actually gave me a Recall@3 of 1.00 and a Precision@3 of 0.33. I decided to deploy the **sentence-based chunking**. It keeps the vector store slightly smaller (38 chunks vs 41) and avoids cutting sentences in half, which just feels much cleaner for text-heavy policy documents.

## 3. Escalation Logic
For the `check_support_ticket_status` tool, I wrote a custom escalation score formula: `(0.6 * escalated_boolean) + (0.4 * normalized_recency)`. The recency part divides the days open by a 30-day window. If the final score hits `0.60` or higher, the agent flags it for the "Escalate to Tier 2" action. 

## 4. RAG Triad Evaluation (Part 3)
I built an evaluation script (`eval/evaluator.py`) to test 15 specific queries (12 covering the required KB topics and 3 out-of-scope). Since this is running under `MOCK_LLM`, the script mocks the LLM-as-a-judge JSON output to calculate the averages for Context Relevance, Groundedness, and Answer Relevance. For my dataset, this resulted in an average of 0.80 for Context and Answer Relevance, and 1.00 for Groundedness.

## How to Test My Code

Here is how to run the different parts of the project from the terminal.

**1. Test the LangGraph Graph (Memory, Checkpoints, Timeouts)**
```bash
python -m app.graph