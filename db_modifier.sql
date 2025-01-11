-- Use this space to modify any databases
-- Change the data source in the top right corner to the database you want to use

CREATE TABLE active_intakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    preview_path TEXT NOT NULL,
    description TEXT NOT NULL,
    used_in_competition BOOLEAN NOT NULL,
    team_number INTEGER NOT NULL,
    years_used TEXT NOT NULL,
    onshape_link TEXT NOT NULL
)
