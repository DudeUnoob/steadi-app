#!/usr/bin/env python3
"""
Utility script to generate cron signatures for testing the threshold evaluator endpoint.
This can be used to:
1. Test the endpoint manually
2. Configure the signature in cron-job.org

Usage:
  python generate_cron_signature.py
"""

import hmac
import hashlib
import time
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_signature(secret_key):
    """Generate a signature for the threshold_evaluator cron job"""
    # Get current timestamp (rounded to nearest minute)
    timestamp = int(time.time() / 60) * 60
    
    # Calculate signature
    signature = hmac.new(
        secret_key.encode(),
        f"threshold_evaluator:{timestamp}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "timestamp": timestamp,
        "signature": signature
    }

def main():
    parser = argparse.ArgumentParser(description="Generate cron signatures for testing")
    parser.add_argument("--secret", default=os.environ.get("CRON_SECRET_KEY", "default-secret-replace-in-production"),
                        help="Secret key for signing (defaults to CRON_SECRET_KEY env var)")
    args = parser.parse_args()
    
    result = generate_signature(args.secret)
    
    print("\n=== Cron Signature for Threshold Evaluator ===")
    print(f"Timestamp: {result['timestamp']} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result['timestamp']))})")
    print(f"Signature: {result['signature']}")
    print("\nFor cron-job.org or similar services:")
    print("1. Set URL to: https://your-api-domain/cron/threshold-evaluator")
    print("2. Add custom header: X-Cron-Signature: " + result['signature'])
    print("3. Set schedule to: Every 15 minutes")
    print("4. The signature will be valid for approximately 1-2 minutes")
    print("\nFor testing with curl:")
    print(f"curl -X POST https://your-api-domain/cron/threshold-evaluator -H 'X-Cron-Signature: {result['signature']}'")
    
if __name__ == "__main__":
    main() 