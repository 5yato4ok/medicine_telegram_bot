CREATE TABLE IF NOT EXISTS aid(
  id    TEXT PRIMARY KEY,
  owner TEXT NOT NULL, 
  name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meds(
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  valid       TIMESTAMP NOT NULL,
  category    TEXT,
  box         TEXT,
  quantity    REAL,
  aidid       TEXT,
  FOREIGN KEY(aidid) 
  REFERENCES aid(id)
  ON DELETE CASCADE
);