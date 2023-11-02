import sqlite3
from flask import *
import bcrypt

conn = sqlite3.connect('./healthdb.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS medicines (name TEXT PRIMARY KEY, mfg_date TEXT, exp_date TEXT, description TEXT)')
conn.commit()

#creates the patient
def create(id, name, mfg_date, exp_date, description):
    cur.execute('INSERT INTO medicines VALUES (?,?,?,?,?)', (name, mfg_date, exp_date, description) )
    conn.commit()