#!/usr/bin/env python3
"""Generate a pool of fake people for testing purposes.

Produces realistic-looking but entirely fabricated identity records
(name, email, phone, address). Optional debt-settlement mode adds
credit fields for direct-mail / lead-list style test data.

Standard library only. No external dependencies.
"""

import argparse
import csv
import json
import random
import sys

FIRST_NAMES = [
    "Aiden", "Abigail", "Alexander", "Amelia", "Benjamin", "Charlotte", "Christopher", "Chloe",
    "Daniel", "Ella", "Elijah", "Emma", "Ethan", "Grace", "Gabriel", "Hannah",
    "Henry", "Isabella", "Jackson", "Lily", "Jacob", "Madison", "Jayden", "Mia",
    "Joseph", "Olivia", "Julian", "Penelope", "Liam", "Samantha", "Logan", "Sophia",
    "Lucas", "Victoria", "Mason", "Zoey", "Nathan", "Addison", "Noah", "Avery",
    "Oliver", "Bella", "Samuel", "Stella", "Sebastian", "Aurora", "Isaac", "Harper",
    "Caleb", "Layla", "Isaiah", "Nora", "Ryan", "Scarlett", "Connor", "Riley",
    "Hunter", "Savannah", "Owen", "Brooklyn", "Jack", "Hazel", "Aaron", "Luna",
    "Brandon", "Ellie", "Jaxon", "Paisley", "Adrian", "Skylar", "Gavin", "Mackenzie",
    "Evan", "Kennedy", "Dominic", "Ariana", "Jonathan", "Sadie", "Austin", "Allison",
    "Christian", "Violet", "Blake", "Sophie", "Adam", "Caroline", "Eli", "Lucy",
    "Cole", "Mila", "Zachary", "Ian", "Gabriella", "Justin", "Piper", "Nora",
]

LAST_NAMES = [
    "Adams", "Alexander", "Armstrong", "Bailey", "Bennett", "Brooks", "Butler", "Campbell",
    "Carter", "Collins", "Cooper", "Cox", "Diaz", "Edwards", "Evans", "Fisher",
    "Foster", "Gonzales", "Griffin", "Gutierrez", "Hawkins", "Hayes", "Hernandez", "Holmes",
    "Howard", "Hughes", "James", "Jenkins", "Jordan", "Kelly", "Kim", "Lawson",
    "Long", "Marshall", "Mendoza", "Miller", "Montgomery", "Morales", "Morgan", "Morris",
    "Murray", "Myers", "Ortiz", "Palmer", "Patterson", "Payne", "Perez", "Perry",
    "Peterson", "Price", "Ramirez", "Reed", "Reyes", "Richardson", "Rivera", "Roberts",
    "Robertson", "Rodgers", "Russell", "Sanders", "Scott", "Shaw", "Simmons", "Snyder",
    "Stewart", "Stone", "Sullivan", "Terry", "Thomas", "Thompson", "Turner", "Vasquez",
    "Wade", "Walker", "Wallace", "Ward", "Watson", "Weaver", "Webb", "Wells",
    "Wheeler", "Williams", "Williamson", "Wood", "Wright", "Young", "Zimmerman", "Anderson",
    "Banks", "Barnes", "Blake", "Bond", "Brady", "Briggs", "Carroll", "Clark",
    "Clarke", "Cole", "Cook", "Dean", "Duncan", "Ellis", "Ford", "Garrett",
]

STREET_NAMES = [
    "Main", "Oak", "Maple", "Pine", "Cedar", "Elm", "Washington", "Lake", "Hill", "Park",
    "River", "Church", "Walnut", "Highland", "Hickory", "Sunset", "Broadway", "Cherry",
    "Willow", "Adams", "Jefferson", "Jackson", "Franklin", "Lincoln",
]

STREET_TYPES = ["St", "Ave", "Blvd", "Ln", "Rd", "Dr", "Pl", "Ct", "Way", "Terrace"]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego",
    "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte", "San Francisco",
    "Indianapolis", "Seattle", "Denver", "Washington", "Boston", "El Paso", "Nashville", "Detroit",
    "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee",
]

STATES = [
    "NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "GA", "NC",
    "MI", "NJ", "VA", "WA", "MA", "TN", "IN", "MO",
]

EMAIL_DOMAINS = ["example.com", "example.net", "example.org", "test.example"]

BASE_FIELDS = ["first_name", "last_name", "email", "phone", "address", "city", "state", "zip"]
DEBT_FIELDS = ["estimated_debt", "credit_score", "num_creditors"]


def make_email(first, last):
    """Build an email that matches the person's name, so records are internally consistent."""
    return f"{first}.{last}{random.randint(1, 999)}@{random.choice(EMAIL_DOMAINS)}".lower()


def make_phone():
    """Random NANP-style 10-digit number (not guaranteed dialable)."""
    area = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(0, 9999)
    return f"({area}) {prefix}-{line:04d}"


def make_person(debt_settlement, debt_floor, debt_ceiling):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    person = {
        "first_name": first,
        "last_name": last,
        "email": make_email(first, last),
        "phone": make_phone(),
        "address": f"{random.randint(100, 9999)} {random.choice(STREET_NAMES)} {random.choice(STREET_TYPES)}",
        "city": random.choice(CITIES),
        "state": random.choice(STATES),
        "zip": f"{random.randint(501, 99950):05d}",
    }
    if debt_settlement:
        person["estimated_debt"] = random.randint(debt_floor, debt_ceiling)
        person["credit_score"] = random.randint(300, 850)
        person["num_creditors"] = random.randint(1, 12)
    return person


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a pool of fake people for testing purposes.",
    )
    parser.add_argument("-n", "--count", type=int, default=10000,
                        help="number of people to generate (default: 10000)")
    parser.add_argument("-o", "--output", default="people.csv",
                        help="output file, or '-' for stdout (default: people.csv)")
    parser.add_argument("-f", "--format", choices=["csv", "jsonl"], default="csv",
                        help="output format (default: csv)")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed the RNG for repeatable output within the same Python version")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="prompt for options instead of reading flags (auto-enabled when run with no args on a terminal)")
    parser.add_argument("--debt-settlement", action="store_true",
                        help="add credit fields: estimated_debt, credit_score, num_creditors")
    parser.add_argument("--debt-floor", type=int, default=10000,
                        help="minimum estimated_debt, with --debt-settlement (default: 10000)")
    parser.add_argument("--debt-ceiling", type=int, default=500000,
                        help="maximum estimated_debt, with --debt-settlement (default: 500000)")
    args = parser.parse_args(argv)

    if args.count < 0:
        parser.error("--count must be zero or positive")
    if args.debt_settlement and args.debt_floor > args.debt_ceiling:
        parser.error("--debt-floor must be <= --debt-ceiling")
    return args


def _prompt(text, default, cast=str, choices=None):
    """Prompt with a default; blank input accepts the default."""
    while True:
        raw = input(f"{text} [{default}]: ").strip()
        if raw == "":
            return default
        if choices and raw not in choices:
            print(f"  choose one of: {', '.join(choices)}")
            continue
        try:
            return cast(raw)
        except ValueError:
            print("  not a valid value, try again")


def _prompt_yes_no(text, default):
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{text} [{hint}]: ").strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  please answer y or n")


def interactive_prompts(args):
    """Fill args by asking the user, using the current values as defaults."""
    print("people-generator interactive mode (press Enter to accept each default)\n")
    args.count = _prompt("How many people?", args.count, int)
    args.format = _prompt("Output format (csv/jsonl)?", args.format, str, choices=["csv", "jsonl"])
    args.output = _prompt("Output file ('-' for stdout)?", args.output, str)
    args.debt_settlement = _prompt_yes_no("Add debt-settlement credit fields?", args.debt_settlement)
    if args.debt_settlement:
        while True:
            args.debt_floor = _prompt("Debt floor?", args.debt_floor, int)
            args.debt_ceiling = _prompt("Debt ceiling?", args.debt_ceiling, int)
            if args.debt_floor <= args.debt_ceiling:
                break
            print("  floor must be <= ceiling, try again")
    print()
    return args


def open_output(path):
    if path == "-":
        return sys.stdout, False
    return open(path, "w", newline="", encoding="utf-8"), True


def generate(args, stream):
    fields = BASE_FIELDS + (DEBT_FIELDS if args.debt_settlement else [])
    if args.format == "csv":
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for _ in range(args.count):
            writer.writerow(make_person(args.debt_settlement, args.debt_floor, args.debt_ceiling))
    else:
        for _ in range(args.count):
            person = make_person(args.debt_settlement, args.debt_floor, args.debt_ceiling)
            stream.write(json.dumps(person) + "\n")


def main(argv=None):
    raw_argv = sys.argv[1:] if argv is None else list(argv)
    args = parse_args(argv)

    # Interactive when explicitly asked, or when launched with no args on a real
    # terminal. Piped / no-args non-TTY runs use defaults and never block on stdin.
    interactive = args.interactive or (not raw_argv and sys.stdin.isatty())
    if interactive:
        args = interactive_prompts(args)

    if args.seed is not None:
        random.seed(args.seed)

    stream, should_close = open_output(args.output)
    try:
        generate(args, stream)
    finally:
        if should_close:
            stream.close()

    if args.output != "-":
        print(f"Wrote {args.count} people to {args.output} ({args.format}).")


if __name__ == "__main__":
    main()
