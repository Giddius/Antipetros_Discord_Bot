INSERT
    OR IGNORE INTO "suggestion_tbl" (
        "name",
        "message_discord_id",
        "author_id",
        "added_by_author_id",
        "utc_posted_time",
        "utc_saved_time",
        "content",
        "link_to_message"
    )
VALUES (
        ?,
        ?,
        (
            SELECT "id"
            FROM "author_tbl"
            WHERE "discord_id" = ?
        ),
        (
            SELECT "id"
            FROM "author_tbl"
            WHERE "discord_id" = ?
        ),
        ?,
        ?,
        ?,
        ?
    )