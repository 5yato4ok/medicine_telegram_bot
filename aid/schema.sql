CREATE TABLE IF NOT EXISTS aid(
  id    INTEGER PRIMARY KEY, 
  name  TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS meds(
  id          INTEGER PRIMARY KEY,
  trackname   TEXT, 
  name        TEXT NOT NULL,
  valid       DATA_TYPE NOT NULL,
  category    TEXT,
  box         TEXT,
  quantity    INTEGER,
  aidid       INTEGER,
  FOREIGN KEY(aidid) REFERENCES aid(id)
);