"""Module manifest for Restaurant Quantity Analysis.

This module provides simple models and views to track ingredients,
dishes and sales so you can observe how ingredient quantities are
consumed when sales are recorded.
"""

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
