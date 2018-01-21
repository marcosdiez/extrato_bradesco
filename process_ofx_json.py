#!/usr/bin/env python
from collections import OrderedDict, defaultdict
import collections
import os
import json
import sys
import datetime
import codecs

data2 = json.load(codecs.open(sys.argv[1], "r", "utf-8"), object_pairs_hook=OrderedDict)
data = data2["OFX"]["BANKMSGSRSV1"]["STMTTRNRS"]["STMTRS"]
statements = data["BANKTRANLIST"]["STMTTRN"]

class OrderedDefaultdict(collections.OrderedDict):
    """ A defaultdict with OrderedDict as its base class. """

    def __init__(self, default_factory=None, *args, **kwargs):
        if not (default_factory is None
                or isinstance(default_factory, collections.Callable)):
            raise TypeError('first argument must be callable or None')
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory  # called by __missing__()

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key,)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):  # optional, for pickle support
        args = (self.default_factory,) if self.default_factory else tuple()
        return self.__class__, args, None, None, self.iteritems()

    def __repr__(self):  # optional
        return '%s(%r, %r)' % (self.__class__.__name__, self.default_factory,
                               list(self.iteritems()))

from json import JSONEncoder
class MyEncoder(JSONEncoder):
    def default(self, o):
        for key, value in o.__dict__.iteritems():
            if isinstance(value, datetime.datetime):
                o.__dict__[key] = "{}".format(value)
        return o.__dict__

class StatementItem(object):
    @staticmethod
    def parse_ofx_date(input):
        pos = input.find("[")
        if input.find("["):
            input = input[0:pos]
        #"DTSTART": "20180120120000",
        #"DTSTART": "2018x01x20x12x0000",
        #< DTPOSTED > 20130204000000[-03:EST]
        return datetime.datetime.strptime(input, "%Y%m%d%H%M%S")

    @staticmethod
    def parse_ofx_currency(input):
        return float(input.replace(",", "."))

    def get_period(self):
        return self.date.strftime("%Y-%m")

    def __init__(self, stmtrn):
        # {
        #     "TRNTYPE": "CREDIT",
        #     "DTPOSTED": "20130213120000",
        #     "TRNAMT": "930,73",
        #     "FITID": "N1012D",
        #     "CHECKNUM": "269578",
        #     "MEMO": "BAIXA AUTOMATICA FUNDOS"
        # },
        self.stmtrn = stmtrn
        self.trn_type = stmtrn["TRNTYPE"]
        self.date = self.parse_ofx_date(stmtrn["DTPOSTED"])
        self.amount = self.parse_ofx_currency(stmtrn["TRNAMT"])
        self.memo = stmtrn["MEMO"]
        self._validate()

    def _validate(self):
        if self.trn_type == "CREDIT" and self.amount < 0:
            raise ValueError(self.stmtrn)
        if self.trn_type == "DEBIT" and self.amount > 0:
            raise ValueError(self.stmtrn)
        if self.trn_type not in ["CREDIT", "DEBIT"]:
            raise ValueError(self.stmtrn)

class StatementMemo(object):
    def __init__(self):
        self.total = 0
        self.count = 0
    def add_value(self, value):
        self.total += value
        self.count += 1

class StatementPeriod(object):
    def __init__(self):
        self.total_credit = 0
        self.total_debit = 0
        self.delta = 0
        self.credits = OrderedDefaultdict(StatementMemo)
        self.debits = OrderedDefaultdict(StatementMemo)

    def add_statement_item(self, item):
        self.delta += item.amount
        if item.trn_type == "CREDIT":
            self.total_credit += item.amount
            self.credits[item.memo].add_value(item.amount)
        else:
            self.total_debit += item.amount
            self.debits[item.memo].add_value(item.amount)

class Statement(object):
    def __init__(self, bank_id, account_id, account_type):
        self.bank_id = bank_id
        self.account_id = account_id
        self.account_type = account_type
        self.total = StatementPeriod()
        self.periods = OrderedDefaultdict(StatementPeriod)
        self.first_statement = None
        self.last_statement = None

    def add_statement_item(self, item):
        self.total.add_statement_item(item)
        self.periods[item.get_period()].add_statement_item(item)

        if self.first_statement is None or item.date < self.first_statement:
            self.first_statement = item.date

        if self.last_statement is None or item.date > self.last_statement:
            self.last_statement = item.date

    def to_json(self):
        return json.dumps(self, sort_keys=True, indent=2, cls=MyEncoder)

    def to_csv_mensal(self):
        forma = "'{periodo}{sep}{entrada}{sep}{saida}{sep}{delta}{lf}"
        output = ""
        sep = ","
        lf = "\n"
        output += "periodo{sep}entrada{sep}saida{sep}delta{lf}".format(sep=sep, lf=lf)
        output += forma.format(sep=sep, lf=lf, periodo="total", entrada=self.total.total_credit, saida=self.total.total_debit, delta=self.total.delta)
        period_names = self.periods.keys()
        period_names.sort()

        for period_name in period_names:
            item = self.periods[period_name]
            output += forma.format(sep=sep, lf=lf,
                                   periodo=period_name,
                                   entrada=item.total_credit,
                                   saida=item.total_debit,
                                   delta=item.delta)
        return output

    def to_csv_grouped(self):
        #periodo	evento	quantidade	debito	credito

        forma = u"'{periodo}{sep}{descricao}{sep}{quantidade}{sep}{debito}{sep}{credito}{lf}"
        sep = ","
        lf = "\n"

        output = "periodo{sep}descricao{sep}quantidade{sep}debito{sep}credito{lf}".format(lf=lf,sep=sep)

        for period_name in self.periods:
            statement_period = self.periods[period_name]
            for name in statement_period.credits:
                statement_memo = statement_period.credits[name]
                output += forma.format(sep=sep, lf=lf, periodo=period_name, descricao=name, quantidade=statement_memo.count,
                                       debito="", credito=statement_memo.total)
            for name in statement_period.debits:
                statement_memo = statement_period.debits[name]
                output += forma.format(sep=sep, lf=lf, periodo=period_name, descricao=name, quantidade=statement_memo.count,
                                       credito="", debito=statement_memo.total)

        return output


inputs = {
    "TRNTYPE": defaultdict(lambda: 0),
    "MEMO_CREDIT": defaultdict(lambda: 0),
    "MEMO_DEBIT": defaultdict(lambda: 0)
}

output = Statement( data["BANKACCTFROM"]["BANKID"],
    data["BANKACCTFROM"]["ACCTID"],
    data["BANKACCTFROM"]["ACCTTYPE"])

for item in statements:
    inputs["TRNTYPE"][item["TRNTYPE"]] += 1
    inputs["MEMO_{}".format(item["TRNTYPE"])][item["MEMO"]] += 1
    statement_item = StatementItem(item)

    output.add_statement_item(statement_item)
    # print(x.get_period())

# print json.dumps(inputs, sort_keys=True, indent=2)
with codecs.open(sys.argv[1][0:sys.argv[1].rfind(".")] + "_processed.json", "w", "utf-8") as output_file:
    output_file.write(output.to_json())

with codecs.open(sys.argv[1][0:sys.argv[1].rfind(".")] + "_mensal.csv", "w", "utf-8") as output_file:
    output_file.write(output.to_csv_mensal())

with codecs.open(sys.argv[1][0:sys.argv[1].rfind(".")] + "_grouped.csv", "w", "utf-8") as output_file:
    output_file.write(output.to_csv_grouped())

print("Done")