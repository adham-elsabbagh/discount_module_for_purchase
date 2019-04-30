from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """

        for order in self:
            amount_untaxed = amount_tax = amount_discount=price_total_without_disc = discount=0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                # price = line._get_discounted_price_unit()
                # print (price)
                amount_discount += (line.product_qty * line.price_unit * line.discount) / 100
                price_total_without_disc += amount_untaxed + amount_discount

            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_discount': order.currency_id.round(amount_discount),
                'amount_total': amount_untaxed + amount_tax,
                'price_total_without_disc': amount_untaxed + amount_discount
            })



    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount type',
                                     readonly=True,
                                     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     default='percent')
    discount_rate = fields.Float('Discount Rate', digits_compute=dp.get_precision('Account'),
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_amount_all',
                                      digits_compute=dp.get_precision('Account'), track_visibility='always')
    price_total_without_disc = fields.Float(string='Price Total', digits=(16, 2),
                                            digits_compute=dp.get_precision('Account'), compute='_amount_all',track_visibility='always')
    discount = fields.Float(
        string='Discount (%)', digits=dp.get_precision('Discount'),readonly=True,store=True,)


    @api.onchange('discount_type', 'discount_rate', 'order_line.discount')
    def supply_rate(self):
        for order in self:
            if order.discount_type == 'percent':
                for line in order.order_line:
                    line.discount = order.discount_rate

            else:
                total = discount = 0.0
                for line in order.order_line:
                    total += round((line.product_qty * line.price_unit))
                if order.discount_rate != 0:
                    discount = (order.discount_rate / total) * 100
                else:
                    discount = order.discount_rate
                for line in order.order_line:
                    line.discount = discount

    @api.multi
    def _prepare_invoice(self, ):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate
        })
        return invoice_vals

    @api.multi
    def button_dummy(self):
        self.supply_rate()
        return True


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Discount %')

    @api.one
    @api.depends('product_qty', 'price_unit', 'taxes_id','discount')
    def _compute_amount(self):
        for line in self:
            # prev_discount = line.discount
            quantity = line.product_qty
            price_total_without_disc = line.price_unit * quantity

            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            if line.discount:
                discount = (line.price_unit * line.discount * line.product_qty)/100
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'] ,
                    'price_subtotal': taxes['total_excluded'] - discount,
                    'price_total_without_disc': price_total_without_disc,
                })
            else:
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                    'price_total_without_disc': price_total_without_disc,

                })
    price_total_without_disc = fields.Float(string='Price Total', digits=(16, 2), default=0.0,compute='_compute_amount')



    _sql_constraints = [
        ('discount_limit', 'CHECK (discount <= 100.0)',
         'Discount must be lower than 100%.'),
    ]


    def _get_discounted_price_unit(self):
        """Inheritable method for getting the unit price after applying
        discount(s).

        :rtype: float
        :return: Unit price after discount(s).
        """
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit

    @api.multi
    def _get_stock_move_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.
        """
        price_unit = False
        price = self._get_discounted_price_unit()
        if price != self.price_unit:
            # Only change value if it's different
            price_unit = self.price_unit
            self.price_unit = price
        price = super(purchase_order_line, self)._get_stock_move_price_unit()
        if price_unit:
            self.price_unit = price_unit
        return price
