# -*- coding: utf-8 -*-

import psycopg2
from odoo import models, fields


class PostgreSQLConnect(models.Model):
    _name = 'postgresql.connect'
    _description = 'PostgreSQL数据库连接'
    _auto = False

    def database_connect(self, database_id):
        """
        postgresql 连接
        """
        db = psycopg2.connect(host=database_id.server_host,
                              port=database_id.server_port,
                              user=database_id.user,
                              password=database_id.password,
                              database=database_id.database_name)
        return db

    def get_datas(self, cr):
        """
        获取多条数据
        """
        datas = cr.fetchall()
        return datas

    def get_data(self, cr):
        """
        获取单条数据
        """
        data = cr.fetchone()
        return data
