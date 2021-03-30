INSERT
    OR IGNORE INTO "cogs_tbl" (
        "name",
        "config_name",
        "description",
        "category_id",
        "relative_path",
        "enabled"
    )
VALUES (
        ?,
        ?,
        ?,
        (
            SELECT "id"
            FROM "category_tbl"
            WHERE "name" = ?
        ),
        ?,
        ?
    )