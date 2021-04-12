INSERT
    OR IGNORE INTO "text_channels_tbl" (
        "id",
        "name",
        "position",
        "created_at",
        "category_id",
        "topic"
    )
VALUES (?, ?, ?, ?, ?, ?)