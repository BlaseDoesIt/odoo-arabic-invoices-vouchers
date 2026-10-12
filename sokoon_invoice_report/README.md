# Sokoon Invoice Report

Odoo **19.0** module. Keeps the standard invoice PDF exactly as it is, with one
change to the customer block at the top left of the page.

## Before

```
partner_id.title.name    Customer Name
```

The customer block is drawn by Odoo's `contact` widget, which expands the
address format configured on the partner's country. That format contains the
literal token `partner_id.title.name`, so the raw token is printed on every
invoice.

## After

```
الزبون    Customer Name
```

## How it works

`views/report_invoice.xml` inherits `account.report_invoice_document` and
replaces the `<address>` element of the customer block with an explicit block
(`sokoon_invoice_report.invoice_customer_block`) that prints the fixed label
`الزبون` followed by the partner name, then the partner address lines when the
partner has any.

All three shipping-address variants of the standard template are patched
(`address_not_same_as_shipping`, `address_same_as_shipping`, `no_shipping`), so
the label shows whichever delivery-address case applies.

The block is forced to `dir="ltr"` with left alignment so the label stays on the
left of the name; the rest of the page keeps its right-to-left layout.

Nothing else is touched — header, logo, invoice title, dates, line table, taxes,
totals, payment communication and footer are all standard Odoo.

## Print entry: `Sokoon Invoice / فاتورة سكون`

This database carries Odoo **Studio** customisations (`studio_customization`)
on `account.report_invoice_document`, which turn the invoice into a
journal-entry style listing with `ACCOUNT` / `PARTNER` columns grouped by
product category. Studio stores those edits as inherited `ir.ui.view` records
on the stock template, so *every* stock print entry renders the Studio layout
instead of the invoice — and so does any inherited or `primary` template built
on it, since a primary view is combined from the parent's fully merged arch.

`report/report_invoice_sokoon.xml` therefore ships a **standalone copy** of the
Odoo 19.0 stock invoice document as `sokoon_invoice_report.sokoon_invoice_document`.
It has no `inherit_id`, so no Studio view can apply to it, and it renders the
original layout exactly as in the company's reference invoice — with the `الزبون` label.

`print_with_payments` is left unset, matching the reference PDF (no payment
block, just the total and the payment communication line).

**Print this entry**, not "فواتير العملاء" / "Invoice PDF".

## Always Arabic

The wrapper forces the document language to Arabic, whatever language the
customer is set to, so every invoice prints identically:

```xml
<t t-set="arabic_lang"
   t-value="o.env['res.lang'].search([('code','in',['ar_SY','ar_001'])], order='code desc', limit=1).code"/>
<t t-set="lang" t-value="arabic_lang or o.partner_id.lang"/>
```

`ar_SY` wins over `ar_001` when both are installed (descending code order).
If no Arabic language is installed it falls back to the partner language, so
the report still renders rather than failing. Both Arabic locales are
`Right-to-Left` in `res.lang`, so setting the language also gives the RTL page
direction of the reference PDF. The customer block keeps its own `dir="ltr"`
so `الزبون` stays on the left.

### `i18n/ar.po` — why the module needs its own

View translations live in each view's own `arch_db`, so the standalone copy
does **not** inherit the Arabic that ships with `account` — it would print
English labels under `lang=ar`. `i18n/ar.po` carries the 64 terms of the
invoice document, taken from `addons/account/i18n/ar.po` (19.0).

One deliberate difference: `Invoice Date` is translated `تاريخ الفاتورة`, the
wording in the reference invoice, rather than the upstream `تاريخ فاتورة العميل`.

Odoo's `get_base_langs()` reduces both `ar_001` and `ar_SY` to `ar`, so this
single file covers either locale. The totals block (`الإجمالي`) comes from
`account.document_tax_totals`, which is still account's own template and so is
already translated.

### Keeping the copy in sync

Being a copy, `sokoon_invoice_document` does not follow upstream changes to the
stock invoice report. When upgrading Odoo, re-copy the `report_invoice_document`
template from `account/views/report_invoice.xml` and re-apply the customer block
swap (three `<address>` elements → `<t t-call="sokoon_invoice_report.invoice_customer_block"/>`).

The tax-total sub-templates are still called from `account`, as in the reference
PDF.

## Scope

The template patch applies to every document printed through the standard
invoice report — customer invoices, credit notes, vendor bills and vendor credit
notes, in both the normal and the "with payments" variants — plus the dedicated
entry above.

## Install

1. Copy `sokoon_invoice_report` into the addons path (it lives in
   `custom_addons/` in this repository).
2. Update the apps list.
3. Install **Sokoon Invoice Report**.

Depends on `account` only.

## Preview / Share / Send & Print

A Print entry alone is not enough. `Preview` and `Share` open the customer
portal, and Odoo 19's portal renders
`partner.invoice_template_pdf_report_id` or — when the partner has none — the
hard-coded `account.account_invoices`, which on this database is the
Studio-customised journal-entry listing. Send & Print resolves the same
fallback and freezes its output into `invoice_pdf_report_id`, the attachment
the portal returns on download.

Three changes make the Sokoon report the one all of them pick:

- `report/report_invoice_sokoon.xml` flags the report action
  `is_invoice_report` and gives it the `move_type != entry` domain — what Odoo
  19 requires before a report may serve as an invoice template
  (`account.move._get_available_action_reports` / `_is_action_report_available`).
- `models/account_move_send.py` redirects the `account.account_invoices`
  last-resort fallback in `_get_default_pdf_report_id`, so newly posted
  invoices attach the Sokoon PDF. A template set explicitly on the partner or
  the journal still wins.
- `controllers/portal.py` resolves the same fallback in
  `portal_my_invoice_detail`, so Preview and Share render the Sokoon document.

Invoices posted before this upgrade keep the PDF attached at posting time —
that attachment is the legal document, so it is deliberately not rewritten.
To refresh one, delete its `invoice_pdf_report_id` attachment and re-send it.
