# -*- coding: utf-8 -*-
{
    'name': "data_sync",
    'sequence': 3,

    'summary': """
        数据同步模块""",

    'description': """
        数据同步(MongoDB --> PostgreSQL)
    """,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/sync_database_info.xml',
        'views/sync_target_table_key_link.xml',
        'views/sync_target_table_key_link_task.xml',
        'views/data_sync_scheduler.xml',
        'views/sync_table_info_view.xml',
        'views/sync_table_mapping_view.xml',
        'views/sync_field_mapping_view.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
