import random

def generate_ola_dataset(seed=42, num_records=40):
    """
    Generates a deterministic dataset of Ola support tickets.
    
    Design Choices:
    - Seed: Set to 42 for deterministic output.
    - resolution_time_hours: Range of 0.5 to 72.0 hours. 
      Reasoning: Simple billing disputes are usually resolved quickly by tier-1 support (under an hour), 
      while complex product defects or safety escalations require manual investigation spanning multiple days.
    - Weights: 'Escalated' status probability is intentionally kept lower than standard statuses 
      to ensure the final escalated percentage naturally lands in the 10-30% band.
    """
    random.seed(seed)
    
    categories = ['Billing', 'Technical Issue', 'Account Access', 'Product Defect', 'General Inquiry']
    statuses = ['Open', 'In Progress', 'Escalated', 'Resolved', 'Closed']
    
    # Weighting statuses to keep 'Escalated' sparse enough to hit the 10-30% global target
    status_weights = [0.20, 0.20, 0.10, 0.25, 0.25]
    
    SUPPORT_TICKETS = []
    
    for i in range(num_records):
        record_id = f"TICK-{1001 + i}"
        category = random.choice(categories)
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        
        # If the ticket status is literally 'Escalated', the boolean must be True.
        # Otherwise, there is a small chance a resolved/closed ticket was previously escalated.
        if status == 'Escalated':
            escalated = True
        else:
            escalated = random.random() < 0.15  
            
        days_since_created = random.randint(0, 30)
        resolution_time_hours = round(random.uniform(0.5, 72.0), 1)
        
        SUPPORT_TICKETS.append({
            "record_id": record_id,
            "category": category,
            "status": status,
            "resolution_time_hours": resolution_time_hours,
            "days_since_created": days_since_created,
            "escalated": escalated
        })
        
    return SUPPORT_TICKETS

def validate_and_report(tickets):
    """Prints the distribution of the dataset to verify it meets all rubric constraints."""
    total_records = len(tickets)
    
    category_counts = {}
    status_counts = {}
    escalated_count = 0
    
    for t in tickets:
        category_counts[t['category']] = category_counts.get(t['category'], 0) + 1
        status_counts[t['status']] = status_counts.get(t['status'], 0) + 1
        if t['escalated']:
            escalated_count += 1
            
    escalated_percentage = (escalated_count / total_records) * 100
    
    print(f"--- DATASET VALIDATION REPORT (Total Records: {total_records}) ---")
    
    print("\n1. Category Counts (Requirement: >= 3 records each)")
    for cat, count in category_counts.items():
        print(f"   - {cat}: {count} records")
        
    print("\n2. Status Counts (Requirement: >= 1 record each)")
    for stat, count in status_counts.items():
        print(f"   - {stat}: {count} records")
        
    print(f"\n3. Escalation Rate (Requirement: 10% - 30%)")
    print(f"   - Escalated: {escalated_count}/{total_records} ({escalated_percentage:.1f}%)")
    
    # Success Checks
    cat_pass = all(c >= 3 for c in category_counts.values()) and len(category_counts) == 5
    stat_pass = all(s >= 1 for s in status_counts.values()) and len(status_counts) == 5
    esc_pass = 10.0 <= escalated_percentage <= 30.0
    
    print("\n--- FINAL VERDICT ---")
    if cat_pass and stat_pass and esc_pass:
        print("✅ SUCCESS: Dataset meets all structural thresholds.")
    else:
        print("❌ FAILED: Adjust the seed or weights and regenerate.")

if __name__ == "__main__":
    # Generate the tickets
    SUPPORT_TICKETS = generate_ola_dataset(seed=42, num_records=40)
    
    # Validate and print the report
    validate_and_report(SUPPORT_TICKETS)
    import json
    with open("data/tickets.json", "w") as f:
        json.dump(SUPPORT_TICKETS, f, indent=4)