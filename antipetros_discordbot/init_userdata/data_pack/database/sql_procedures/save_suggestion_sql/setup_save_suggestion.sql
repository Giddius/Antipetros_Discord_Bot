CREATE TABLE author_tbl (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name STRING UNIQUE NOT NULL,
    display_name STRING UNIQUE NOT NULL,
    discord_id INTEGER UNIQUE NOT NULL,
    is_member BOOLEAN NOT NULL
);
CREATE TABLE category_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
    name STRING UNIQUE NOT NULL,
    emoji STRING UNIQUE
);
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        1,
        'General',
        NULL
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        2,
        'Bug',
        'REGIONAL INDICATOR SYMBOL LETTER B'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        3,
        'Change request',
        'REGIONAL INDICATOR SYMBOL LETTER C'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        4,
        'Feature request',
        'REGIONAL INDICATOR SYMBOL LETTER F'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        5,
        'Game Balance',
        'REGIONAL INDICATOR SYMBOL LETTER G'
    );
INSERT INTO category_tbl (
        id,
        name,
        emoji
    )
VALUES (
        6,
        'Minor Task',
        'CHILDREN CROSSING'
    );
CREATE TABLE extra_data_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    name STRING NOT NULL UNIQUE,
    location STRING UNIQUE NOT NULL
);
CREATE TABLE suggestion_tbl (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    name STRING,
    author_id INTEGER REFERENCES author_tbl (id) NOT NULL,
    added_by_author_id INTEGER REFERENCES author_tbl (id) NOT NULL,
    message_discord_id INTEGER UNIQUE NOT NULL,
    link_to_message STRING UNIQUE,
    utc_posted_time DATETIME NOT NULL,
    utc_saved_time DATETIME NOT NULL,
    upvotes INTEGER DEFAULT (0),
    downvotes INTEGER DEFAULT (0),
    content BLOB UNIQUE NOT NULL,
    extra_data_id INTEGER REFERENCES extra_data_tbl (id),
    discussed BOOLEAN DEFAULT (0),
    category_id INTEGER REFERENCES category_tbl (id) DEFAULT (1)
);