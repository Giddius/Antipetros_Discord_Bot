INSERT
    OR IGNORE INTO "author_tbl" (
        "name",
        "display_name",
        "discord_id",
        "is_member"
    )
VALUES (?, ?, ?, ?)