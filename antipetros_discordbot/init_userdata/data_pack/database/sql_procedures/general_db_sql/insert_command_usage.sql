INSERT
    OR IGNORE INTO "command_usage_tbl" ("command_id")
VALUES (
        (
            SELECT "id"
            FROM "commands_tbl"
            WHERE "name" = ?
        )
    )