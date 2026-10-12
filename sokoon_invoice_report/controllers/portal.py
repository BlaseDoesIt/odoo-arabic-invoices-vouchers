# -*- coding: utf-8 -*-
from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.account.controllers.portal import PortalAccount


class SokoonPortalAccount(PortalAccount):

    @http.route()
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        """Render the portal invoice with the Sokoon template.

        ``Preview`` and ``Share`` both land on ``/my/invoices/<id>``; the page
        embeds itself again with ``report_type=html``. Standard Odoo resolves
        that render to ``partner.invoice_template_pdf_report_id`` or, when the
        partner carries none, to the hard-coded ``account.account_invoices`` -
        which on this database is the Studio-customised journal-entry listing,
        i.e. the "wrong report" the user sees.

        Only that hard-coded fallback is replaced here. A template explicitly
        set on the partner still wins, and every other branch of the standard
        controller (the posted-invoice legal-document download, the access
        redirect, the portal page itself) is left to ``super()``.
        """
        if report_type not in ('html', 'pdf', 'text'):
            return super().portal_my_invoice_detail(
                invoice_id, access_token=access_token, report_type=report_type,
                download=download, **kw,
            )

        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # sudo: the portal route is public, and resolving an xml id reads
        # ir.model.data / ir.actions.report.
        sokoon_report = request.env.ref(
            'sokoon_invoice_report.action_report_invoice_sokoon', raise_if_not_found=False,
        ).sudo()
        # The posted-invoice download returns the stored legal attachment, not a
        # fresh render - leave it to super(). Same for a partner-set template.
        if (
            not sokoon_report
            or (report_type == 'pdf' and download and invoice_sudo.state == 'posted')
            or invoice_sudo.partner_id.invoice_template_pdf_report_id
            or not invoice_sudo._is_action_report_available(sokoon_report)
        ):
            return super().portal_my_invoice_detail(
                invoice_id, access_token=access_token, report_type=report_type,
                download=download, **kw,
            )

        # Mirrors the standard controller: a draft invoice prints as a Pro Forma.
        request.update_context(proforma_invoice=not invoice_sudo.invoice_pdf_report_id)
        return self._show_report(
            model=invoice_sudo,
            report_type=report_type,
            report_ref=sokoon_report.report_name,
            download=download,
        )
