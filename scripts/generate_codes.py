#!/usr/bin/env python3
"""
generate_codes.py — Generate volunteer codes
Each code encodes specific paragraph indices from the dataset AND the HF token

Usage:
    python generate_codes.py <hf_token> [--target-samples N] [--volunteers N]

Examples:
    python generate_codes.py hf_abc123 --target-samples 10000 --volunteers 10
    python generate_codes.py hf_abc123 --target-samples 5000 --volunteers 5
"""

import argparse
import base64
import json
import sys

# ════════════════════════════════════════════
#  CONFIGURE
# ════════════════════════════════════════════

HF_INPUT_REPO = "ghananlpcommunity/twi-english-paragraph-dataset_news"
TOTAL_PARAGRAPHS_IN_DATASET = 257000  # Total available in dataset

# Default values (can be overridden by CLI arguments)
DEFAULT_TARGET_SAMPLES = 257000   # Total Twi texts to generate
DEFAULT_NUM_VOLUNTEERS = 10      # Number of volunteers to split work across

# ════════════════════════════════════════════


def encode_code(repo, indices, token):
    """Encode volunteer assignment including HF token"""
    payload = json.dumps({
        "repo": repo,
        "indices": indices,
        "token": token
    }, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def generate_codes(hf_token, target_samples, num_volunteers):
    """Generate volunteer codes with assigned paragraph indices
    
    Args:
        hf_token: HuggingFace token with write access to output repo
        target_samples: Total number of Twi texts to generate
        num_volunteers: Number of volunteers to distribute work across
    
    Returns:
        List of volunteer code dictionaries
    """
    # Each prompt generates 1 Twi text, so we need target_samples unique paragraphs
    paragraphs_needed = target_samples
    
    if paragraphs_needed > TOTAL_PARAGRAPHS_IN_DATASET:
        print(f"⚠️  Warning: Requested {paragraphs_needed:,} samples but only {TOTAL_PARAGRAPHS_IN_DATASET:,} paragraphs available.")
        paragraphs_needed = TOTAL_PARAGRAPHS_IN_DATASET
    
    # Split evenly across volunteers
    paragraphs_per_volunteer = paragraphs_needed // num_volunteers
    
    volunteers = []
    current_start = 0
    
    for i in range(num_volunteers):
        # Last volunteer gets any remainder
        if i == num_volunteers - 1:
            end_idx = paragraphs_needed
        else:
            end_idx = current_start + paragraphs_per_volunteer
        
        indices = list(range(current_start, end_idx))
        
        if not indices:
            break
        
        code = encode_code(HF_INPUT_REPO, indices, hf_token)
        volunteers.append({
            "volunteer": i + 1,
            "paragraphs": len(indices),
            "range": f"{current_start}-{end_idx-1}",
            "code": code
        })
        
        current_start = end_idx
    
    return volunteers, paragraphs_needed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate volunteer codes for Twi text collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_codes.py hf_abc123 --target-samples 10000 --volunteers 10
  python generate_codes.py hf_abc123 --target-samples 5000 --volunteers 5
  python generate_codes.py hf_abc123  # Uses defaults: 10k samples, 10 volunteers
        """
    )
    
    parser.add_argument(
        "hf_token",
        help="HuggingFace token with write access to ghananlpcommunity/prestine-twi"
    )
    
    parser.add_argument(
        "--target-samples",
        type=int,
        default=DEFAULT_TARGET_SAMPLES,
        help=f"Total number of Twi texts to generate (default: {DEFAULT_TARGET_SAMPLES:,})"
    )
    
    parser.add_argument(
        "--volunteers",
        type=int,
        default=DEFAULT_NUM_VOLUNTEERS,
        help=f"Number of volunteers to distribute work across (default: {DEFAULT_NUM_VOLUNTEERS})"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Validate token format
    if not args.hf_token.startswith("hf_"):
        print("⚠️  Warning: Token doesn't start with 'hf_' - are you sure this is correct?")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    print(f"📝  Generating volunteer codes...")
    print(f"    Target samples: {args.target_samples:,}")
    print(f"    Volunteers: {args.volunteers}")
    print()
    
    volunteers, actual_paragraphs = generate_codes(
        args.hf_token,
        args.target_samples,
        args.volunteers
    )
    
    if not volunteers:
        sys.exit("❌ No codes generated — check your configuration")
    
    # Print summary table
    print("=" * 95)
    print("  VOLUNTEER CODES")
    print("=" * 95)
    print(f"  {'#':<4} {'PARAGRAPHS':<12} {'RANGE':<20}  CODE (first 50 chars)")
    print(f"  {'-'*4} {'-'*12} {'-'*20}  {'-'*50}")
    
    for v in volunteers:
        code_preview = v['code'][:50] + "..." if len(v['code']) > 50 else v['code']
        print(f"  {v['volunteer']:<4} {v['paragraphs']:<12} {v['range']:<20}  {code_preview}")
    
    print("=" * 95)
    print()
    print(f"  Total texts to generate: {actual_paragraphs:,}")
    print(f"  Texts per volunteer: ~{actual_paragraphs // args.volunteers:,}")
    print()
    
    # Save codes
    with open("volunteer_codes.json", "w") as f:
        json.dump(volunteers, f, indent=2)
    
    print("✅ Codes saved to volunteer_codes.json")
    print()
    print("⚠️  SECURITY NOTES:")
    print("    • Each code contains the HF write token embedded")
    print("    • Share individual codes ONLY with trusted volunteers")
    print("    • Keep volunteer_codes.json PRIVATE")
    print("    • Token has write access to ghananlpcommunity/prestine-twi")
    print("    • Each volunteer gets a unique subset of paragraphs")
    print("    • DO NOT commit volunteer_codes.json to git")
    print()
