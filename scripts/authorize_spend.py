"""Create an explicitly authorized, expiring test session (never resets an existing ID)."""
import argparse
import sys
import time
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import spend


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', required=True)
    parser.add_argument('--ceiling-usd', default='1.00')
    parser.add_argument('--hours', type=float, default=4)
    parser.add_argument('--authorization', help='Explicit operator authorization record; never an API key')
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    if not args.status:
        if not args.authorization or not 0 < args.hours <= 24:
            parser.error('Authorization text and an expiry of 0–24 hours are required.')
        value = Decimal(args.ceiling_usd) * 1_000_000
        if not value.is_finite() or value != value.to_integral_value():
            parser.error('Use a finite dollar amount with at most six decimal places.')
        spend.authorize(args.session, int(value), time.time()+args.hours*3600, authorization=args.authorization)
    print(spend.status(args.session))


if __name__ == '__main__':
    main()
