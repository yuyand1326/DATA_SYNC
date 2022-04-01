# -*- coding: utf-8 -*-
{
    'name': "data_sync",
    'sequence': 3,

    'summary': """
        Parallel data migration from MySQL to PostgreSQL or MongoDB to PostgreSQL""",

    'description': """
        本模块主要进行MySQL到PostgreSQL以及MongoDB到PostgreSQL的数据平行迁移，以数据的最后更新时间（最后修改时间）作为时间节点，可选择某一区间内的数据进行迁移。
    """,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'price': 9.9,
    'currency': 'USD',
    'also available in version': 'v14.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    'images': [
        'static/images/main_screenshot.png'
    ],

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
    'license': 'LGPL-3',
}
