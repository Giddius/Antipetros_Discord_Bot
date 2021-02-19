CREATE TABLE author_tbl (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT UNIQUE NOT NULL,
    discord_id INTEGER UNIQUE NOT NULL,
    is_member BOOLEAN NOT NULL
);
CREATE TABLE team_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
    name TEXT NOT NULL UNIQUE,
    save_emoji TEXT UNIQUE NOT NULL
);
INSERT INTO team_tbl (name, save_emoji)
VALUES ('dev_team', 'floppy_disk');
INSERT INTO team_tbl (name, save_emoji)
VALUES (
        'admin_team',
        'computer_disk'
    );
INSERT INTO team_tbl (name, save_emoji)
VALUES ('event_team', 'notebook');
INSERT INTO team_tbl (name, save_emoji)
VALUES ('pr_team', 'videocassette');
INSERT INTO team_tbl (name, save_emoji)
VALUES (
        'art_team',
        'framed_picture_selector'
    );
INSERT INTO team_tbl (name, save_emoji)
VALUES (
        'backend_team',
        'laptop_computer'
    );
CREATE TABLE category_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    emoji TEXT UNIQUE
);
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        1,
        'General',
        'regional_indicator_symbol_letter_o'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        2,
        'Bug',
        'regional_indicator_symbol_letter_b'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        3,
        'Change request',
        'regional_indicator_symbol_letter_c'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        4,
        'Feature request',
        'regional_indicator_symbol_letter_f'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        5,
        'Game Balance',
        'regional_indicator_symbol_letter_g'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        6,
        'Minor Task',
        'children_crossing'
    );
CREATE TABLE extra_data_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    location TEXT UNIQUE NOT NULL
);
CREATE TABLE suggestion_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    name TEXT,
    author_id INTEGER REFERENCES author_tbl (id) NOT NULL,
    added_by_author_id INTEGER REFERENCES author_tbl (id) NOT NULL,
    message_discord_id INTEGER UNIQUE NOT NULL,
    link_to_message TEXT UNIQUE,
    utc_posted_time DATETIME NOT NULL,
    utc_saved_time DATETIME NOT NULL,
    upvotes INTEGER DEFAULT (0),
    downvotes INTEGER DEFAULT (0),
    content BLOB UNIQUE NOT NULL,
    extra_data_id INTEGER REFERENCES extra_data_tbl (id),
    discussed BOOLEAN DEFAULT (0),
    category_id INTEGER REFERENCES category_tbl (id) DEFAULT (1),
    team_id INTEGER REFERENCES team_tbl (id)
);
CREATE TABLE emoji_tbl(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    alias TEXT NOT NULL UNIQUE,
    as_unicode TEXT NOT NULL UNIQUE
)