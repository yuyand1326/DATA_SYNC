# -*- coding: utf-8 -*-

import pymongo
from odoo import models, fields


class MongoDBConnect(models.Model):
    _name = 'mongodb.connect'
    _description = 'MongoDB数据库连接'
    _auto = False

    def database_connect(self, database_id):
        """
         mongodb 连接
        """
        client = pymongo.MongoClient(host=database_id.server_host,
                                     port=database_id.server_port,
                                     username=database_id.user,
                                     password=database_id.password,
                                     )
        db = client[database_id.database_name]
        return db

    # def get_datas(self, cr):
    #     """
    #     获取多条数据
    #     """
    #     datas = cr.fetchall()
    #     return datas
    #
    # def get_data(self, cr):
    #     """
    #     获取单条数据
    #     """
    #     data = cr.fetchone()
    #     return data
