# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _get_default_pdf_report_id(self, move):
        """Print the Sokoon invoice instead of the stock ``Invoice PDF``.

        Standard Odoo falls back to ``account.account_invoices`` when neither
        the partner nor the journal carries an ``invoice_template_pdf_report_id``.
        That fallback is what the Send & Print flow bakes into
        ``invoice_pdf_report_id`` at posting time, and that stored attachment is
        what Preview / Share hand back afterwards - so leaving the fallback
        alone means every invoice keeps a stock (Studio-mangled) PDF attached
        no matter what is printed manually.

        An explicit template set on the partner or the journal still wins; only
        the last-resort fallback is redirected.
        """
        report = super()._get_default_pdf_report_id(move)
        if report != self.env.ref('account.account_invoices', raise_if_not_found=False):
            return report
        sokoon_report = self.env.ref(
            'sokoon_invoice_report.action_report_invoice_sokoon', raise_if_not_found=False,
        )
        if sokoon_report and move._is_action_report_available(sokoon_report):
            return sokoon_report
        return report
