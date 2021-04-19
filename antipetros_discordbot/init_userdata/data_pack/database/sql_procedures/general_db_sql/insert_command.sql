INSERT
    OR REPLACE INTO "commands_tbl" (
        "id",
        "name",
        "cog_id",
        "is_group",
        "help",
        "brief",
        "short_doc",
        "usage",
        "signature",
        "example",
        "gif_path",
        "github_link",
        "enabled",
        "hidden"
    )
VALUES (
        (
            SELECT "id"
            FROM "commands_tbl"
            WHERE "name" = ?
        ),
        ?,
        (
            SELECT "id"
            FROM "cogs_tbl"
            WHERE "name" = ?
        ),
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?
    )