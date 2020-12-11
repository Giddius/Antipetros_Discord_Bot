SELECT a.message_discord_id,
    a.name,
    a.utc_posted_time,
    b.name AS author_name,
    a.content,
    d.name AS data_name
FROM suggestion_tbl a
    JOIN author_tbl b ON b.id = a.author_id
    JOIN author_tbl c ON c.id = a.added_by_author_id
    LEFT JOIN category_tbl e ON e.id = a.category_id
    LEFT JOIN extra_data_tbl d ON d.id = a.extra_data_id
WHERE a."message_discord_id" = ?