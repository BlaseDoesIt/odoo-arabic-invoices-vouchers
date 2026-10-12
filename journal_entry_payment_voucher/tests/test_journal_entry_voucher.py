"""Which lines land on which voucher, and in what currency.

Those are the only two questions this report can get wrong in a way that is
not visible on the page, so they are the ones pinned here. The layout is not
tested beyond "it renders" - a PDF's appearance is not something an assertion
can hold onto, but a template that raises on every print is.
"""

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from odoo.addons.journal_entry_payment_voucher.models.account_move import (
    ARABIC_CURRENCY_FORMS,
    num2words,
)


@tagged('post_install', '-at_install')
class TestJournalEntryVoucher(AccountTestInvoicingCommon):
    """A journal entry printed as سند دفع and as سند قبض."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.expense = cls.company_data['default_account_expense']
        cls.revenue = cls.company_data['default_account_revenue']
        cls.payable = cls.company_data['default_account_payable']

    def _entry(self):
        """Two debit lines against one credit line, plus a line worth nothing.

        The 0.00 line is the interesting one: it belongs to neither side, so it
        must not print on either voucher.
        """
        return self.env['account.move'].create({
            'move_type': 'entry',
            'date': '2026-08-18',
            'ref': 'S00656',
            'journal_id': self.company_data['default_journal_misc'].id,
            'line_ids': [
                Command.create({
                    'name': "ترويج فيديو على صفحة المحافظة",
                    'account_id': self.expense.id,
                    'debit': 21750.0,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': "ترويج فيديو عن مخالفات البناء",
                    'account_id': self.expense.id,
                    'debit': 45000.0,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': "بلا قيمة",
                    'account_id': self.expense.id,
                    'debit': 0.0,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': "S00656 - S00500",
                    'account_id': self.payable.id,
                    'debit': 0.0,
                    'credit': 66750.0,
                }),
            ],
        })

    # ------------------------------------------------------------------
    # Which side prints
    # ------------------------------------------------------------------
    def test_payment_voucher_prints_the_debit_side(self):
        voucher = self._entry()._journal_voucher_values('payment')
        self.assertEqual(
            [row['label'] for row in voucher['rows']],
            ["ترويج فيديو على صفحة المحافظة", "ترويج فيديو عن مخالفات البناء"],
        )
        self.assertEqual([row['amount'] for row in voucher['rows']], [21750.0, 45000.0])
        self.assertEqual(voucher['total'], 66750.0)

    def test_receipt_voucher_prints_the_credit_side(self):
        voucher = self._entry()._journal_voucher_values('receipt')
        self.assertEqual([row['label'] for row in voucher['rows']], ["S00656 - S00500"])
        self.assertEqual(voucher['total'], 66750.0)

    def test_a_line_worth_nothing_is_on_neither_voucher(self):
        entry = self._entry()
        for voucher_type in ('payment', 'receipt'):
            rows = entry._journal_voucher_values(voucher_type)['rows']
            self.assertNotIn("بلا قيمة", [row['label'] for row in rows])

    def test_the_total_is_the_column(self):
        """The header's figure is the column's sum - not the entry's balance."""
        entry = self._entry()
        for voucher_type in ('payment', 'receipt'):
            voucher = entry._journal_voucher_values(voucher_type)
            self.assertEqual(
                voucher['total'],
                sum(row['amount'] for row in voucher['rows']),
            )

    def test_an_unknown_voucher_type_is_refused(self):
        with self.assertRaises(ValueError):
            self._entry()._journal_voucher_values('cheque')

    # ------------------------------------------------------------------
    # Currency
    # ------------------------------------------------------------------
    def test_figures_follow_the_currency_record(self):
        """Decimals come off res.currency, not from this module."""
        entry = self._entry()
        currency = entry._journal_voucher_currency()
        self.assertEqual(currency, entry.currency_id)
        self.assertEqual(
            entry._journal_voucher_values('payment')['total_text'],
            '{:,.{precision}f}'.format(66750.0, precision=currency.decimal_places),
        )

    def _currency(self, code):
        currency = self.env['res.currency'].with_context(active_test=False).search(
            [('name', '=', code)], limit=1)
        if not currency:
            self.skipTest("no %s currency in this database" % code)
        return currency

    def test_a_listed_currency_is_inflected_by_the_number(self):
        """Arabic changes the currency noun with the number counting it.

        The four cases the language distinguishes, all of the same currency -
        if any of these come back with the same form, the converter is being
        handed a plain label instead of the four in ARABIC_CURRENCY_FORMS.
        """
        if num2words is None:
            self.skipTest("num2words is not installed")
        entry = self._entry()
        syp = self._currency('SYP')
        self.assertEqual(entry._journal_voucher_amount_words(500.0, syp),
                         "خمسمائة ليرة سورية")
        self.assertEqual(entry._journal_voucher_amount_words(2.0, syp),
                         "ليرتان سوريتان")
        self.assertEqual(entry._journal_voucher_amount_words(5.0, syp),
                         "خمس ليرات سورية")
        self.assertEqual(entry._journal_voucher_amount_words(11.0, syp),
                         "إحدى عشرة ليرةً سوريةً")

    def test_the_number_word_agrees_with_the_units_gender(self):
        """Five is خمس before a feminine unit and خمسة before a masculine one.

        Which is why the gender is in the table and not inferred: it changes
        the NUMBER, not the noun, so getting it wrong misspells a word that
        looks like it has nothing to do with the currency.
        """
        if num2words is None:
            self.skipTest("num2words is not installed")
        entry = self._entry()
        self.assertEqual(entry._journal_voucher_amount_words(5.0, self._currency('SYP')),
                         "خمس ليرات سورية")
        self.assertEqual(entry._journal_voucher_amount_words(5.0, self._currency('USD')),
                         "خمسة دولارات أمريكية")

    def test_the_subunit_is_arabic_too(self):
        """Cents and قروش, not "Cents" left in English after an Arabic number."""
        if num2words is None:
            self.skipTest("num2words is not installed")
        entry = self._entry()
        words = entry._journal_voucher_amount_words(175500.25, self._currency('USD'))
        self.assertEqual(
            words,
            "مائة و خمسة و سبعون ألفاً و خمسمائة دولار أمريكي و خمسة و عشرون سنتاً")

    def test_an_amount_under_one_unit_does_not_open_with_a_conjunction(self):
        if num2words is None:
            self.skipTest("num2words is not installed")
        words = self._entry()._journal_voucher_amount_words(0.75, self._currency('USD'))
        self.assertEqual(words, "خمسة و سبعون سنتاً")

    def test_an_unlisted_currency_falls_back_to_the_record_label(self):
        """A currency this module does not carry forms for still spells out.

        Uninflected - one label after the number - which is all two fields on
        the currency record can express, and is why adding a currency to
        ARABIC_CURRENCY_FORMS is an improvement rather than a prerequisite.
        """
        if num2words is None:
            self.skipTest("num2words is not installed")
        currency = self.env['res.currency'].with_context(active_test=False).search(
            [('name', 'not in', list(ARABIC_CURRENCY_FORMS))], limit=1)
        if not currency:
            self.skipTest("every currency in this database is in the table")
        currency.currency_unit_label = "فرنك"
        words = self._entry()._journal_voucher_amount_words(500.0, currency)
        self.assertTrue(words.endswith("فرنك"), words)

    # ------------------------------------------------------------------
    # The document
    # ------------------------------------------------------------------
    def test_both_reports_render(self):
        entry = self._entry()
        for report, title in (
            ('journal_entry_payment_voucher.report_payment_voucher', "سند دفع"),
            ('journal_entry_payment_voucher.report_receipt_voucher', "سند قبض"),
        ):
            html = self.env['ir.actions.report']._render_qweb_html(report, entry.ids)[0]
            if isinstance(html, bytes):
                html = html.decode('utf-8')
            self.assertIn(title, html)
            # The figure is stated once, in the header block.
            self.assertIn('66,750.00', html)
            # ...and the table no longer repeats it as a total row.
            self.assertNotIn('الإجمالي', html)

    def test_the_paper_stays_a5_landscape(self):
        """The type scale in the template is measured for this paper.

        See note 1 at the top of report/journal_entry_voucher_templates.xml: on
        any other size the document prints at the wrong optical scale, which is
        not something the reports themselves can complain about.
        """
        paperformat = self.env.ref('journal_entry_payment_voucher.paperformat_journal_entry_voucher')
        self.assertEqual(paperformat.format, 'A5')
        self.assertEqual(paperformat.orientation, 'Landscape')
        for report in (
            'journal_entry_payment_voucher.action_report_payment_voucher',
            'journal_entry_payment_voucher.action_report_receipt_voucher',
        ):
            self.assertEqual(self.env.ref(report).paperformat_id, paperformat)
