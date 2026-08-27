"""Stage 4 -- offline build step: postings -> data/profiles/<role>.json.

Run this whenever the taxonomy or the dataset changes. The API only ever
reads the output. Keeping this offline is what keeps the API inside the
512MB / 10s cold-start budget in Stage 5's gate.
"""

from __future__ import annotations

# TODO Stage 4:
#   for each role in data/roles.json:
#     - pull its postings
#     - extract() each one, keeping the required/preferred split
#     - aggregate into SkillDemand rows
#     - RoleProfile(...).save()


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
