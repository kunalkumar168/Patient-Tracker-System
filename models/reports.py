import sqlite3
from flask import *
import bcrypt

class ReportFile:
    def __init__(self):
        self.conn = sqlite3.connect('./healthdb.db')
        self.cur = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS report (report_id TEXT PRIMARY KEY, patient_email TEXT, doctor_email TEXT, report_name TEXT, file_path TEXT)')
        self.conn.commit()

    def get_id(self):
        self.cur.execute('SELECT MAX(report_id) FROM report;')
        result = self.cur.fetchone()[0]
        return str(int(result)+1) if result else 1

    def create(self, patient_email, doctor_email, report_name, file_path):
        report_id = self.get_id()
        self.cur.execute('INSERT INTO report VALUES (?,?,?,?,?)', (report_id, patient_email, doctor_email, report_name, file_path))
        self.conn.commit()