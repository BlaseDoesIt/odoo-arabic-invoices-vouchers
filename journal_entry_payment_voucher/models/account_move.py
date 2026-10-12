import logging

from odoo import fields, models

try:
    from num2words import num2words
except ImportError:
    num2words = None

try:
    from num2words.lang_AR import Num2Word_AR
except ImportError:
    Num2Word_AR = None

_logger = logging.getLogger(__name__)

#: Which side of the journal entry each voucher prints.
#:
#: A payment voucher (سند دفع) is money going out, so it lists what was paid
#: for - the DEBIT lines. A receipt voucher (سند قبض) is money coming in and
#: lists the CREDIT lines. That is the whole difference between the two
#: documents; everything else in the template is a label.
#:
#: This is also why the voucher prints one المبلغ column instead of the
#: debit/credit pair the journal entry carries. A line belongs to exactly one
#: side, so on its own voucher it has exactly one amount - and the other side's
#: rows, which would otherwise print as a column of 0.00, are simply not rows
#: of this document. The column therefore sums to the amount of the voucher,
#: which the document states once, at the top: as a figure next to AMOUNT and
#: spelled out under المبلغ كتابة. The table itself carries no total row.
VOUCHER_SIDES = {
    'payment': 'debit',
    'receipt': 'credit',
}

#: num2words' code for the language the amount in words is spelled in - not an
#: Odoo language code. The voucher is an Arabic document, so the words are
#: Arabic whatever language the person printing it happens to be using in the
#: web client. Set this to None to follow the printer's own language instead.
AMOUNT_WORDS_LANG = 'ar'

#: Arabic grammatical forms for the currencies, keyed by the ISO code on the
#: Odoo currency record.
#:
#: WHY THIS TABLE EXISTS, given that everything else about a currency is read
#: off ``res.currency``: Arabic inflects a counted noun by the number counting
#: it, and Odoo's currency record has two label fields where Arabic needs four
#: forms and a gender. "ليرة" is not a spelling of one word - it is
#:
#:     ليرة سورية        (0, 1, and any hundred: خمسمائة ليرة سورية)
#:     ليرتان سوريتان    (exactly 2)
#:     ليرات سورية       (3-10: خمس ليرات سورية)
#:     ليرةً سوريةً       (11-99: أحد عشر ليرةً سوريةً)
#:
#: and the gender decides the number word itself - خمس ليرات for a feminine
#: unit against خمسة دولارات for a masculine one. Two label fields cannot say
#: that, so the four forms live here and the currency is still identified by
#: the record: this is keyed by ``currency.name``, the ISO code Odoo stores.
#:
#: A currency that is not listed falls back to the record's own
#: ``currency_unit_label`` / ``currency_subunit_label``, uninflected - which is
#: the old behaviour, and is why adding a currency here is optional. To add
#: one, give the four forms in the order above and say whether each noun is
#: feminine; the plural of an Arabic noun is frequently irregular (قرش becomes
#: قروش, not قرشات), so write them out rather than deriving them.
ARABIC_CURRENCY_FORMS = {
    'SYP': {
        'unit': ("ليرة سورية", "ليرتان سوريتان", "ليرات سورية", "ليرةً سوريةً"),
        'unit_feminine': True,
        'subunit': ("قرش", "قرشان", "قروش", "قرشاً"),
        'subunit_feminine': False,
    },
    'USD': {
        'unit': ("دولار أمريكي", "دولاران أمريكيان", "دولارات أمريكية", "دولاراً أمريكياً"),
        'unit_feminine': False,
        'subunit': ("سنت", "سنتان", "سنتات", "سنتاً"),
        'subunit_feminine': False,
    },
    'EUR': {
        'unit': ("يورو", "يوروان", "يوروهات", "يورو"),
        'unit_feminine': False,
        'subunit': ("سنت", "سنتان", "سنتات", "سنتاً"),
        'subunit_feminine': False,
    },
    'TRY': {
        'unit': ("ليرة تركية", "ليرتان تركيتان", "ليرات تركية", "ليرةً تركيةً"),
        'unit_feminine': True,
        'subunit': ("قرش", "قرشان", "قروش", "قرشاً"),
        'subunit_feminine': False,
    },
    'LBP': {
        'unit': ("ليرة لبنانية", "ليرتان لبنانيتان", "ليرات لبنانية", "ليرةً لبنانيةً"),
        'unit_feminine': True,
        'subunit': ("قرش", "قرشان", "قروش", "قرشاً"),
        'subunit_feminine': False,
    },
    'SAR': {
        'unit': ("ريال سعودي", "ريالان سعوديان", "ريالات سعودية", "ريالاً سعودياً"),
        'unit_feminine': False,
        'subunit': ("هللة", "هللتان", "هللات", "هللةً"),
        'subunit_feminine': True,
    },
    'AED': {
        'unit': ("درهم إماراتي", "درهمان إماراتيان", "دراهم إماراتية", "درهماً إماراتياً"),
        'unit_feminine': False,
        'subunit': ("فلس", "فلسان", "فلوس", "فلساً"),
        'subunit_feminine': False,
    },
    'EGP': {
        'unit': ("جنيه مصري", "جنيهان مصريان", "جنيهات مصرية", "جنيهاً مصرياً"),
        'unit_feminine': False,
        'subunit': ("قرش", "قرشان", "قروش", "قرشاً"),
        'subunit_feminine': False,
    },
    'JOD': {
        'unit': ("دينار أردني", "ديناران أردنيان", "دنانير أردنية", "ديناراً أردنياً"),
        'unit_feminine': False,
        'subunit': ("قرش", "قرشان", "قروش", "قرشاً"),
        'subunit_feminine': False,
    },
    'KWD': {
        'unit': ("دينار كويتي", "ديناران كويتيان", "دنانير كويتية", "ديناراً كويتياً"),
        'unit_feminine': False,
        'subunit': ("فلس", "فلسان", "فلوس", "فلساً"),
        'subunit_feminine': False,
    },
    'IQD': {
        'unit': ("دينار عراقي", "ديناران عراقيان", "دنانير عراقية", "ديناراً عراقياً"),
        'unit_feminine': False,
        'subunit': ("فلس", "فلسان", "فلوس", "فلساً"),
        'subunit_feminine': False,
    },
    'QAR': {
        'unit': ("ريال قطري", "ريالان قطريان", "ريالات قطرية", "ريالاً قطرياً"),
        'unit_feminine': False,
        'subunit': ("درهم", "درهمان", "دراهم", "درهماً"),
        'subunit_feminine': False,
    },
    'GBP': {
        'unit': ("جنيه إسترليني", "جنيهان إسترلينيان", "جنيهات إسترلينية", "جنيهاً إسترلينياً"),
        'unit_feminine': False,
        'subunit': ("بنس", "بنسان", "بنسات", "بنساً"),
        'subunit_feminine': False,
    },
}


class AccountMove(models.Model):
    """Everything the voucher prints, computed here rather than in QWeb.

    The template asks for one dict per document and lays it out. It does no
    arithmetic and knows nothing about debit, credit or currency conversion,
    which keeps the two questions this report has to get right - which lines
    belong on which voucher, and what currency their amount is in - in one
    testable place.
    """

    _inherit = 'account.move'

    # ------------------------------------------------------------------
    # Currency
    # ------------------------------------------------------------------
    # The currency itself is always a res.currency record: which one the
    # voucher is in, the code printed in the header, and the number of decimals
    # the amounts are rounded and printed to all come from it.
    #
    # The one thing that does not is the Arabic grammar of the currency's name,
    # which the record has nowhere to put - see ARABIC_CURRENCY_FORMS above for
    # what is missing and why. A currency absent from that table still reads
    # off the record's own labels.

    def _journal_voucher_currency(self):
        """The single currency the voucher is printed in."""
        self.ensure_one()
        return self.currency_id or self.company_currency_id

    def _journal_voucher_line_amount(self, line, currency):
        """``line``'s signed value in ``currency``: positive debit, negative credit.

        ``debit``/``credit`` are always company currency and ``amount_currency``
        is always the line's own, so which one answers the question depends on
        what the voucher is being printed in.
        """
        self.ensure_one()
        balance = line.debit - line.credit
        if currency == self.company_currency_id:
            return balance
        if line.currency_id == currency:
            return line.amount_currency
        # A line kept in some third currency - an exchange difference or a tax
        # line can be. Bring it over at the entry's own date rather than print
        # a number in the wrong unit.
        return self.company_currency_id._convert(
            balance,
            currency,
            self.company_id,
            self.date or fields.Date.context_today(self),
        )

    # ------------------------------------------------------------------
    # Amount in words
    # ------------------------------------------------------------------
    def _journal_voucher_amount_words(self, amount, currency):
        """``amount`` spelled out, in Arabic, with the currency inflected.

        Arabic agrees the currency with the number counting it, so this is not
        "spell the number, append a label" - خمسمائة ليرة سورية, ليرتان
        سوريتان and أحد عشر ليرةً سوريةً are the same currency after three
        different numbers, and the number word itself changes with the unit's
        gender (خمس ليرات against خمسة دولارات). num2words' Arabic converter
        knows those rules but ships one currency, so the forms come from
        :data:`ARABIC_CURRENCY_FORMS` and the grammar from the converter.

        Falls back to spelling the number and appending the currency record's
        own label - uninflected, but correct in every other respect - for a
        currency that is not in that table, for a non-Arabic
        :data:`AMOUNT_WORDS_LANG`, or if the converter's internals move under
        us. The figure itself is printed either way.
        """
        self.ensure_one()
        currency = currency.with_context(lang=self._journal_voucher_lang())
        if num2words is None:
            # No spelling library on this deployment. Odoo's own method has the
            # same dependency and returns an empty string, so defer to it
            # rather than invent a format: the figure is on the page either way.
            _logger.warning("num2words is not installed; the voucher cannot spell out amounts.")
            return currency.amount_to_text(amount)

        words = self._journal_voucher_arabic_currency_words(amount, currency)
        if words:
            return words
        return self._journal_voucher_plain_words(amount, currency)

    def _journal_voucher_arabic_currency_words(self, amount, currency):
        """``amount`` in inflected Arabic, or ``False`` if that is not available.

        Drives num2words' Arabic converter directly rather than through
        ``num2words(..., to='currency')``, because that entry point calls
        ``set_currency_prefer``, which knows four currencies and silently
        relabels everything else as ريال - it would print a dollar amount as
        riyals. Setting the forms on the converter and converting is the same
        code path with the relabelling step left out.

        Reaching into another library's attributes is a real cost, so it is
        contained here: every failure returns ``False`` and the caller spells
        the amount the plain way.
        """
        if Num2Word_AR is None or AMOUNT_WORDS_LANG != 'ar':
            return False
        forms = ARABIC_CURRENCY_FORMS.get(currency.name)
        if not forms:
            return False
        try:
            converter = Num2Word_AR()
            converter.currency_unit = forms['unit']
            converter.currency_subunit = forms['subunit']
            converter.isCurrencyNameFeminine = forms['unit_feminine']
            converter.isCurrencyPartNameFeminine = forms['subunit_feminine']
            converter.partPrecision = currency.decimal_places
            converter.separator = 'و'
            converter.arabicPrefixText = ''
            converter.arabicSuffixText = ''
            text = converter.convert(value=amount).strip()
            return self._journal_voucher_tidy_arabic(text, amount, forms) or False
        except Exception:  # noqa: BLE001 - any breakage here falls back
            _logger.warning(
                "Could not spell %s %s in Arabic; falling back to the currency's label.",
                amount, currency.name, exc_info=True)
            return False

    def _journal_voucher_tidy_arabic(self, text, amount, forms):
        """Three places where the converter's output is not what Arabic writes.

        All three are about the integer part, and all three are matched on an
        exact leading word rather than reformatted, so an amount that is none
        of these cases is returned untouched.
        """
        integer_value = int(abs(amount))
        has_fraction = abs(abs(amount) - integer_value) > 1e-9

        # Under one unit there is no integer half to spell, but the converter
        # still writes the "و" that joins the two halves: "و خمسة و سبعون قرشاً".
        #
        # Matched WITH its trailing space, so it can only ever match the
        # conjunction standing as its own word. Without that space this also
        # matches the "و" that opens واحد, and 21,750 comes out as احد و عشرون.
        if text.startswith('و '):
            text = text[2:].lstrip()

        # The next two rewrite where the number sits relative to the noun, so
        # they only apply when the integer part is the whole amount. With a
        # fraction after it the sentence continues, and there is no longer an
        # end of it for the number to move to.
        if not has_fraction:
            # "واحد ليرة سورية" - Arabic counts one by putting the number after
            # the noun and agreeing it: ليرة سورية واحدة.
            if integer_value == 1:
                for one in ('واحد ', 'إحدى '):
                    if text.startswith(one):
                        text = '%s %s' % (text[len(one):],
                                          'واحدة' if forms['unit_feminine'] else 'واحد')
                        break

            # "اثنتان ليرتان سوريتان" - the dual noun already says two.
            elif integer_value == 2:
                for two in ('اثنتان ', 'اثنان '):
                    if text.startswith(two):
                        text = text[len(two):]
                        break

        return text.strip()

    def _journal_voucher_plain_words(self, amount, currency):
        """``amount`` spelled out with the currency record's labels appended."""
        integer_part, _dot, fraction_part = ("%.*f" % (currency.decimal_places, amount)).partition('.')
        words = self._journal_voucher_num2words(int(integer_part))
        if currency.currency_unit_label:
            words = "%s %s" % (words, currency.currency_unit_label)
        fraction = int(fraction_part or 0)
        if fraction:
            subunit = self._journal_voucher_num2words(fraction)
            if currency.currency_subunit_label:
                subunit = "%s %s" % (subunit, currency.currency_subunit_label)
            words = "%s و %s" % (words, subunit)
        return words

    def _journal_voucher_lang(self):
        """The language the document is being rendered in."""
        return self.env.context.get('lang') or self.env.user.lang or 'en_US'

    def _journal_voucher_num2words(self, number):
        """``number`` in words, falling back to English if the language is unsupported."""
        lang = AMOUNT_WORDS_LANG or self._journal_voucher_lang()
        try:
            return num2words(number, lang=lang)
        except NotImplementedError:
            return num2words(number, lang='en')

    # ------------------------------------------------------------------
    # The document
    # ------------------------------------------------------------------
    def _journal_voucher_values(self, voucher_type):
        """Everything one voucher prints.

        ``voucher_type`` is a key of :data:`VOUCHER_SIDES`. Rows are the lines
        on that voucher's side, in entry order, each with its لقاء label and its
        amount; the total is their sum, which is what the header spells out.
        """
        self.ensure_one()
        if voucher_type not in VOUCHER_SIDES:
            raise ValueError("Unknown voucher type %r" % (voucher_type,))
        currency = self._journal_voucher_currency()
        debit_side = VOUCHER_SIDES[voucher_type] == 'debit'

        rows = []
        for line in self.line_ids:
            if not line.account_id:
                continue
            amount = self._journal_voucher_line_amount(line, currency)
            # The sign picks the side, and a line that rounds to nothing in the
            # printed currency is not a row of either voucher.
            if currency.is_zero(amount) or debit_side != (amount > 0):
                continue
            rows.append({
                'label': line.name or self.ref or '',
                'amount': abs(amount),
                'amount_text': self._journal_voucher_format(abs(amount), currency),
            })

        total = currency.round(sum(row['amount'] for row in rows))
        return {
            'voucher_type': voucher_type,
            'currency': currency,
            'rows': rows,
            'total': total,
            'total_text': self._journal_voucher_format(total, currency),
            'amount_words': self._journal_voucher_amount_words(total, currency),
        }

    def _journal_voucher_format(self, amount, currency):
        """``amount`` as it is printed: grouped thousands, the currency's decimals.

        Deliberately not ``formatLang`` or the monetary widget. Those follow the
        printing user's language, and this document's figures are set in Latin
        digits with a comma group and a dot decimal on every install - see the
        sample voucher. The currency still decides how many decimals there are.
        """
        return '{:,.{precision}f}'.format(amount, precision=currency.decimal_places)
