# -*- coding: utf-8 -*-
{
    'name': 'Sokoon Invoice Report',
    'version': '19.0.4.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Arabic invoice PDF with a fixed "الزبون" customer label',
    'description': """
Sokoon Invoice Report
=====================

Keeps the standard Odoo invoice PDF exactly as it is, with a single change to
the customer block printed at the top left of the page.

Problem
-------
The customer block is rendered by the standard ``contact`` widget, which builds
its output from the address format configured on the partner's country. On this
database that address format contains the literal token ``partner_id.title.name``,
so every printed invoice shows the raw text::

    partner_id.title.name    Customer Name

Fix
---
This module inherits ``account.report_invoice_document`` and replaces the
``<address>`` element of the customer block (all three shipping-address
variants) with an explicit block that prints::

    الزبون    Customer Name

The label is a fixed string, so it no longer depends on the country address
format and the raw ``partner_id.title.name`` token can never leak into the PDF
again. The block is forced to ``dir="ltr"`` / left alignment so the label stays
on the left of the customer name, matching the existing layout.

Everything else in the report - header, logo, invoice title, dates, line table,
taxes, totals, payment communication and footer - is untouched standard Odoo, so
the printed document is otherwise identical to the current one.

Dedicated print entry
---------------------
This database also carries Odoo Studio customisations
(``studio_customization``) on ``account.report_invoice_document``, which turn
the invoice into a journal-entry style listing with ACCOUNT / PARTNER columns
grouped by product category. Studio stores those edits as inherited
``ir.ui.view`` records on the stock template, so every stock print entry - and
any inherited or primary template built on it - renders the Studio layout
instead of the invoice.

The module therefore ships a standalone copy of the Odoo 19.0 stock invoice
document as ``sokoon_invoice_report.sokoon_invoice_document``. It carries no
``inherit_id``, so no Studio view applies to it, and it renders the original
layout exactly as in the company's reference invoice. A Print entry on
invoices exposes it::

    Sokoon Invoice / فاتورة سكون

``print_with_payments`` is left unset, matching the reference PDF.

Always Arabic
-------------
The wrapper forces the document language to Arabic whatever language the
customer is set to, preferring ``ar_SY`` over ``ar_001`` when both are
installed, and falling back to the partner language when no Arabic language is
installed. Both Arabic locales are Right-to-Left in ``res.lang``, so this also
gives the RTL page direction of the reference PDF.

View translations live in each view's own ``arch_db``, so the standalone copy
does not inherit the Arabic shipped with ``account`` and would otherwise print
English labels. ``i18n/ar.po`` carries the 64 terms of the invoice document,
taken from ``addons/account/i18n/ar.po`` (19.0), with "Invoice Date" translated
``تاريخ الفاتورة`` to match the reference invoice. ``get_base_langs()`` reduces both
``ar_001`` and ``ar_SY`` to ``ar``, so the one file covers either locale.

Keeping the copy in sync
------------------------
Being a copy, ``sokoon_invoice_document`` does not follow upstream changes to
the stock invoice report. When upgrading Odoo, re-copy
``account/views/report_invoice.xml`` and re-apply the customer block swap.

Preview / Share / Send & Print
------------------------------
A Print entry alone is not enough: the ``Preview`` and ``Share`` buttons open
the customer portal, and the portal renders
``partner.invoice_template_pdf_report_id`` or - when the partner has none - the
hard-coded ``account.account_invoices``, i.e. the Studio-customised stock
report. Send & Print uses the same fallback and freezes its output into
``invoice_pdf_report_id``, the attachment the portal hands back on download.

Three changes make the Sokoon report the one all of them pick:

* the report action is flagged ``is_invoice_report`` and given the
  ``move_type != entry`` domain, which is what Odoo 19 requires before a report
  may serve as an invoice template at all;
* ``account.move.send._get_default_pdf_report_id`` redirects the
  ``account.account_invoices`` last-resort fallback to it, so newly posted
  invoices attach the Sokoon PDF (a template explicitly set on the partner or
  the journal still wins);
* the portal controller resolves the same fallback to it, so Preview and Share
  render the Sokoon document.

Invoices posted before this module was upgraded keep the PDF that was attached
at posting time - that attachment is the legal document, so it is deliberately
not rewritten. Delete the stale ``invoice_pdf_report_id`` attachment and re-send
such an invoice to regenerate it.

Scope
-----
The inherited patch in ``views/report_invoice.xml`` still applies the "الزبون"
label to every document rendered through the stock invoice report - customer
invoices, credit notes, vendor bills and vendor credit notes - for databases
without the Studio customisation. The standalone entry above is the one to
print on this database.
""",
    'author': "Kosai Alhafez",
    'website': "https://blasedoesit.com",
    'depends': ['account'],
    'data': [
        'views/report_invoice.xml',
        'report/report_invoice_sokoon.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
