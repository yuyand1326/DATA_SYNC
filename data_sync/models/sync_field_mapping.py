# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SyncFieldMapping(models.Model):
    _name = 'sync.field.mapping'
    _description = '同步字段映射关系表'

    sync_table_id = fields.Many2one('sync.table.mapping', string='同步表映射关系表的主键id')
    origin_table = fields.Char(related="sync_table_id.origin_table_id.table_name", string='源同步表名称')
    origin_field = fields.Char(string='源同步表字段名称')
    origin_field_type = fields.Char(string='源同步表字段类型')
    origin_field_description = fields.Char(string='源字段描述')
    target_table = fields.Char(related="sync_table_id.target_table_id.table_name", string='目标同步表名称')
    target_field = fields.Char(string='目标同步表字段名称')
    target_field_type = fields.Char(string='目标同步表字段类型')
    target_field_description = fields.Char(string='目标字段描述')
    unique_identify = fields.Boolean(string='唯一标识')  # 用于判断数据是否存在
    status = fields.Boolean(string='生效状态')  # 1-有效  0-无效
    date_node = fields.Boolean(string='最后更新时间字段')
