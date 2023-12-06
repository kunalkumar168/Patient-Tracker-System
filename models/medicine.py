import sqlite3
from flask import *
import bcrypt

class Medicine:
    def __init__(self):
        self.conn = sqlite3.connect('./healthdb.db')
        self.cur = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS medicines (name TEXT PRIMARY KEY, mfg_date TEXT, exp_date TEXT, description TEXT)')
        self.conn.commit()

    def create(self, name, mfg_date, exp_date, description):
        self.cur.execute('INSERT INTO medicines VALUES (?,?,?,?,?)', (name, mfg_date, exp_date, description) )
        self.conn.commit()