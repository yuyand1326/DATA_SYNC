# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SyncTableMapping(models.Model):
    _name = 'sync.table.mapping'
    _description = '同步表映射关系表'
    _order = 'sequence'
    _rec_name = 'target_table_description'

    origin_table_id = fields.Many2one('sync.table.info', string='源同步表的主键id')
    origin_table_description = fields.Char(related="origin_table_id.table_description", string='源同步表描述')
    target_table_id = fields.Many2one('sync.table.info', string='目标同步表的主键id')
    target_table_description = fields.Char(related="target_table_id.table_description", string='目标同步表描述')
    sequence = fields.Integer(string='同步顺序')  # 基础表（1 - 99），主表（100 - 999），从表（1000 - 9999）
    last_sync_time = fields.Datetime(string='开始同步时间', help="最后一条同步数据的最后更新时间")  # 最后一条同步数据的最后更新时间（last_modified_time）
    end_sync_time = fields.Datetime(string='结束同步时间', default=fields.Datetime.now)
    status = fields.Boolean(string='生效状态')  # 1-有效  0-无效
    group_id = fields.Integer(string='分组', default=1)

    sync_fields_ids = fields.One2many('sync.field.mapping', 'sync_table_id', string='同步字段列表')

    def name_get(self):
        res = []
        display_name = ''
        for item in self:
            if item.origin_table_id and item.target_table_id:
                display_name = "%s ---> %s" % (item.origin_table_description, item.target_table_description)
            res.append((item.id, display_name))
        return res
