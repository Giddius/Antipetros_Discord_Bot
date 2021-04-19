INSERT
    OR IGNORE INTO "command_usage_tbl" (
        "timestamp",
        "command_id"
    )
VALUES (
        ?,
        (
            SELECT "id"
            FROM "commands_tbl"
            WHERE "name" = ?
        )
    )