-- category_tbl definition
CREATE TABLE category_tbl (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    CONSTRAINT category_tbl_name_unique UNIQUE (name)
);
-- cogs_tbl definition
CREATE TABLE cogs_tbl (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    config_name TEXT NOT NULL,
    description TEXT,
    category_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    enabled INTEGER DEFAULT 0 NOT NULL,
    CONSTRAINT cogs_tbl_config_name_unique UNIQUE (config_name),
    CONSTRAINT cogs_tbl_name_unique UNIQUE (name),
    CONSTRAINT cogs_tbl_path_unique UNIQUE (relative_path),
    CONSTRAINT cogs_tbl_FK FOREIGN KEY (category_id) REFERENCES category_tbl(id)
);
CREATE TABLE commands_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "cog_id" INTEGER NOT NULL,
    "help" TEXT,
    "short_doc" TEXT,
    "signature" TEXT,
    "usage" TEXT,
    "enabled" INTEGER DEFAULT 0 NOT NULL,
    "hidden" INTEGER DEFAULT 1 NOT NULL,
    CONSTRAINT cogs_tbl_name_unique UNIQUE (name),
    CONSTRAINT cog_FK FOREIGN KEY ("cog_id") REFERENCES cogs_tbl(id)
);
CREATE TABLE memory_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" DATETIME NOT NULL UNIQUE,
    "memory_in_use" INTEGER NOT NULL
);
CREATE TABLE latency_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" DATETIME NOT NULL UNIQUE,
    "latency" INTEGER NOT NULL
);
CREATE TABLE cpu_performance_tbl (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" DATETIME NOT NULL UNIQUE,
    "usage_percent" INTEGER NOT NULL,
    "load_average_1" INTEGER NOT NULL,
    "load_average_5" INTEGER NOT NULL,
    "load_average_15" INTEGER NOT NULL
)