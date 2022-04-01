# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SyncTargetTableKeyLink(models.Model):
    _name = 'sync.target.table.key.link'
    _description = '同步目标表主外键关联表'

    sync_table_id = fields.Many2one('sync.table.mapping', string='同步表映射关系表的主键id')
    main_table_id = fields.Many2one('sync.table.info', string='主表id编号')
    pk_field = fields.Char(string='主键字段名称')  # 自增的主键字段
    origin_pk_field = fields.Char(string='源同步表的主键字段', help='源同步主表主键字段映射字段')
    sub_table_id = fields.Many2one('sync.table.info', string='从表id编号')
    fk_field = fields.Char(string='外键字段名称')  # 将关联的pk_field的值写入该字段
    origin_fk_field = fields.Char(string='源同步表的外键字段', help='源同步从表外键字段映射字段')
    status = fields.Boolean(string='生效状态')  # 1-有效  0-无效
