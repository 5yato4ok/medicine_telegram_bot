CREATE TABLE IF NOT EXISTS aid(
  id    TEXT PRIMARY KEY, 
  name  TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS meds(
  id          TEXT PRIMARY KEY,
  trackname   TEXT, 
  name        TEXT NOT NULL,
  valid       DATA_TYPE NOT NULL,
  category    TEXT,
  box         TEXT,
  quantity    INTEGER,
  aidid       TEXT,
  FOREIGN KEY(aidid) REFERENCES aid(id)
);