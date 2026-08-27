"""Stage 1 -- raw dataset -> Postgres.

Load raw rows first, clean in SQL afterwards. Cleaning in SQL rather than in
pandas means the cleaning is reproducible, reviewable and re-runnable, which
matters when Stage 3 tells you the data was the problem all along.

DEDUPE HARD. Job boards are full of the same posting reposted across
companies and dates. Duplicates silently inflate every frequency number in
Stage 4, and the output looks perfectly plausible while being wrong.
"""

from __future__ import annotations

# TODO Stage 1:
#   1. read the frozen snapshot (data/postings.csv)
#   2. filter to the roles in data/roles.json by title match
#   3. dedupe on (normalized_title, company, first 500 chars of description)
#   4. insert into postings
#   5. print per-role counts and FAIL if any role is under 250 -- that is the
#      Stage 1 gate, and enforcing it in code stops you talking yourself past it


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
