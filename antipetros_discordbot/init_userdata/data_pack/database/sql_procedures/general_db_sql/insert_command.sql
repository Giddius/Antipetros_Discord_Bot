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
        "hidden",
        "image_id"
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
        ?,
        (
            SELECT "id"
            from "images_tbl"
            WHERE "name" = ?
        )
    )