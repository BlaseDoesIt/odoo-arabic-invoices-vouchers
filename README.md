# Arabic invoices and vouchers for Odoo

Two **Odoo 19** modules that print Arabic accounting documents straight from Odoo, in the company's own design. Built for Sokoon Rental House in Damascus, where they replaced invoices and vouchers typed up in Word and Excel.

Project page: [blasedoesit.com/projects/invoices](https://blasedoesit.com/projects/invoices/)

## Modules

### `journal_entry_payment_voucher`: payment and receipt vouchers

Adds two PDF reports to the **Print** menu of any journal entry:

- **سند دفع (payment voucher)**: money going out, lists the debit side.
- **سند قبض (receipt voucher)**: money coming in, lists the credit side.

What's in it:

- **Amount in Arabic words with correct grammar.** Arabic changes the currency noun depending on the number (خمسمائة ليرة سورية, ليرتان سوريتان, أحد عشر دولاراً أمريكياً). The four forms and the gender for each currency live in `ARABIC_CURRENCY_FORMS` in `models/account_move.py`. The number itself comes from num2words' Arabic converter, called directly so unknown currencies aren't relabeled as ريال.
- **One amount column.** Each row only appears on the voucher whose side it belongs to, so the column adds up to the voucher amount. The total is stated once in the header, as a figure and in words.
- **A5 landscape** to match the printed stationery, with the signature block pinned to the bottom of the page.
- **Tests** in `tests/test_journal_entry_voucher.py`.

### `sokoon_invoice_report`: Arabic customer invoice

The technical name is kept as it is in production so existing databases upgrade cleanly.

- **Fixes a customer label bug.** The stock invoice builds the customer block from the country's address format. On this database that format contained a raw `partner_id.title.name` token, which printed literally on every invoice. The module replaces the block with a fixed **الزبون** label.
- **A clean copy of the stock invoice.** Odoo Studio edits on the stock template had turned the invoice into a journal-style listing. The module ships a standalone copy of the Odoo 19 invoice document with no `inherit_id`, so Studio changes can't reach it.
- **Always Arabic, right to left**, whatever language the customer has. Prefers `ar_SY`, then `ar_001`.
- **Preview, Share and Send use it too.** It overrides the portal controller and `account.move.send._get_default_pdf_report_id`, so the customer portal and emailed PDFs get the same document, not just the Print menu.
- **Arabic labels** in `i18n/ar.po` (the 64 terms of the invoice document).

## Tech

Python, QWeb reports, Odoo Accounting, num2words, wkhtmltopdf. Cairo font included for Arabic text.

## Install

Requires **Odoo 19** with the Accounting app. Both modules work on Community or Enterprise.

1. Copy one or both module folders into a directory on your Odoo addons path.
2. Restart Odoo, then **Apps → Update Apps List**.
3. Install **Journal Entry Voucher** and/or **Sokoon Invoice Report**.
4. Open a journal entry or an invoice and use **Print**.

Run the voucher tests:

```bash
odoo-bin -d <test_db> -i journal_entry_payment_voucher --test-enable --stop-after-init
```

## Author

Built by **Kosai Alhafez**, business systems developer.
[blasedoesit.com](https://blasedoesit.com) · kosai@blasedoesit.com

## License

LGPL-3. See [LICENSE](LICENSE).
