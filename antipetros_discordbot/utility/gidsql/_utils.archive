
   def vacuum(self):
        self("VACUUM")
        log.info("finished VACUUM the DB")

    def dump_sql(self):  # sourcery skip: list-comprehension
        _out = []
        con = sqlite.connect(self.db_loc, isolation_level=None, detect_types=sqlite.PARSE_DECLTYPES)
        for line in con.iterdump():
            _out.append(line)
        con.close()
        return _out
