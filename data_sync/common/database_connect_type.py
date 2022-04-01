# -*- coding: utf-8 -*-

from odoo import models, fields


class MySQL(models.Model):
    _name = 'database.connect.type'
    _description = '数据库连接类型映射'
    _auto = False

    def get_connect_type(self, database_type):
        connect_type = {
            '0': 'mysql.connect',
            '1': 'postgresql.connect',
            '2': 'mongodb.connect',
        }
        return connect_type.get(database_type, 'postgresql.connect')
