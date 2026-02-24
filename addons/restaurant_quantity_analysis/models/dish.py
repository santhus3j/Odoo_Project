"""Models for dishes and the ingredients required by each dish.

This module defines two simple models:
- `RestaurantDish`: represents a menu dish and its ingredient lines.
- `DishIngredient`: a line linking a dish to an ingredient and the
  quantity of that ingredient required to prepare a single unit of the dish.

Keeping these models minimal keeps the example focused on quantity
calculations performed elsewhere (sales processing / analysis).
"""

from odoo import models, fields


class RestaurantDish(models.Model):
    _name = 'restaurant.dish'
    _description = 'Restaurant Dish'

    # Human readable name of the dish
    name = fields.Char(string="Dish Name", required=True)

    # One2many of ingredient lines for this dish. Each line specifies
    # which ingredient is used and how much (in kg) is required per dish.
    ingredient_ids = fields.One2many(
        'restaurant.dish.ingredient',
        'dish_id',
        string="Ingredients"
    )


class DishIngredient(models.Model):
    _name = 'restaurant.dish.ingredient'
    _description = 'Dish Ingredient'

    # The parent dish for this ingredient line. Deleting the dish
    # will cascade and remove related ingredient lines.
    dish_id = fields.Many2one('restaurant.dish', ondelete='cascade')

    # Link to the ingredient record being consumed
    ingredient_id = fields.Many2one('restaurant.ingredient', required=True)

    # Amount (in kg) of the linked ingredient required to produce
    # a single unit of the dish. Used by sales processing to deduct
    # stock when a sale is recorded.
    quantity_required = fields.Float(string="Quantity per Dish (kg)")
