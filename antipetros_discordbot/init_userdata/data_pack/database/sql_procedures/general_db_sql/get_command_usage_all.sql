SELECT "name"
FROM command_usage_tbl
    INNER JOIN commands_tbl ON commands_tbl.id = command_usage_tbl.command_id