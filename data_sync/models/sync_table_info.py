# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SyncTableInfo(models.Model):
    _name = 'sync.table.info'
    _description = '同步表信息'
    _rec_name = 'table_name'

    database_id = fields.Many2one('sync.database.info', string='数据库主键id')
    table_name = fields.Char(string='同步表名称')
    status = fields.Boolean(string='生效状态')  # 1-有效  0-无效
    map_status = fields.Boolean(string='映射状态')  # 是否形成映射表
    table_description = fields.Char(string='表描述')
    database_description = fields.Char(related="database_id.database_description", string='数据库描述')
