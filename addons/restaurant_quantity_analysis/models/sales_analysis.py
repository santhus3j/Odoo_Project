"""Sales model and simple stock deduction logic.

`RestaurantSale` captures a sale of a dish and, upon creation,
deducts the calculated amounts of each linked ingredient from the
corresponding `RestaurantIngredient.quantity_available` field.

Note: This example performs direct subtraction on the float field.
In a production system you would usually add checks to prevent
negative stock, use transactions, and possibly move stock logic to
stock-specific classes or use Odoo's stock modules.
"""

from odoo import models, fields, api


class RestaurantSale(models.Model):
    _name = 'restaurant.sale'
    _description = 'Restaurant Sale'

    # Dish sold
    dish_id = fields.Many2one('restaurant.dish', required=True)

    # Number of dish units sold in this sale
    quantity_sold = fields.Integer(string="Quantity Sold")

    # Date of the sale; defaults to today
    sale_date = fields.Date(default=fields.Date.today)

    @api.model
    def create(self, vals):
        """Override create to deduct ingredient quantities when a sale
        record is created.

        This iterates the dish's ingredient lines and reduces the
        corresponding `RestaurantIngredient.quantity_available` by
        (quantity_required * quantity_sold).
        """
        record = super().create(vals)

        # Subtract required quantities from available stock
        for item in record.dish_id.ingredient_ids:
            ingredient = item.ingredient_id
            ingredient.quantity_available -= (
                item.quantity_required * record.quantity_sold
            )

        return record
