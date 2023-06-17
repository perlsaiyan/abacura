import sqlite3
from datetime import datetime
from abacura.mud import OutputMessage


class RingBufferLogSql:
    def __init__(self, db_filename: str, ring_size: int = 10000, wal: bool = True, commit_interval: int = 100):
        self.db_filename = db_filename
        self.ring_size = ring_size
        self.commit_interval = commit_interval
        self.conn = sqlite3.connect(db_filename)
        self.rows_logged = 0

        if wal:
            self.conn.execute("PRAGMA journal_mode=WAL")

        # sql = "drop table if exists log_ring"
        # self.conn.execute(sql)
        sql = "create table if not exists log_ring(ring_number not null primary key, epoch_ns, vnum, message, stripped)"
        self.conn.execute(sql)
        self.conn.execute("create index if not exists log_ring_n1 on log_ring(epoch_ns)")

        self.ring_number = self.get_current_ring_number()

    def get_current_ring_number(self):
        sql = """select ifnull(max(ring_number), 0) 
                   from log_ring 
                  where epoch_ns = (select max(epoch_ns) from log_ring)"""
        cur = self.conn.execute(sql)
        rows = cur.fetchall()
        return rows[0][0] if len(rows) else 0

    def log(self, log_epoch_ns, log_vnum: str, message: OutputMessage):
        if type(message) not in [str, 'str']:
            return

        values = (self.ring_number, log_epoch_ns, log_vnum, message.message, message.stripped)
        self.conn.execute("insert or replace into log_ring values(?, ?, ?, ?, ?)", values)

        self.ring_number = (self.ring_number + 1) % self.ring_size

        self.rows_logged += 1
        if self.rows_logged % self.commit_interval == 0:
            self.conn.commit()

    def query(self, like: str = '', clause: str = '', limit: int = 100, epoch_start: int = 0, grouped: bool = False):
        select = "message, ring_number, epoch_ns, vnum"
        group_by = ""
        if grouped:
            select = "message, max(ring_number), max(epoch_ns), last_value(vnum) over (order by epoch_ns desc)"
            group_by = "group by message"

        sql = """select %s
                   from log_ring
                  where stripped like ?
                    and epoch_ns > ? 
                        %s 
                        %s
                  order by 3 desc 
                  limit ? 
              """ % (select, clause, group_by)
        c = self.conn.execute(sql, (like, epoch_start, limit))
        results = c.fetchall()

        logs = []
        for message, rb, ns, vnum in reversed(results):
            dt: datetime = datetime.fromtimestamp(ns / 1e9)
            dts = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            logs.append((dts, vnum, message))

        return logs

    def commit(self):
        self.conn.commit()

    def checkpoint(self, method: str = 'truncate'):
        self.commit()
        if method.lower() not in ['truncate', 'passive', 'full', 'restart']:
            raise ValueError('Invalid checkpoint method %s' % method)
        self.conn.execute("pragma wal_checkpoint(%s)" % method)
