#!/usr/bin/env python3
"""
generate_codes.py — Generate volunteer codes
Each code encodes specific paragraph indices from the dataset
"""

import base64
import json
import sys

# ════════════════════════════════════════════
#  CONFIGURE
# ════════════════════════════════════════════

HF_INPUT_REPO = "ghananlpcommunity/twi-english-paragraph-dataset_news"
TOTAL_PARAGRAPHS = 257000  # Total in dataset

# How many paragraphs per volunteer
PARAGRAPHS_PER_VOLUNTEER = 1000

# Number of volunteers
NUM_VOLUNTEERS = 10

# ════════════════════════════════════════════


def encode_code(repo, indices):
    """Encode volunteer assignment"""
    payload = json.dumps({
        "repo": repo,
        "indices": indices
    }, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def generate_codes():
    """Generate volunteer codes with assigned paragraph indices"""
    volunteers = []
    
    for i in range(NUM_VOLUNTEERS):
        start_idx = i * PARAGRAPHS_PER_VOLUNTEER
        end_idx = min(start_idx + PARAGRAPHS_PER_VOLUNTEER, TOTAL_PARAGRAPHS)
        indices = list(range(start_idx, end_idx))
        
        if not indices:
            break
        
        code = encode_code(HF_INPUT_REPO, indices)
        volunteers.append({
            "volunteer": i + 1,
            "paragraphs": len(indices),
            "range": f"{start_idx}-{end_idx-1}",
            "code": code
        })
    
    return volunteers


if __name__ == "__main__":
    print("📝  Generating volunteer codes...\n")
    volunteers = generate_codes()
    
    if not volunteers:
        sys.exit("❌ No codes generated — check config")
    
    # Print table
    print("=" * 95)
    print("  VOLUNTEER CODES")
    print("=" * 95)
    print(f"  {'#':<4} {'PARAGRAPHS':<12} {'RANGE':<20}  CODE")
    print(f"  {'-'*4} {'-'*12} {'-'*20}  {'-'*50}")
    
    for v in volunteers:
        print(f"  {v['volunteer']:<4} {v['paragraphs']:<12} {v['range']:<20}  {v['code']}")
    
    print("=" * 95)
    print()
    
    # Save codes
    with open("volunteer_codes.json", "w") as f:
        json.dump(volunteers, f, indent=2)
    
    print("✅ Codes saved to volunteer_codes.json")
    print("⚠️  Share individual codes only — keep volunteer_codes.json private\n")
