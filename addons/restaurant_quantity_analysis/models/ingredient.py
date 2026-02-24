"""Ingredient model used to track available quantities.

This model stores the ingredient name, current available quantity
in kilograms and a minimum threshold that can be used for alerts
or reordering logic.
"""

from odoo import models, fields


class RestaurantIngredient(models.Model):
    _name = 'restaurant.ingredient'
    _description = 'Restaurant Ingredient'

    # Ingredient display name
    name = fields.Char(string="Ingredient Name", required=True)

    # How much of this ingredient is currently on hand (kg)
    quantity_available = fields.Float(string="Available Quantity (kg)")

    # Threshold for when stock is considered low (business logic can
    # compare this to `quantity_available` to trigger alerts/reorders)
    minimum_quantity = fields.Float(string="Minimum Threshold")
