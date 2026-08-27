-- Stage 1 schema.
--
-- The important design decision here is `source`. Postings from different
-- job boards describe different labour markets: pooling LinkedIn (largely
-- US) with Naukri (India) and computing one percentage produces a number
-- that is an artifact of which dataset happened to be bigger, not a fact
-- about either market. So `source` is carried everywhere and profiles are
-- computed per (role, source).

CREATE TABLE IF NOT EXISTS sources (
    id           TEXT PRIMARY KEY,          -- 'linkedin', 'naukri'
    name         TEXT NOT NULL,
    market       TEXT NOT NULL,             -- 'global', 'india'
    collected_on DATE,                      -- when the snapshot was taken
    notes        TEXT
);

CREATE TABLE IF NOT EXISTS postings (
    id            BIGSERIAL PRIMARY KEY,
    source_id     TEXT NOT NULL REFERENCES sources(id),
    external_id   TEXT,                     -- the board's own id, if present
    role_id       TEXT NOT NULL,            -- matched from data/roles.json
    title         TEXT NOT NULL,
    company       TEXT,
    location      TEXT,
    description   TEXT NOT NULL,
    posted_on     DATE,
    dedupe_key    TEXT NOT NULL,            -- see UNIQUE below
    UNIQUE (source_id, dedupe_key)
);

-- Dedupe within a source, not across. The same role genuinely appears on
-- both boards and both sightings are real evidence; the same posting
-- repeated ten times on one board is not.
--
-- dedupe_key = md5(lower(title) || '|' || lower(company) || '|' ||
--                  left(regexp_replace(description,'\s+',' ','g), 500))
--
-- Duplicates silently inflate every frequency in Stage 4, and the output
-- looks entirely plausible while being wrong. This is the failure mode most
-- likely to survive undetected all the way to a demo.

CREATE INDEX IF NOT EXISTS postings_role_source ON postings (role_id, source_id);

CREATE TABLE IF NOT EXISTS posting_skills (
    posting_id  BIGINT NOT NULL REFERENCES postings(id) ON DELETE CASCADE,
    skill_id    TEXT   NOT NULL,
    section     TEXT   NOT NULL,            -- 'required' | 'preferred' | 'other'
    method      TEXT   NOT NULL,            -- 'alias' | 'fuzzy' | 'embedding'
    confidence  REAL   NOT NULL,
    evidence    TEXT,                       -- the sentence it came from
    PRIMARY KEY (posting_id, skill_id, section)
);

CREATE INDEX IF NOT EXISTS posting_skills_skill ON posting_skills (skill_id);

-- Kept for the Stage 3 comparison: several Kaggle sets ship their own
-- pre-extracted skills column. Storing it separately lets us report how our
-- extractor compares against it -- a free baseline, and a better answer than
-- "I used the skills column the dataset gave me".
CREATE TABLE IF NOT EXISTS postings_provided_skills (
    posting_id BIGINT NOT NULL REFERENCES postings(id) ON DELETE CASCADE,
    raw_skill  TEXT   NOT NULL,
    PRIMARY KEY (posting_id, raw_skill)
);
