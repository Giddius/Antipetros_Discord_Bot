CREATE TABLE IF NOT EXISTS "images_tbl" (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    data BLOB NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS cog_categories_tbl (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    CONSTRAINT category_tbl_name_unique UNIQUE (name)
);
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
    "example" TEXT,
    "gif_path" TEXT,
    "github_link" TEXT,
    "enabled" BOOL NOT NULL,
    "hidden" BOOL NOT NULL,
    "image_id" Integer REFERENCES "images_tbl"("id"),
    CONSTRAINT cogs_tbl_name_unique UNIQUE (name),
    CONSTRAINT cog_FK FOREIGN KEY ("cog_id") REFERENCES cogs_tbl(id)
);
CREATE TABLE IF NOT EXISTS memory_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" TIMESTAMP NOT NULL UNIQUE DEFAULT (datetime('now', 'utc')),
    "memory_in_use" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS latency_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" TIMESTAMP NOT NULL UNIQUE DEFAULT (datetime('now', 'utc')),
    "latency" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS cpu_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" TIMESTAMP NOT NULL UNIQUE DEFAULT (datetime('now', 'utc')),
    "usage_percent" INTEGER NOT NULL,
    "load_average_1" INTEGER NOT NULL,
    "load_average_5" INTEGER NOT NULL,
    "load_average_15" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS category_channels_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL UNIQUE,
    "position" INTEGER NOT NULL UNIQUE,
    "created_at" TIMESTAMP NOT NULL,
    "deleted" BOOL
);
CREATE TABLE IF NOT EXISTS text_channels_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL UNIQUE,
    "position" INTEGER NOT NULL UNIQUE,
    "created_at" TIMESTAMP NOT NULL,
    "category_id" INTEGER REFERENCES "category_channels_tbl" ("id"),
    "topic" TEXT,
    "deleted" BOOL
);
CREATE TABLE IF NOT EXISTS channel_usage_tbl (
    "timestamp" TIMESTAMP NOT NULL DEFAULT (datetime('now', 'utc')),
    "channel_id" INTEGER NOT NULL REFERENCES "text_channels_tbl" ("id"),
    UNIQUE ("timestamp", "channel_id")
);
CREATE VIEW IF NOT EXISTS channel_usage_view AS
SELECT COUNT(timestamp) AS usage_amount,
    channel_id
FROM channel_usage_tbl
GROUP BY channel_id
ORDER BY usage_amount DESC;
CREATE TABLE IF NOT EXISTS command_usage_tbl (
    "timestamp" TIMESTAMP NOT NULL DEFAULT (datetime('now', 'utc')),
    "command_id" INTEGER NOT NULL REFERENCES "commands_tbl" ("id"),
    UNIQUE ("timestamp", "command_id")
);
CREATE VIEW IF NOT EXISTS command_usage_view AS
SELECT COUNT(timestamp) AS usage_amount,
    command_id
FROM command_usage_tbl
GROUP BY command_id
ORDER BY usage_amount DESC;
CREATE TABLE IF NOT EXISTS server_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL UNIQUE,
    "address" TEXT NOT NULL,
    "port" INTEGER NOT NULL,
    "query_port" INTEGER NOT NULL UNIQUE,
    UNIQUE("address", "port")
);
CREATE INDEX IF NOT EXISTS server_index ON server_tbl ("id");
CREATE TABLE IF NOT EXISTS server_population_tbl (
    "timestamp" TIMESTAMP NOT NULL DEFAULT (datetime('now', 'utc')),
    "server_id" INTEGER NOT NULL REFERENCES "server_tbl" ("id"),
    "amount_players" INTEGER NOT NULL,
    UNIQUE ("timestamp", "server_id")
);
CREATE INDEX IF NOT EXISTS server_population_index ON server_population_tbl ("server_id");
CREATE TABLE IF NOT EXISTS is_online_messages_tbl (
    "server_id" INTEGER NOT NULL UNIQUE REFERENCES "server_tbl" ("id"),
    "message_id" INTEGER UNIQUE
);
CREATE INDEX IF NOT EXISTS is_online_messages_index ON is_online_messages_tbl ("server_id");
CREATE TABLE IF NOT EXISTS misc_messages_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL UNIQUE,
    "channel_id" INTEGER NOT NULL REFERENCES "text_channels_tbl" ("id"),
    "message_id" INTEGER NOT NULL,
    "extra_info" TEXT,
    UNIQUE("channel_id", "message_id")
);
CREATE TABLE IF NOT EXISTS reminder_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL UNIQUE,
    "remind_at" TIMESTAMP NOT NULL,
    "user_id" INTEGER NOT NULL,
    "original_channel_id" INTEGER NOT NULL REFERENCES "text_channels_tbl" ("id"),
    "original_message_id" INTEGER NOT NULL UNIQUE,
    "reason" TEXT,
    "reference_message_id" INTEGER,
    "done" BOOL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS log_level_tbl (
    "id" INTEGER NOT NULL UNIQUE,
    "name" TEXT NOT NULL UNIQUE
);
INSERT
    OR IGNORE INTO "log_level_tbl" ("id", "name")
VALUES (0, 'NO_LEVEL');
INSERT
    OR IGNORE INTO "log_level_tbl" ("id", "name")
VALUES (1, 'DEBUG');
INSERT
    OR IGNORE INTO "log_level_tbl" ("id", "name")
VALUES (2, 'INFO');
INSERT
    OR IGNORE INTO "log_level_tbl" ("id", "name")
VALUES (3, 'WARNING');
INSERT
    OR IGNORE INTO "log_level_tbl" ("id", "name")
VALUES (4, 'CRITICAL');
INSERT
    OR IGNORE INTO "log_level_tbl" ("id", "name")
VALUES (5, 'ERROR');
CREATE TABLE IF NOT EXISTS antistasi_function_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "function_name" TEXT NOT NULL UNIQUE,
    "file_name" TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS log_record_type_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS log_files_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "server_id" INTEGER NOT NULL REFERENCES "server_tbl" ("id"),
    UNIQUE("name", "server_id")
);
CREATE TABLE IF NOT EXISTS log_records_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "recorded_at" TIMESTAMP NOT NULL,
    "server_id" INTEGER NOT NULL REFERENCES "server_tbl" ("id"),
    "file_id" INTEGER NOT NULL REFERENCES "log_files_tbl" ("id"),
    "start" INTEGER NOT NULL,
    "end" INTEGER NOT NULL,
    "level_id" INTEGER NOT NULL REFERENCES "log_level_tbl" ("id"),
    "function_id" INTEGER NOT NULL REFERENCES "antistasi_function_tbl" ("id"),
    "called_by_id" INTEGER REFERENCES "antistasi_function_tbl" ("id"),
    "message" TEXT NOT NULL,
    UNIQUE("recorded_at", "server_id", "message")
);