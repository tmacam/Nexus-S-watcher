#!/usr/bin/python
#
# Copyright 2011 Tiago Alves Macambira. All Rights Reserved.

"""Watches for Nexus S approval by Brazil's FCC (Anatel).

We periodically scrape Anatel's homologation search page for approved Samsung
mobile phones from the GT-i90XXx series. We exclude the Samsung Galaxy S from
the result and, if anything is left, we say that this is (supposedly) the Nesus
S.
"""

__author__ = 'tmacam@burocrata.org (Tiago Alves Macambira)'
__license__ = """Copyright (C) 2011 by Tiago Alves Macambira

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE."""


import optparse
import time
import urllib2

from BeautifulSoup import BeautifulSoup
import pynotify


URL_ENCODED_DATA = ('pTipo=&'
                    'NumCertificado=&'
                    'NumCertificado2=&'
                    'CodHomologacao=&'
                    'Data1=&'
                    'Data2=&'
                    'Periodo1=&'
                    'Periodo2=&'
                    'CodSolicitante=&'
                    'nomeSolicitante=&'
                    'ComparacaoSolicitante=i&'
                    'CodFabricante=&'
                    'nomeFabricante=samsung&'
                    'ComparacaoFabricante=i&'
                    'NumProcesso=&'
                    'CodOCD=&'
                    'CodServico=&'
                    'CodTipo=ZM&'
                    'IdtModalidadeAplicacao=&'
                    'DescModelo=GT-I90&'
                    'acao=h&'
                    'chave=&')

ANATEL_URL = 'http://sistemas.anatel.gov.br/sgch/Consulta/Homologacao/tela.asp'

KNOWN_GALAXY_MODELS = set([u'GT-I9000B', u'GT-I9003B'])

class EmptyPageError(Exception):
    pass


def StripScript(soup):
    """Remove all those script tags -- they will hurt us more than help us."""
    while soup.script:
        _ = soup.script.extract()
    return soup


def GetParentByTag(node, name):
    while node.name != name:
        node = node.parent
    return node


def ParseTable(node):
    """Convert the result HTML table into a list of lists representation."""
    rows = []
    for row in node.findAll('tr'):
        columns = []
        for col in row.findAll(['th', 'td']):
            text = u''.join([unicode(data).strip()
                             for data in col.findAll(recursive=True,
                                                     text=True)])
            columns.append(text)
        rows.append(columns)
    return rows


def ParsedTableToHTML(table):
    res = """<html>
    <head>
        <title>Celulares Serie GT-9xxx da Samsung</title>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" >
    </head>
    <body>"""+ unicode(table).encode('utf-8') + """</body></html>"""
    return res


def ParsedTableToStr(plain_table):
    res = []
    for line in plain_table:
        for col in line:
            res.append(u'%30s|' % (col,))
        res.append(u'\n')
    return u''.join(res)


def GetResultPage(filename):
    if filename:
        fh = open(filename, 'r')
    else:
        fh = urllib2.urlopen(ANATEL_URL, URL_ENCODED_DATA, 120)
    #fh=open('anatel.data','r')
    page_data = fh.read().decode('latin1')
    if not page_data:
        raise EmptyPageError()
    return page_data


def ExtractResultTable(page_data):
    """Extract the result table node from the result page.

    Args:
      page_data: raw result from the server.  We assume it to be a
        unicode str or trivially convertible to unicode.

    Returns:
      the result table node.
    """
    page = BeautifulSoup(unicode(page_data))
    # Get to the cheese
    res_table_th = page.find('th', 'SubTituloCentro')
    res_table = GetParentByTag(res_table_th, 'table')
    StripScript(res_table)
    #remove Extra crap
    pagination_td = res_table.find('td', 'SubTituloEsquerda')
    _ = GetParentByTag(pagination_td, 'table').extract()
    return res_table


def FilterOutKnownModels(plain_table):
    # Remove Header
    models = plain_table[1:]
    return [prod for prod in models if prod[2] not in KNOWN_GALAXY_MODELS]


def NotifyLoop(filename, timeout):
    """Periodically revisit Anatel's results and notify if Nexus S is found."""
    pynotify.init('nexus S watcher')
    while True:
        print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        try:
            page_data = GetResultPage(filename)
            res_table = ExtractResultTable(page_data)
            plain_table = ParseTable(res_table)
            # remove header and galaxy S
            left = FilterOutKnownModels(plain_table)
            if left:
                #(homologation, sitar, model, file_id, maker, kind,
                # validity) = left[0]
                print left
                n = pynotify.Notification('Nexus S', 'Nexus S is out!')
                n.set_timeout(timeout)
                n.show()
            else:
                print '\tnothing so far...'
        except EmptyPageError:
            print '\tOops! Page returned empty!'
        except urllib2.URLError as error:
            print "\turllib2.URLError:", error
        time.sleep(timeout)


def MakeOptionParser():
    """Buils and returns the command line option parser."""
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file', dest='filename', default=None,
                      metavar='FILE',
                      help=('Parse result from FILE instead of fetching '
                            'from the network. If not provided (the default), '
                            'it will fetch from the network'))
    parser.add_option('-o', '--stdout', action='store_true',
                      dest='stdout', default=False,
                      help=('Run once and output result to stdout instead '
                            'of using notifications. Not the default.'))
    parser.add_option('-l', '--list', action='store_true',
                      dest='list', default=False,
                      help=('List all fones from the GT-I90xx series. '
                            'Requires -o.'))
    parser.add_option('-t', '--timeout', dest='timeout', default=300,
                      metavar='SECS',
                      help=('How frequently, in seconds, we pull new results '
                            'from Anatel\'s servers.'))

    return parser


def VerifyAndPrintToStdout(filename, list_all_found):
    page_data = GetResultPage(filename)
    res_table = ExtractResultTable(page_data)
    plain_table = ParseTable(res_table)
    if list_all_found:
        print ParsedTableToStr(plain_table)
    # remove header and galaxy S
    left = FilterOutKnownModels(plain_table)
    if left: print left


def main():
    parser = MakeOptionParser()
    opts, unused_args = parser.parse_args()
    if opts.stdout:
        VerifyAndPrintToStdout(opts.filename, opts.list)
    else:
        NotifyLoop(opts.filename, opts.timeout)


if __name__ == '__main__':
    main()
