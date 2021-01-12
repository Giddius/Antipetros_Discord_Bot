SELECT "link_name",
    "link",
    "author"
FROM "saved_links_tbl"
    INNER JOIN "author_tbl" on author_tbl.id = saved_links_tbl.author_id
WHERE "link_name" = ?