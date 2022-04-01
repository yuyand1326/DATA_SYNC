# -*- coding: utf-8 -*-

from odoo import models
import datetime


class DataSync(models.Model):
    _name = 'data.sync'
    _description = '同步程序'
    _auto = False

    table_data = {}

    def data_sync_task(self, group_id):
        """
        数据同步主任务
        """
        sync_table_mapping_data = self.env['sync.table.mapping'].search(
            ['&', ('status', '=', True), ('group_id', '=', group_id)], order='sequence ASC')
        if sync_table_mapping_data is None:
            return
        for item in sync_table_mapping_data:
            self.select_database_type(item)

    def select_database_type(self, item):
        """
        通过数据库类型选择对应的同步方法
        """
        database_type = {
            '0': self.env['data.sync.mysql'].data_sync_task_mysql,
            '1': None,
            '2': self.env['data.sync.mongodb'].data_sync_task_mongodb
        }
        method = database_type.get(item.origin_table_id.database_id.database_type, None)
        if (method and item.origin_table_id.status and item.origin_table_id.status
                and item.origin_table_id.database_id.status
                and item.target_table_id.database_id.status):
            method(item)
        else:
            return

    def get_connect_by_database_info(self, database_info):
        """
        根据数据库信息获取连接
        """
        connect_type = self.env['database.connect.type'].get_connect_type(database_info.database_type)
        db = self.env[connect_type].database_connect(database_info)
        cursor = None
        if database_info.database_type != '2':
            cursor = db.cursor()
        return db, cursor

