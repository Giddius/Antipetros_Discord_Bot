SELECT a.id,
    a.name,
    a.utc_posted_time,
    a.utc_saved_time,
    a.upvotes,
    a.downvotes,
    a.link_to_message,
    e.name AS category_name,
    b.name AS author_name,
    c.name AS setter_name,
    a.content,
    d.name AS data_name,
    d.location AS data_location
FROM suggestion_tbl a
    JOIN author_tbl b ON b.id = a.author_id
    JOIN author_tbl c ON c.id = a.added_by_author_id
    LEFT JOIN category_tbl e ON e.id = a.category_id
    LEFT JOIN extra_data_tbl d ON d.id = a.extra_data_id
WHERE a.discussed = 0