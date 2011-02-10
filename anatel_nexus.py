#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""One-line documentation for anatel_nexus module.

A detailed description of anatel_nexus.
"""

__author__ = 'macambira@google.com (Tiago Macambira)'

# a python readability reviewer would cry of horor of the code below...
import sys
from time import strftime, localtime, sleep
from urllib import urlencode
import urllib2

from BeautifulSoup import BeautifulSoup
import pynotify

data_urlencoded='pTipo=&NumCertificado=&NumCertificado2=&CodHomologacao=&Data1=&Data2=&Periodo1=&Periodo2=&CodSolicitante=&nomeSolicitante=&ComparacaoSolicitante=i&CodFabricante=&nomeFabricante=samsung&ComparacaoFabricante=i&NumProcesso=&CodOCD=&CodServico=&CodTipo=ZM&IdtModalidadeAplicacao=&DescModelo=GT-I90&acao=h&chave=&'
anatel_url = 'http://sistemas.anatel.gov.br/sgch/Consulta/Homologacao/tela.asp'

#data=dict([ keyval.split('=')  for keyval in x.split('&') if keyval])

#def main(argv):

def StripScript(soup):
    "remove all those script tags -- they will hurt us more than help us"
    while soup.script:
        _ = soup.script.extract()
    return soup

def GetParentByTag(node, name):
    while node.name != name:
        node = node.parent
    return node

def ParseTable(node):
    rows = []
    for row in node.findAll('tr'):
        columns=[]
        for col in row.findAll(['th', 'td']):
            text = u"".join([unicode(data).strip() 
                            for data in col.findAll(recursive=True,text=True)])
            columns.append(text)
        rows.append(columns)
    return rows

def ParsedTableToHTML(table):
    res = """<html>
    <head>
        <title>Celulares Serie GT-9xxx da Samsung</title>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" >
    </head>
    <body>"""+ unicode(res_table).encode('utf-8') + """</body></html>"""


def ParsedTableToStr(plain_table):
    res = []
    for line in plain_table:
        for col in line:
            res.append(u"%30s|" % (col,))
        res.append(u"\n")
    return u"".join(res)

def GetPage():
    fh = urllib2.urlopen(anatel_url,data_urlencoded,120)
    #fh=open('anatel.data','r')
    page_data = fh.read().decode('latin1')
    return page_data

def ExtractHtmlTable(page_data):
    """We assume page_data to be a unicode str or trivially convertible to
    unicode.
    """
    page = BeautifulSoup(unicode(page_data))
    # Get to the cheese
    res_table_th = page.find('th', 'SubTituloCentro')
    res_table = GetParentByTag(res_table_th, 'table')
    StripScript(res_table)
    #remove Extra crap
    pagination_td = res_table.find('td','SubTituloEsquerda')
    _ = GetParentByTag(pagination_td,'table').extract()
    return res_table


def NotifyLoop(timeout=300):
    pynotify.init("nexus S watcher")
    while True:
        print strftime("%Y-%m-%d %H:%M:%S", localtime())
        page_data = GetPage()
        res_table = ExtractHtmlTable(page_data)
        plain_table = ParseTable(res_table)
        # remove header and galaxy S
        left = [prod for prod in plain_table[1:] if prod[2] <> u'GT-I9000B' ]
        if left:
            (homologation, sitar, model, file_id, maker, kind, validity) = \
                    left[0]
            print left
            n = pynotify.Notification("Nexus S","Nexus S is out!")
            n.set_timeout(timeout)
            n.show()
        else:
            print "\tnothig so far..."
        sleep(timeout)


def main():
    page_data = GetPage()
    res_table = ExtractHtmlTable(page_data)
    plain_table = ParseTable(res_table)
    # remove header and galaxy S
    #print ParsedTableToStr(plain_table)
    left = [prod for prod in plain_table[1:] if prod[2] != u'GT-I9000B' ]
    if left: print left

if __name__ == '__main__':
    #main()
    NotifyLoop()
