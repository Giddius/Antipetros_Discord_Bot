UPDATE suggestion_tbl
SET category_id = (
        SELECT "id"
        FROM "category_tbl"
        WHERE "name" = ?
    )
WHERE "message_discord_id" = ?