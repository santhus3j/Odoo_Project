{
    'name': 'Restaurant Quantity Analysis',
    'version': '1.0',
    'summary': 'Track ingredient usage and dish sales',
    'category': 'Restaurant',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/ingredient_views.xml',
        'views/dish_views.xml',
        'views/analysis_views.xml',
    ],
    'installable': True,
    'application': True,
}
