INSERT
    OR REPLACE INTO "cog_categories_tbl" ("id", "name")
VALUES (
        (
            SELECT "id"
            FROM "cog_categories_tbl"
            WHERE "name" = ?
        ),
        ?
    )