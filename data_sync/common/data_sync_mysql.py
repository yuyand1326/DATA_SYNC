# -*- coding: utf-8 -*-

from odoo import models


class DataSyncMySql(models.Model):
    _name = 'data.sync.mysql'
    _description = '同步程序(MySQL --> PostgreSQL)'
    _auto = False

    table_data = {}

    def data_sync_task_mysql(self, item):
        """
        数据同步(MySQL --> PostgreSQL)
        """
        # 获取源同步表信息
        origin_table_name = item.origin_table_id.table_name
        # 连接源同步数据库
        _, origin_cursor = self.env['data.sync'].get_connect_by_database_info(item.origin_table_id.database_id)
        # 获取目标同步表信息
        target_table_name = item.target_table_id.table_name
        # 连接目标同步数据库
        target_db, _ = self.env['data.sync'].get_connect_by_database_info(item.target_table_id.database_id)
        # 获取同步目标表需要关联的字段关联关系列表
        field_list = self.env['sync.field.mapping'].search(['&', ('sync_table_id', '=', item.id),
                                                            ('status', '=', True)])
        # 获取唯一字段和最后更新时间索引
        unique_and_last_time_index = self.get_unique_and_last_time_index(field_list)
        data_flag = True  # 数据存在标签
        while data_flag:
            # 查询是否存在待同步数据
            datas = self.get_origin_data(unique_and_last_time_index, origin_cursor,
                                         origin_table_name, item)
            if datas:
                # 新增或更新数据
                data_flag = self.data_insert_or_update_task(datas, target_db, target_table_name,
                                                            item, field_list,
                                                            unique_and_last_time_index)
            else:
                data_flag = False

    @staticmethod
    def get_unique_and_last_time_index(field_list):
        """
        唯一标识字段映射列表和最后更新时间字段下标索引
        """
        last_time_index = 0  # 最后更新时间字段下标索引
        last_time_name = ''  # 最后更新时间字段名称
        unique_field = []
        origin_base_field_list = []
        origin_unique_field_list = []
        target_base_field_list = []
        target_unique_field_list = []
        placeholder_list = []
        for index, field in enumerate(field_list):
            # 获取唯一标识字段
            if field.unique_identify:
                unique_field.append((field.origin_field, field.target_field))
                origin_unique_field_list.append(field.origin_field)
                target_unique_field_list.append(field.target_field)
            else:
                origin_base_field_list.append(field.origin_field)
                target_base_field_list.append(field.target_field)
            placeholder_list.append('%s')
            if field.date_node:
                last_time_index = index - len(unique_field)
                last_time_name = field.origin_field
        # 源表字段列表
        origin_field_list = origin_base_field_list + origin_unique_field_list
        # 目标表字段列表
        target_field_list = target_base_field_list + target_unique_field_list
        return dict(unique_field=unique_field,
                    last_time_index=last_time_index,
                    origin_field_list=origin_field_list,
                    target_field_list=target_field_list,
                    placeholder_list=placeholder_list,
                    last_time_name=last_time_name)

    def get_origin_data(self, unique_and_last_time_index, origin_cursor, origin_table_name, item):
        """
        校验源表是否存在待同步数据
        """
        last_time_name = unique_and_last_time_index.get('last_time_name')
        sql_select = """
                       select %s from %s
                       where %s >= %%s and %s <=%%s
                       order by %s ASC limit 1000
        """ % (', '.join(unique_and_last_time_index.get('origin_field_list')), origin_table_name,
               last_time_name, last_time_name, last_time_name)
        origin_cursor.execute(sql_select, (item.last_sync_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                           item.end_sync_time.strftime("%Y-%m-%d %H:%M:%S.%f")))
        datas = self.env[self.env['database.connect.type'].get_connect_type(
            item.origin_table_id.database_id.database_type)].get_datas(origin_cursor)
        return datas

    def data_insert_or_update_task(self, datas, target_db, target_table_name, item, field_list,
                                   unique_and_last_time_index):
        """
        数据插入和更新
        """
        unique_field = unique_and_last_time_index.get('unique_field')
        target_field_list = unique_and_last_time_index.get('target_field_list')
        target_cursor = target_db.cursor()
        count = 0
        for data in datas:
            count += 1
            # 获取目标表数据
            target_data, limit, limit_data = self.select_target_data(target_cursor, data,
                                                                     unique_field,
                                                                     target_table_name, item)
            if target_data is not None:
                # 目标表数据存在，则更新
                self.data_update_task(target_db, field_list, target_table_name, limit,
                                      data + tuple(limit_data))
            else:
                # 不存在，则新增
                field_table = (target_table_name,
                               ', '.join(target_field_list),
                               ', '.join(unique_and_last_time_index.get('placeholder_list')))
                self.data_insert_task(target_db, target_cursor, field_table, data)
            target_data_dict = dict(zip(target_field_list, list(data)))
            # 同步主外键关联
            self.data_sync_key_link(target_db, target_table_name, item.id,
                                    limit, limit_data, target_data_dict)
            if count == len(datas):
                # 更新最后同步时间
                self.update_last_sync_time(data, unique_and_last_time_index, item.id)
                if len(datas) < 1000:
                    return False
        return True

    def select_target_data(self, target_cursor, data, unique_field, target_table_name, item):
        """
        唯一标识字段 where 条件拼接
        """
        limit = []
        limit_data = []
        for j in range(len(data) - len(unique_field), len(data)):
            limit.append(unique_field[j - len(data) + len(unique_field)][1] + " = %s")
            limit_data.append(data[j])
        limit_str = ' and '.join(limit)
        sql_select_unique = "select id from %s where %s " % (target_table_name, limit_str)
        target_cursor.execute(sql_select_unique, tuple(limit_data))
        target_data = self.env[self.env['database.connect.type'].get_connect_type(
            item.target_table_id.database_id.database_type)].get_data(target_cursor)
        return target_data, limit_str, limit_data

    @staticmethod
    def data_update_task(target_db, field_list, target_table_name, limit, data):
        """
        数据更新
        """
        sql_set = []
        sql_set_unique = []
        target_cursor = target_db.cursor()
        # 更新语句字段拼接
        for field in field_list:
            if field.unique_identify:
                sql_set_unique.append(field.target_field + " = %s ")
            else:
                sql_set.append(field.target_field + " = %s ")
        # 更新语句
        sql_set.extend(sql_set_unique)
        sql_update = 'update %s set %s where %s ' % (target_table_name, ','.join(sql_set), limit)
        target_cursor.execute(sql_update, data)
        target_db.commit()

    def update_last_sync_time(self, data, unique_and_last_time_index, data_id):
        """
        更新最后同步时间
        """
        last_time_index = unique_and_last_time_index.get('last_time_index')
        update_last_time_sql = """
                update sync_table_mapping set last_sync_time= '%s' where id = %s
                """ % (data[last_time_index].strftime("%Y-%m-%d %H:%M:%S.%f"), data_id)
        self.env.cr.execute(update_last_time_sql)
        self.env.cr.commit()

    @staticmethod
    def data_insert_task(target_db, target_cursor, field_table, data):
        """
        新增数据
        """
        sql_insert = " insert into %s (%s) values (%s)" % field_table
        target_cursor.execute(sql_insert, data)
        target_db.commit()

    def data_sync_key_link(self, target_db, target_table_name, sync_table_id, limit, limit_data,
                           target_data_dict):
        """
        同步目标表主外键关联表
        """
        sync_target_table_key_link = self.env['sync.target.table.key.link'].search(
            ['&', ('sync_table_id', '=', sync_table_id), ('status', '=', True)])
        if sync_target_table_key_link is None:
            return
        target_cursor = target_db.cursor()
        for key_item in sync_target_table_key_link:
            # 获取关联表名称与源外键值
            table_name_key_link = key_item.main_table_id.table_name
            key_data = target_data_dict.get(key_item.origin_fk_field)
            if key_data == '' or key_data is None:
                continue
            # key_data是否存在映射表中
            if table_name_key_link in self.table_data and key_data in self.table_data.get(
                    table_name_key_link):
                # 存在，则更新外键
                self.update_key_by_field(target_db, target_cursor, (target_table_name,
                                                                    key_item.fk_field,
                                                                    str(self.table_data.get(
                                                                        table_name_key_link).get(
                                                                        key_data)),
                                                                    limit), tuple(limit_data))
            else:
                # 不存在，则查询主表主键值
                data_link = self.select_data_by_field(target_cursor,
                                                      (key_item.pk_field, table_name_key_link,
                                                       key_item.origin_pk_field),
                                                      key_data,
                                                      key_item.main_table_id.database_id.database_type)
                if data_link is None:
                    # 主表关联记录不存在，插入外键关联补偿任务表
                    self.insert_compensate_task_info(target_cursor, key_item, target_table_name,
                                                     limit, limit_data)
                    continue
                # 目标同步表外键值更新
                self.update_key_by_field(target_db, target_cursor, (
                          target_table_name, key_item.fk_field, str(data_link[0]), limit), tuple(limit_data))
                if key_item.main_table_id.map_status:
                    # 主表映射状态为True,更新table_data
                    self.update_table_data_dict(table_name_key_link, key_data, data_link)

    @staticmethod
    def update_key_by_field(target_db, target_cursor, field_table, target_value):
        """
        根据动态字段更新子表
        update %s set %s = %s where %s
        """
        update_key_sql = ' update %s set %s = %s where %s' % field_table
        target_cursor.execute(update_key_sql, target_value)
        target_db.commit()

    def select_data_by_field(self, target_cursor, query_params, target_value, database_type):
        """
        根据动态字段查询数据
        select %s from %s where %s = %%s
        """
        select_sql = 'select %s from %s where %s = %%s' % query_params
        target_cursor.execute(select_sql, (target_value,))
        data_key = self.env[
            self.env['database.connect.type'].get_connect_type(database_type)].get_data(
            target_cursor)
        return data_key

    def insert_compensate_task_info(self, target_cursor, key_item, target_table_name, limit,
                                    limit_data):
        """
        主外键关联表补偿任务信息插入
        """
        # 查询从表当前记录id
        sub_table_pk_data = self.select_current_pk_data(target_table_name, limit, limit_data, target_cursor, key_item)
        # 关联任务表从表主键id值
        sub_table_pk_ids = self.get_sub_table_pk_ids(key_item.main_table_id.id, key_item.sub_table_id.id)
        # 判断当前记录是否已在任务表中
        if sub_table_pk_data not in sub_table_pk_ids:
            sql_insert_key_link = """insert into sync_target_table_key_link_task( 
                                  main_table_id, pk_field, origin_pk_field, sub_table_id, fk_field, 
                                  origin_fk_field, sub_table_pk, retry_times, status) 
                                 values ( %s, '%s', '%s', %s, '%s', '%s', %s, %s, %s)""" % (
                key_item.main_table_id.id, key_item.pk_field,
                key_item.origin_pk_field,
                key_item.sub_table_id.id, key_item.fk_field,
                key_item.origin_fk_field,
                sub_table_pk_data[0], 0, True)
            self.env.cr.execute(sql_insert_key_link)
            self.env.cr.commit()

    def update_table_data_dict(self, table_name_key_link, key_data, data_link):
        """
        更新当前table_data
        """
        if table_name_key_link not in self.table_data:
            self.table_data[table_name_key_link] = {key_data: data_link[0]}
        else:
            self.table_data[table_name_key_link][key_data] = data_link[0]

    def select_current_pk_data(self, target_table_name, limit, limit_data, target_cursor, key_item):
        """
        查询当前记录id
        """
        sql_select_key_link = "select id from %s where %s" % (target_table_name, limit)
        target_cursor.execute(sql_select_key_link, tuple(limit_data))
        sub_table_pk_data = self.env[self.env['database.connect.type'].get_connect_type(
            key_item.sub_table_id.database_id.database_type)].get_data(target_cursor)
        return sub_table_pk_data

    @staticmethod
    def update_sub_key_by_id(target_db, target_cursor, target_table_name, item_key, target_value):
        """
        根据id更新子表key
        update %s set %s = %%s where id = %s
        """
        update_sub_key_sql = 'update %s set %s = %%s where id = %s' % \
                             (target_table_name, item_key.fk_field, item_key.sub_table_pk)
        target_cursor.execute(update_sub_key_sql, (target_value,))
        target_db.commit()

    def get_sub_table_pk_ids(self, main_table_id, sub_table_id):
        """
        获取关联任务表中从表主键id值
        """
        data = [()]
        sql = """   select sub_table_pk from sync_target_table_key_link_task 
                    where main_table_id = %s and sub_table_id = %s
         """ % (main_table_id, sub_table_id)
        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()
        if datas is not None:
            return datas
        return data

    def compensate_task(self, group_id, total_group):
        """
        主外键关联表补偿任务
        """
        table_key_link_datas = self.env['sync.target.table.key.link.task'].search(
            [('status', '=', True)], limit=1000)
        if table_key_link_datas is None:
            return
        for item_key in table_key_link_datas:
            if item_key.id % total_group != group_id:
                continue
            # 连接目标同步数据库
            target_db, target_cursor = self.get_connect_by_database_info(
                item_key.sub_table_id.database_id)
            target_table_name = item_key.sub_table_id.table_name
            # 查询从表源外键字段值
            data_key = self.select_data_by_field(target_cursor,
                                                 (item_key.origin_fk_field, target_table_name, 'id'),
                                                 str(item_key.sub_table_pk),
                                                 item_key.sub_table_id.database_id.database_type)
            if data_key is None:
                item_key.status = False
                continue
            self.compensate_task_update(item_key, data_key, target_table_name, target_db)

    def compensate_task_update(self, item_key, data_key, target_table_name, target_db):
        """
        主外键关联表补偿任务更新
        """
        target_cursor = target_db.cursor()
        table_name_key_link = item_key.main_table_id.table_name
        # 判断从表源外键字段值是否存在映射表中
        if table_name_key_link in self.table_data and data_key[0] in self.table_data.get(
                table_name_key_link):
            # 存在，更新子表key
            self.update_sub_key_by_id(target_db, target_cursor, target_table_name, item_key,
                                      self.table_data.get(table_name_key_link).get(data_key[0]))
            item_key.status = False
        else:
            # 不存在，查询主表主键值
            data_pk = self.select_data_by_field(target_cursor,
                                                (item_key.pk_field, table_name_key_link,
                                                 item_key.origin_pk_field),
                                                data_key,
                                                item_key.main_table_id.database_id.database_type)
            if data_pk is not None:
                # 更新子表key
                self.update_sub_key_by_id(target_db, target_cursor, target_table_name, item_key,
                                          data_pk)
                item_key.status = False
                if item_key.main_table_id.map_status:
                    # 主表映射状态为True,更新table_data
                    self.update_table_data_dict(table_name_key_link, data_key[0], data_pk)
        item_key.retry_times += 1