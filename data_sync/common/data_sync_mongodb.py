# -*- coding: utf-8 -*-

from odoo import models
from bson.objectid import ObjectId
import datetime


class DataSyncMongoDb(models.Model):
    _name = 'data.sync.mongodb'
    _description = '同步程序(MongoDB-->PostgreSQL)'
    _auto = False

    def data_sync_task_mongodb(self, item):
        """
        数据同步(MongoDB-->PostgreSQL)
        """
        # 获取源同步表信息
        origin_table_name = item.origin_table_id.table_name
        # 连接源同步数据库
        origin_db, _ = self.env['data.sync'].get_connect_by_database_info(item.origin_table_id.database_id)
        # 获取目标同步表信息
        target_table_name = item.target_table_id.table_name
        # 连接目标同步数据库
        target_db, _ = self.env['data.sync'].get_connect_by_database_info(item.target_table_id.database_id)
        # 获取同步目标表需要关联的字段关联关系列表
        field_list = self.env['sync.field.mapping'].search(['&', ('sync_table_id', '=', item.id),
                                                            ('status', '=', True)])
        # 获取字段映射字典
        field_map = self.get_unique_mongodb(field_list)
        data_flag = True  # 数据存在标签
        while data_flag:
            # 查询是否存在待同步数据
            datas = self.get_origin_data_mongodb(field_map, origin_db,origin_table_name, item)
            if len(datas) > 0:
                # 新增或更新数据
                data_flag = self.data_insert_or_update_task_mongodb(datas, target_db, target_table_name,
                                                                    item, field_list, field_map)
            else:
                data_flag = False

    @staticmethod
    def get_unique_mongodb(field_list):
        """
        原表和目标表字段映射
        """
        unique_field = []
        origin_base_field_dict = {}
        origin_unique_field_dict = {}
        target_base_field_list = []
        target_unique_field_list = []
        placeholder_list = []  # SQL语句占位符
        field_map_dict = {}  # 字段映射字典
        last_time_name = ''  # 最后更新时间字段名称
        for index, field in enumerate(field_list):
            # 获取唯一标识字段
            if field.unique_identify:
                unique_field.append((field.origin_field, field.target_field))
                origin_unique_field_dict[field.origin_field] = 1
                target_unique_field_list.append(field.target_field)
            else:
                origin_base_field_dict[field.origin_field] = 1
                target_base_field_list.append(field.target_field)
            # SQL语句占位符
            placeholder_list.append('%s')
            # 字段映射字典
            field_map_dict[field.target_field] = field.origin_field
            if field.date_node:
                last_time_name = field.origin_field
        # 源表字段列表
        origin_unique_field_dict.update(origin_base_field_dict)
        # 目标表字段列表
        target_field_list = target_unique_field_list + target_base_field_list
        return dict(unique_field=unique_field,
                    origin_field_dict=origin_base_field_dict,
                    target_field_list=target_field_list,
                    placeholder_list=placeholder_list,
                    field_map_dict=field_map_dict,
                    last_time_name=last_time_name)

    def get_origin_data_mongodb(self, field_map, origin_db, origin_table_name, item):
        """
        校验源表是否存在待同步数据
        """
        last_time_name = field_map.get('last_time_name')
        datas = origin_db[origin_table_name].aggregate([
            {
                "$match": {"$and": [{last_time_name: {"$gte": item.last_sync_time}},
                                    {last_time_name: {"$lte": item.end_sync_time}}]}

            },
            {
                '$sort': {last_time_name: 1}
            },
            {
                '$project': field_map.get('origin_field_dict')
            },
            {
                '$limit': 1000
            }
        ])
        origin_datas = [data for data in datas]
        return origin_datas

    def data_insert_or_update_task_mongodb(self, datas, target_db, target_table_name, item, field_list, field_map):
        """
        数据插入和更新
        """
        unique_field = field_map.get('unique_field')
        target_field_list = field_map.get('target_field_list')
        target_cursor = target_db.cursor()
        count = 0
        for data in datas:
            count += 1
            # 获取目标表数据
            target_data, limit, limit_data = self.select_target_data_mongodb(target_cursor, data,
                                                                             unique_field, target_table_name, item)
            if target_data is not None:
                # 目标表数据存在，则更新
                self.data_update_task_mongodb(target_db, field_list, target_table_name, limit, data, tuple(limit_data))
            else:
                # 不存在，则新增
                field_table = (target_table_name,
                               ', '.join(target_field_list),
                               ', '.join(field_map.get('placeholder_list')))
                self.data_insert_task_mongodb(target_db, target_cursor, field_table, data, field_map)
            if count == len(datas):
                # 更新最后同步时间
                self.update_last_sync_time_mongodb(data, item.id, field_map)
                if len(datas) < 1000:
                    return False
        return True

    def select_target_data_mongodb(self, target_cursor, data, unique_field, target_table_name, item):
        """
        唯一标识字段 where 条件拼接
        """
        limit = []
        limit_data = []
        for j in range(len(unique_field)):
            limit.append(unique_field[j][1] + " = %s")
            limit_data.append(str(data.get(unique_field[j][0])))
        limit_str = ' and '.join(limit)
        sql_select_unique = "select id from %s where %s " % (target_table_name, limit_str)
        target_cursor.execute(sql_select_unique, tuple(limit_data))
        target_data = self.env[self.env['database.connect.type'].get_connect_type(
            item.target_table_id.database_id.database_type)].get_data(target_cursor)
        return target_data, limit_str, limit_data

    @staticmethod
    def data_update_task_mongodb(target_db, field_list, target_table_name, limit, data, limit_data):
        """
        数据更新
        """
        sql_set = []
        sql_set_unique = []
        target_cursor = target_db.cursor()
        limit_unique_datas = []
        limit_base_datas = []
        # 更新语句字段拼接
        for field in field_list:
            if field.unique_identify:
                sql_set_unique.append(field.target_field + " = %s ")
                limit_unique_datas.append(str(data.get(field.origin_field)))
            else:
                sql_set.append(field.target_field + " = %s ")
                if (isinstance(data.get(field.origin_field), (datetime.datetime, bool))
                        or data.get(field.origin_field) is None):
                    limit_base_datas.append(data.get(field.origin_field))
                else:
                    limit_base_datas.append(str(data.get(field.origin_field)))
        # 更新语句
        sql_set_unique.extend(sql_set)
        sql_update = 'update %s set %s where %s ' % (target_table_name, ','.join(sql_set_unique), limit)
        target_cursor.execute(sql_update, tuple(limit_unique_datas + limit_base_datas) + limit_data)
        target_db.commit()

    @staticmethod
    def data_insert_task_mongodb(target_db, target_cursor, field_table, data, field_map):
        """
        新增数据
        """
        insert_data = []
        for target_field in field_map.get('target_field_list'):
            origin_field = field_map.get('field_map_dict').get(target_field)
            if (isinstance(data.get(origin_field), (datetime.datetime, bool))
                    or data.get(origin_field) is None):
                insert_data.append(data.get(origin_field))
            else:
                insert_data.append(str(data.get(origin_field)))

        sql_insert = " insert into %s (%s) values (%s)" % field_table
        target_cursor.execute(sql_insert, tuple(insert_data))
        target_db.commit()

    def update_last_sync_time_mongodb(self, data, data_id, field_map):
        """
        更新最后同步时间
        """
        update_last_time_sql = """
                   update sync_table_mapping set last_sync_time= '%s' where id = %s
                   """ % (data.get(field_map.get('last_time_name')).strftime("%Y-%m-%d %H:%M:%S.%f"), data_id)
        self.env.cr.execute(update_last_time_sql)
        self.env.cr.commit()




