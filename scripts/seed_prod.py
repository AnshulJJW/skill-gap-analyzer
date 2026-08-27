"""Stage 7 -- seed the deployed database from the committed snapshot.

Never seed production by hand. If you cannot redo it from a script, you
cannot redo it at all, and you will need to redo it -- probably the night
before you send the link to someone.
"""

from __future__ import annotations

# TODO Stage 7: same as load_db.py but pointed at DATABASE_URL from the
#               environment, with an explicit --confirm flag so it cannot
#               run against prod by accident.


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
