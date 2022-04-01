# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SyncTableInfo(models.Model):
    _name = 'sync.database.info'
    _description = '同步数据库信息'
    _rec_name = 'database_name'

    DATABASE_TYPE = [('0', 'MySQL'), ('1', 'PostgreSQL'), ('2', 'MongoDB')]

    database_name = fields.Char(string='数据库名称')
    server_host = fields.Char(string='数据库主机')  # ip地址
    server_port = fields.Integer(string='端口号')
    user = fields.Char(string='数据库登录用户名')
    password = fields.Char(string='数据库登录密码')
    status = fields.Boolean(string='生效状态')
    database_description = fields.Char(string='数据库描述')
    database_type = fields.Selection(DATABASE_TYPE, string='数据库类型')

    def read(self, fields=None, load='_classic_read'):
        datas = super().read(fields=fields, load=load)
        for data in datas:
            if data.get('password'):
                data['password'] = '******'
        return datas
