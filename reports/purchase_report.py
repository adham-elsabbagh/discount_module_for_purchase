from odoo import api, fields, models, tools
import odoo.addons.decimal_precision as dp

class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    # discount = fields.Float('Discount', readonly=True)

    def _select(self):
        res = super(PurchaseReport,self)._select()
        select_str = res+""",sum(l.product_uom_qty / u.factor * u2.factor * cr.rate * l.price_unit * l.discount / 100.0)
         as discount"""
        return select_str

#new##########################################

    discount = fields.Float(
        string='Discount (%)', digits=dp.get_precision('Discount'),
        group_operator="avg",readonly=True,
    )

    def _select_purchase_discount(self):
        return """
            , l.discount AS discount
            """

    def _group_by_purchase_discount(self):
        return ", l.discount"

    def _get_discounted_price_unit_exp(self):
        """Inheritable method for getting the SQL expression used for
        calculating the unit price with discount(s).

        :rtype: str
        :return: SQL expression for discounted unit price.
        """
        return '(1.0 - COALESCE(l.discount, 0.0) / 100.0) * l.price_unit '

    @api.model_cr
    def init(self):
        """Inject parts in the query with this hack, fetching the query and
        recreating it. Query is returned all in upper case and with final ';'.
        """
        super(PurchaseReport, self).init()
        self._cr.execute("SELECT pg_get_viewdef(%s, true)", (self._table,))
        view_def = self._cr.fetchone()[0]
        if view_def[-1] == ';':  # Remove trailing semicolon
            view_def = view_def[:-1]
        view_def = view_def.replace(
            "FROM purchase_order_line",
            "{} FROM purchase_order_line".format(
                self._select_purchase_discount()
            ),
        )
        view_def += self._group_by_purchase_discount()
        # Replace the expression with space for avoiding to replace in the
        # group by part
        view_def = view_def.replace(
            'l.price_unit ', self._get_discounted_price_unit_exp(),
        )
        # Re-create view
        tools.drop_view_if_exists(self._cr, self._table)
        # pylint: disable=sql-injection
        self._cr.execute("create or replace view {} as ({})".format(
            self._table, view_def,
        ))
