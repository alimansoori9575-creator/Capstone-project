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