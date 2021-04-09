SELECT "timestamp",
    "usage_percent",
    "load_average_1",
    "load_average_5",
    "load_average_15"
FROM "cpu_performance_tbl"
WHERE "timestamp" BETWEEN ? AND ?