-- category_tbl definition
CREATE TABLE IF NOT EXISTS cog_categories_tbl (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    CONSTRAINT category_tbl_name_unique UNIQUE (name)
);
-- cogs_tbl definition
CREATE TABLE IF NOT EXISTS cogs_tbl (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    config_name TEXT NOT NULL,
    description TEXT,
    cog_category_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    CONSTRAINT cogs_tbl_config_name_unique UNIQUE (config_name),
    CONSTRAINT cogs_tbl_name_unique UNIQUE (name),
    CONSTRAINT cogs_tbl_path_unique UNIQUE (relative_path),
    CONSTRAINT cogs_tbl_FK FOREIGN KEY (cog_category_id) REFERENCES cog_categories_tbl(id)
);
CREATE TABLE IF NOT EXISTS commands_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL UNIQUE,
    "cog_id" INTEGER,
    "is_group" INTEGER NOT NULL DEFAULT 0,
    "help" TEXT,
    "brief" TEXT,
    "short_doc" TEXT,
    "usage" TEXT,
    "signature" TEXT,
    "example" TEXT,
    "gif_path" TEXT,
    "github_link" TEXT,
    "enabled" BOOL NOT NULL,
    "hidden" BOOL NOT NULL,
    CONSTRAINT cogs_tbl_name_unique UNIQUE (name),
    CONSTRAINT cog_FK FOREIGN KEY ("cog_id") REFERENCES cogs_tbl(id)
);
CREATE TABLE IF NOT EXISTS memory_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" DATETIME NOT NULL UNIQUE,
    "memory_in_use" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS latency_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" DATETIME NOT NULL UNIQUE,
    "latency" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS cpu_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" DATETIME NOT NULL UNIQUE,
    "usage_percent" INTEGER NOT NULL,
    "load_average_1" INTEGER NOT NULL,
    "load_average_5" INTEGER NOT NULL,
    "load_average_15" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS category_channels_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL UNIQUE,
    "position" INTEGER NOT NULL UNIQUE,
    "created_at" DATETIME NOT NULL,
    "deleted" BOOL
);
CREATE TABLE IF NOT EXISTS text_channels_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL UNIQUE,
    "position" INTEGER NOT NULL UNIQUE,
    "created_at" DATETIME NOT NULL,
    "category_id" INTEGER REFERENCES "category_channels_tbl" ("id"),
    "topic" TEXT,
    "deleted" BOOL
);
CREATE TABLE IF NOT EXISTS channel_usage_tbl (
    "timestamp" DATETIME NOT NULL,
    "channel_id" INTEGER NOT NULL REFERENCES "text_channels_tbl" ("id"),
    UNIQUE ("timestamp", "channel_id")
);
CREATE INDEX IF NOT EXISTS channel_usage_timestamp_index ON "channel_usage_tbl" ("timestamp");
CREATE TABLE IF NOT EXISTS command_usage_tbl (
    "timestamp" DATETIME NOT NULL,
    "command_id" INTEGER NOT NULL REFERENCES "commands_tbl" ("id"),
    UNIQUE ("timestamp", "command_id")
);
CREATE INDEX IF NOT EXISTS command_usage_timestamp_index ON "command_usage_tbl" ("timestamp")