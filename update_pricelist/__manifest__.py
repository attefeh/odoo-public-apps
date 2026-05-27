{
    'name' : 'Update Pricelist',
    'version': '1.0',
    'category': 'Sale',
    'description': "Update pricelist by fixed amount or percentage",
    "author": "Attefeh Falah",
    "website": "https://www.attefehfalah.com",
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/update_pricelist_item_views.xml',
        'views/product_pricelist_views.xml',
        'views/product_product_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
