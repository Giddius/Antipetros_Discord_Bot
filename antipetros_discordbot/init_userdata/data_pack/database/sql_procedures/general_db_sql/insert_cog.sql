INSERT
    OR REPLACE INTO "cogs_tbl" (
        "id",
        "name",
        "config_name",
        "description",
        "cog_category_id",
        "relative_path"
    )
VALUES (
        (
            SELECT "id"
            FROM "cogs_tbl"
            WHERE "name" = ?
        ),
        ?,
        ?,
        ?,
        (
            SELECT "id"
            FROM "cog_categories_tbl"
            WHERE "name" = ?
        ),
        ?
    )