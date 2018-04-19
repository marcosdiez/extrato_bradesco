#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
from collections import OrderedDict, defaultdict
import collections
import os
import json
import sys
import datetime
import codecs

if len(sys.argv) < 2:
    print("usage: {} SOURCE_JSON_FILE")
    sys.exit(1)

source_file = sys.argv[1]

if not os.path.isfile(source_file):
    print("usage: {} SOURCE_JSON_FILE")
    sys.exit(1)

print("Opening {}".format(source_file))
data2 = json.load(codecs.open(source_file, "r", "utf-8"), object_pairs_hook=OrderedDict)
data = data2["OFX"]["BANKMSGSRSV1"]["STMTTRNRS"]["STMTRS"]
statements = data["BANKTRANLIST"]["STMTTRN"]

memos_to_ignore = [
    "Baixa Automatica Fundos",
    "bx Autom Fundos",
    "Aplicacao Fundo Ficfirf di Special",
    "Estorno Lancto* Ficfirf di Special",
    "APLICACAO EM FUNDOS B. FIC FI RF MACRO",
    "BX AUTOMATICA APLICACOES",
    "BAIXA AUTOMAT POUPANCA*",
    "BAIXA AUTOMATICA FUNDOS",
    "RESGATE FUNDOS FIC FI R.FIXA MARTE",
    "ESTORNO DE LANCAMENTO* B. FIC FI RF MACRO",
    "APLIC.INVEST FACIL",
    "RESGATE INVEST FACIL"
    ]

memos_to_only_care_about_the_prefix = [
    "TARIFA REGISTRO COBRANCA QUANDO DO REGISTRO",
    "CONTA DE GAS COMGAS/SP",
    "TAR COMANDADA COBRANCA POR MOTIVO DE DEVOLUCAO",
    "CONTA DE LUZ ELETROPAULO/SP",
    "DOC/TED INTERNET",
    "TAR COMANDADA COBRANCA",
    "TARIFA REGISTRO COBRANCA",
    "TARIFA AUTORIZ COBRANCA TIT.BX.DECURSO PRAZO"
    ]

memos_to_replace = {
    "TRANSF CC PARA CC PJ GENILDO DE OLIVEIRA CRUZ" : "GASTO COM FUNCIONARIO",
    "TRANSF CC PARA CC PJ GILDEMAR FERREIRA S" : "GASTO COM FUNCIONARIO",
    "TRANSF CC PARA CC PJ JOAO RODRIGUES" : "GASTO COM FUNCIONARIO",
    "TRANSF CC PARA CC PJ VALDEIR BRAZ DE SOUZA" : "GASTO COM FUNCIONARIO",
    "TED DIF.TITUL.CC H.BANK DEST. JOSINALDO ALEXANDRE" : "GASTO COM FUNCIONARIO",
    "TED DIF.TITUL.CC H.BANK DEST. Josinaldo  Alexandre": "GASTO COM FUNCIONARIO",
    "TRANSF CC PARA CP PJ SEBASTIAO  RODRIGUES  DE S" : "GASTO COM FUNCIONARIO",
    "TRANSF CC PARA CP PJ VANDERLEI PEREIRA DOURADO" : "GASTO COM FUNCIONARIO",
    "BRADESCO NET EMPRESA NET EMPRESA DARF 0561" : "GASTO COM FUNCIONARIO",
    "BRADESCO NET EMPRESA NET EMPRESA DARF 8301" : "GASTO COM FUNCIONARIO",
    "PAGTO ELETRONICO TRIBUTO INTERNET --DARF": "GASTO COM FUNCIONARIO",
    "PAGTO ELETRONICO TRIBUTO INTERNET - PESS GPS 2100": "GASTO COM FUNCIONARIO",
    "PAGTO ELETRONICO TRIBUTO INTERNET --FGTS/GRF S/TOMADOR": "GASTO COM FUNCIONARIO",
    "PAGTO ELETRONICO TRIBUTO INTERNET --FGTS/GRF S/TOMADO": "GASTO COM FUNCIONARIO",
    "PAGTO ELETRONICO TRIBUTO INTERNET --PMSP SP": "IPTU",
    "TRANSF CC PARA CC PJ ZITA DE OLIVEIRA PENNA" : "SINDICO",
    "TRANSF FDOS DOC-E H BANK DEST.Celso do Santos": "TED DIF.TITUL.CC H.BANK DEST. Celso dos Santos",
    "TED DIF.TITUL.CC H.BANK DEST. Celso do Santos": "TED DIF.TITUL.CC H.BANK DEST. Celso dos Santos",
    "DOC/TED INTERNET" : "GASTOS BANCARIOS",
    "TARIFA BANCARIA CESTA PJ 2" : "GASTOS BANCARIOS",
    "TAR COMANDADA COBRANCA" : "GASTOS BANCARIOS",
    "TARIFA REGISTRO COBRANCA" : "GASTOS BANCARIOS",
    "TARIFA AUTORIZ COBRANCA TIT.BX.DECURSO PRAZO": "GASTOS BANCARIOS",
    "LIQUIDACAO DE COBRANCA VALOR DISPONIVEL" : "LIQUIDACAO DE COBRANCA Valor Disponivel"

}

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
        return self.__class__, args, None, None, self.items()

    def __repr__(self):  # optional
        return '%s(%r, %r)' % (self.__class__.__name__, self.default_factory,
                               list(self.iteritems()))

from json import JSONEncoder
class MyEncoder(JSONEncoder):
    def default(self, o):
        for key, value in o.__dict__.items():
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
        self.original_name = stmtrn["_original_name"]
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
        self.items = []

    def add_item(self, item):
        self.items.append(item)
        self.add_value(item.amount)

    def add_value(self, value):
        self.total += value
        self.count += 1

    def make_notes(self):
        output = ""
        for stmtrn in self.items:
            date = stmtrn.date[0:stmtrn.date.find(" ")]
            output += "{}  {:10.2f}  {}\n".format(
                date,
                stmtrn.amount,
                stmtrn.original_name,
            )
        return output


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
            self.credits[item.memo].add_item(item)
            #self.credits[item.memo].add_value(item.amount)
        else:
            self.total_debit += item.amount
            self.debits[item.memo].add_item(item)
            # self.debits[item.memo].add_value(item.amount)

class ReturnAndIncrement():
    def __init__(self, initial_value=0):
        self.value = initial_value

    def reset(self):
        self.value = 0

    def set(self, value):
        self.value = value

    def bump(self, value=1):
        return_value = self.value
        self.value += value
        return return_value

    def get(self):
        return self.value


class XlsxMensal():
    def __init__(self, target_file_name, statement):
        self.row = 0
        self.col = 0
        self.target_file_name = target_file_name
        self.statement = statement
        self.worksheet = None

    def go(self):
        import xlsxwriter
        with xlsxwriter.Workbook(self.target_file_name) as workbook:
            bold = workbook.add_format({'bold': True})
            money = workbook.add_format({'num_format': '#,##0'})
            self.worksheet = workbook.add_worksheet()

    def _add_cell(self, *param):
        self.worksheet.write(self.row, self.col, *param)
        self.col += 1

    def _newline(self):
        self.row = 0
        self.col = 0

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

    def to_xlsx_grouped(self, source_file, sufix):
        import xlsxwriter

        target_file_name = source_file[0:source_file.rfind(".")] + sufix
        print("Saving {}".format(target_file_name))

        with xlsxwriter.Workbook(target_file_name) as workbook:
            bold = workbook.add_format({'bold': True})
            bold.set_align("center")

            red = workbook.add_format({'font_color': 'red'})
            black = workbook.add_format({'font_color': 'black'})

            money = workbook.add_format({'num_format': '#,##0.00;[Red]-#,##0.00;#,##0.00'})
            percent = workbook.add_format({'num_format': '0.00%'})
            comment_format_line_size = 20
            comment_format = {'width': 700, 'height': comment_format_line_size}

            worksheet = workbook.add_worksheet()
            worksheet.set_landscape()
            worksheet.set_header()
            statement_date = "{} ~ {}".format(
                self.first_statement[0:self.first_statement.find(" ")],
                self.last_statement[0:self.last_statement.find(" ")],
            )
            worksheet.set_footer("&L" + target_file_name + "&C" + statement_date + '&RPage &P of &N')
            worksheet.repeat_rows(0)  # Repeat the first row.
            worksheet.set_margins(left=0.4, right=0.4, top=0.4)

            worksheet.set_column(1, 1, 70)
            worksheet.set_column(2, 4, 12)
            worksheet.set_column(7, 9, 13)

            headers = ["Período", "Descrição", "Quantidade", "Crédito", "Débito", "%", "", "Soma Crédito", "Soma Débito", "Diferença"]
            col = ReturnAndIncrement()
            row = ReturnAndIncrement()
            for header in headers:
                worksheet.write(row.get(), col.bump(), header, bold)
            row.bump()

            for period_name in self.periods:
                statement_period = self.periods[period_name]
                soma_credito = 0
                soma_debito = 0

                for name in sorted(statement_period.credits):
                    statement_memo = statement_period.credits[name]
                    soma_credito += statement_memo.total

                    col.reset()
                    worksheet.write(row.get(), col.bump(), period_name)
                    if statement_memo.count > 1:
                        comment_format["height"] = comment_format_line_size * statement_memo.count
                        worksheet.write_comment(row.get(), col.get(), statement_memo.make_notes(), comment_format)
                    worksheet.write(row.get(), col.bump(), name) # descricao
                    worksheet.write(row.get(), col.bump(), statement_memo.count) #quantidade
                    worksheet.write(row.get(), col.bump(), statement_memo.total, money) # credito
                    row.bump()

                for name in statement_period.debits:
                    statement_memo = statement_period.debits[name]
                    soma_debito += statement_memo.total

                for name in sorted(statement_period.debits):
                    statement_memo = statement_period.debits[name]
                    percent_value = statement_memo.total / soma_debito

                    col.reset()
                    worksheet.write(row.get(), col.bump(), period_name)
                    if statement_memo.count > 1:
                        comment_format["height"] = comment_format_line_size * statement_memo.count
                        worksheet.write_comment(row.get(), col.get(), statement_memo.make_notes(), comment_format)
                    worksheet.write(row.get(), col.bump(), name) # descricao
                    worksheet.write(row.get(), col.bump(), statement_memo.count) #quantidade
                    col.bump() # credito
                    worksheet.write(row.get(), col.bump(), statement_memo.total, money) # debito
                    worksheet.write(row.get(), col.bump(), percent_value, percent)  # percent
                    row.bump()


                delta = (abs(soma_credito) - abs(soma_debito))
                descricao = "Total Crédito: {:15,.2f} Débito: {:15,.2f} Diferença: {:15,.2f}".format(
                    soma_credito,
                    soma_debito,
                    delta)

                col.reset()
                worksheet.write(row.get(), col.bump(), period_name)
                # worksheet.write(row.get(), col.bump(), descricao)  # descricao


                credit_color = black
                if soma_credito < 0:
                    credit_color = red
                debit_color = black
                if soma_debito < 0:
                    debit_color = red
                delta_color = black
                if delta < 0:
                    delta_color = red

                worksheet.write_rich_string(row.get(), col.bump(),
                                            "Total Crédito: ", credit_color, "{:15,.2f}".format(soma_credito),
                                            " Débito: ", debit_color, "{:15,.2f}".format(soma_debito),
                                            " Diferenca: ", delta_color, "{:15,.2f}".format(delta)
                                            )  # descricao


                col.bump(5)
                worksheet.write(row.get(), col.bump(), soma_credito, money)  # Soma Crédito
                worksheet.write(row.get(), col.bump(), soma_debito, money)  # Soma Débito
                worksheet.write(row.get(), col.bump(), delta, money)  # Diferença
                row.bump()
                
                row.bump()

            worksheet.print_area("A1:F{}".format(row.get()))


    def to_xlsx_mensal(self, source_file, sufix):
        import xlsxwriter

        target_file_name = source_file[0:source_file.rfind(".")] + sufix
        print("Saving {}".format(target_file_name))


        with xlsxwriter.Workbook(target_file_name) as workbook:
            bold = workbook.add_format({'bold': True})
            money = workbook.add_format({'num_format': '#,##0.00;[Red]-#,##0.00;#,##0.00'})

            worksheet = workbook.add_worksheet()
            worksheet.set_column(0, 4, 12)

            headers = ["periodo", "entrada", "saida", "delta"]
            col = ReturnAndIncrement()
            row = ReturnAndIncrement()
            for header in headers:
                worksheet.write(row.get(), col.bump(), header, bold)
            row.bump()

            col.reset()
            worksheet.write(row.get(), col.bump(), "total", bold)
            worksheet.write(row.get(), col.bump(), self.total.total_credit, money)
            worksheet.write(row.get(), col.bump(), self.total.total_debit, money)
            worksheet.write(row.get(), col.bump(), self.total.delta, money)
            row.bump()

            for period_name in sorted(self.periods.keys()):
                col.reset()
                item = self.periods[period_name]
                worksheet.write(row.get(), col.bump(), period_name, money)
                worksheet.write(row.get(), col.bump(), item.total_credit, money)
                worksheet.write(row.get(), col.bump(), item.total_debit, money)
                worksheet.write(row.get(), col.bump(), item.delta, money)
                row.bump()

    def to_csv_mensal(self):
        forma = "'{periodo}{sep}{entrada}{sep}{saida}{sep}{delta}{lf}"
        output = ""
        sep = ","
        lf = "\n"
        output += "periodo{sep}entrada{sep}saida{sep}delta{lf}".format(sep=sep, lf=lf)
        output += forma.format(sep=sep, lf=lf, periodo="total", entrada=self.total.total_credit, saida=self.total.total_debit, delta=self.total.delta)

        for period_name in sorted(self.periods.keys()):
            item = self.periods[period_name]
            output += forma.format(sep=sep, lf=lf,
                                   periodo=period_name,
                                   entrada=item.total_credit,
                                   saida=item.total_debit,
                                   delta=item.delta)
        return output

    def to_csv_grouped(self):
        #periodo	evento	quantidade	debito	credito

        forma  = "'{periodo}{sep}{descricao}{sep}{quantidade}{sep}{credito}{sep}{debito}{sep}{percent}{lf}"
        forma_final = "'{periodo}{sep}{descricao}{sep}{sep}{sep}{sep}{sep}{sep}{soma_credito}{sep}{soma_debito}{sep}{delta}{lf}"
        sep = ","
        lf = "\n"

        output = "Período{sep}Descrição{sep}Quantidade{sep}Crédito{sep}Débito{sep}%{sep}{sep}Soma Crédito{sep}Soma Débito{sep}Diferença{lf}".format(lf=lf,sep=sep)

        for period_name in self.periods:
            statement_period = self.periods[period_name]
            soma_credito = 0
            soma_debito = 0

            for name in sorted(statement_period.credits):
                statement_memo = statement_period.credits[name]
                fixed_name = name.replace(sep,"")
                soma_credito += statement_memo.total
                output += forma.format(sep=sep, lf=lf, periodo=period_name, descricao=fixed_name, quantidade=statement_memo.count,
                                       debito="", credito=statement_memo.total, percent="")

            for name in statement_period.debits:
                statement_memo = statement_period.debits[name]
                soma_debito += statement_memo.total

            for name in sorted(statement_period.debits):
                statement_memo = statement_period.debits[name]
                fixed_name = name.replace(sep, "")
                percent = statement_memo.total/soma_debito
                output += forma.format(sep=sep, lf=lf, periodo=period_name, descricao=fixed_name, quantidade=statement_memo.count,
                                       credito="", debito=statement_memo.total, percent=percent)

            delta = (abs(soma_credito)-abs(soma_debito))
            descricao = "\"Total Crédito: {:15,.2f} Débito: {:15,.2f} Diferença: {:15,.2f}\"".format(soma_credito, soma_debito, delta)
            output += forma_final.format(sep=sep, lf=lf, periodo=period_name, descricao=descricao,
                                         soma_debito=soma_debito, soma_credito=soma_credito, delta=delta)
            output += lf

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
    memo = item["_original_name"] = item["MEMO"]

    if memo in memos_to_ignore:
        continue

    for memo_to_only_care_about_the_prefix in memos_to_only_care_about_the_prefix:
        if memo.startswith(memo_to_only_care_about_the_prefix):
            memo = item["MEMO"] = memo_to_only_care_about_the_prefix

    if memo in memos_to_replace:
        memo = item["MEMO"] = memos_to_replace[memo]

    if memo in memos_to_ignore:
        continue

    inputs["TRNTYPE"][item["TRNTYPE"]] += 1
    inputs["MEMO_{}".format(item["TRNTYPE"])][item["MEMO"]] += 1
    statement_item = StatementItem(item)

    output.add_statement_item(statement_item)
    # print(x.get_period())


def save_target_file(source_file, sufix, content):
    target_file_name = source_file[0:source_file.rfind(".")] + sufix
    print("Saving {}".format(target_file_name))
    with codecs.open(target_file_name, "w", "utf-8-sig") as output_file:
        output_file.write(content)

save_target_file(source_file, "_processed.json", output.to_json())
save_target_file(source_file, "_mensal.csv", output.to_csv_mensal())
save_target_file(source_file, "_grouped.csv", output.to_csv_grouped())
output.to_xlsx_mensal(source_file, "_mensal.xlsx")
output.to_xlsx_grouped(source_file, "_grouped.xlsx")

print("Done")
