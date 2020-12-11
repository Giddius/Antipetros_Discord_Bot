CREATE TABLE author_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name STRING UNIQUE NOT NULL,
    display_name STRING UNIQUE NOT NULL,
    discord_id INTEGER UNIQUE NOT NULL,
    is_member BOOLEAN NOT NULL
);
CREATE TABLE saved_links_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    link_name STRING UNIQUE NOT NULL,
    link STRING NOT NULL,
    post_time DATETIME NOT NULL,
    delete_time DATETIME NOT NULL,
    is_removed BOOLEAN DEFAULT (0),
    message_discord_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL REFERENCES author_tbl (id)
);