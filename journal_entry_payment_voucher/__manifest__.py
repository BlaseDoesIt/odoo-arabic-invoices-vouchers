{
    'name': "Journal Entry Voucher",
    # 1.1.0: the amount in words is Arabic with the currency inflected, the
    # table has no total row, and the corner curves were re-cut.
    #
    # The words were "number + whatever label the currency record carries",
    # which printed "خمسمائة Dollars" on a default database and could not be
    # fixed by typing Arabic into the record either: Arabic agrees a counted
    # noun with its number, so one label cannot serve خمسمائة ليرة سورية,
    # ليرتان سوريتان and أحد عشر ليرةً سوريةً. The four forms per currency are
    # now in ARABIC_CURRENCY_FORMS (models/account_move.py) and the inflection
    # comes from num2words' Arabic converter, driven directly - see
    # `_journal_voucher_arabic_currency_words` for why not through
    # `num2words(to='currency')`, which relabels every currency it does not
    # know as ريال.
    #
    # The curves: each is now an ellipse centred OFF the paper, so only one
    # quadrant of it can land on the page. The grey ring in 1.0.0 was centred
    # on the page and closed, printing its bottom across the document as a
    # thick letter O. The signature block moved with them - it is pinned to the
    # foot of the page rather than flowed after the table, which is what makes
    # the gap between it and the curves a fixed geometry. That reserved band
    # costs two rows: eight fit on a page now, against ten in 1.0.0.
    'version': '19.0.1.1.0',
    'category': 'Accounting/Accounting',
    'summary': "Print a journal entry as a payment (سند دفع) or receipt (سند قبض) voucher.",
    'description': """
Journal Entry Voucher
=====================

Adds two PDF reports to the Print menu of a journal entry:

* **سند دفع — Payment Voucher**: the money going out. Lists the DEBIT side.
* **سند قبض — Receipt Voucher**: the money coming in. Lists the CREDIT side.

That mapping is the only difference between the two documents. Each prints one
**المبلغ** (amount) column rather than the debit/credit pair a journal entry
has, so a row only ever appears on the voucher whose side it belongs to, and
the column sums to the amount of the voucher. That amount is stated once, in
the header - as a figure and spelled out in Arabic - so the table carries no
total row.

The currency is read off Odoo's own ``res.currency`` record - the code, the
decimal places, and the unit names. The amount in words is written in Arabic
with the currency inflected by the number counting it (خمسمائة ليرة سورية,
ليرتان سوريتان, أحد عشر دولاراً أمريكياً), which needs four grammatical forms
and a gender where a currency record has two label fields; those forms live in
``ARABIC_CURRENCY_FORMS`` in models/account_move.py. A currency that is not
listed there falls back to the record's own labels, uninflected.

Paper is A5 landscape (210x148mm), matching the printed voucher stationery.
""",
    'author': "Kosai Alhafez",
    "website": "https://blasedoesit.com",
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'auto_install': False,

    # `account` for account.move / account.move.line, `web` for the report
    # machinery and `web.html_container`. Nothing else - the voucher draws its
    # own stationery instead of inheriting an external layout.
    'depends': [
        'account',
        'web',
    ],

    'data': [
        # The templates are referenced by the report actions' `report_name`,
        # which is resolved at print time, so load order between these two is
        # not load-critical. Templates first anyway, so a fresh install never
        # has an action pointing at a template that is not there yet.
        'report/journal_entry_voucher_templates.xml',
        'report/journal_entry_voucher_reports.xml',
    ],
}
