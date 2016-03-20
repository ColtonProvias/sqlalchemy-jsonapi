import re
from collections import OrderedDict

TESTS = {
    'email == "cj@coltonprovias.com"': 'User.email == "cj@coltonprovias.com"',
    'email.lower() == "cj@coltonprovias.com"': 'User.email.lower() == "cj@coltonprovias.com"',
    'email ilike \'cj@%\'': 'User.email.ilike(\'cj@%\')',
    'published_at!=null': 'User.published_at != None',
    '(5<score<=10)||published_at!=null': '(5 < User.score <= 10) or published_at != None',
    'id in [0, 2.3, 4]': 'User.id in [0, 2.3, 4]',
    'text == "sample == true"': 'User.text == "sample == true"',
    '-missing == 5': '-User.missing == 5'
}

STRING = r"(?P<STRING>('([^'\\]*(?:\\.[^'\\]*)*)'" + r'|"([^"\\]*(?:\\.[^"\\]*)*)"))'

REGEX = [STRING,
    r'(?P<WHITESPACE>\s+)',
    r'(?P<NAME>\b[a-zA-Z_][a-zA-Z0-9_]*\b)',
    r'(?P<PAREN_OPEN>\()',
    r'(?P<PAREN_CLOSE>\))',
    r'(?P<BRACKET_OPEN>\[)',
    r'(?P<BRACKET_CLOSE>\])',
    r'(?P<GT>\>)',
    r'(?P<LT>\<)',
    r'(?P<GTE>\>\=)',
    r'(?P<LTE>\<\=)',
    r'(?P<OR>(\|\||or))',
    r'(?P<AND>(\&\&|and))',
    r'(?P<NOT>(\!|not))',
    r'(?P<IN>in)',
    r'(?P<DOT>\.)',
    r'(?P<COMMA>,)',
    r'(?P<EQUAL>\=\=)',
    r'(?P<NOT_EQUAL>\!\=)',
    r'(?P<ADD>\+)',
    r'(?P<SUBTRACT>\-)',
    r'(?P<MULTIPLY>\*)',
    r'(?P<DIVIDE>\/)',
    r'(?P<FLOOR>\/\/)',
    r'(?P<MODULO>\%)',
    r'(?P<CLARKSON>\*\*)',
    r'(?P<INTEGER>\d+)',
    r'(?P<FLOAT>\d+\.\d+)'
]

###
# EQ
# NE
# LT
# LE
# GT
# GE
# NEG
# GETITEM
# CONCAT
# LIKE
# ILIKE
# IN_
# NOTIN_
# NOTLIKE
# NOTILIKE
# IS_
# ISNOT
# STARTSWITH
# ENDSWITH
# CONTAINS
# MATCH
# ADD
# SUBTRACT
# MULTIPLY
# DIVIDE
# MODULUS
# FLOORDIV

BINARY_OPERATORS = OrderedDict([
    ['EQ', r'(?P<EQ>\=\=)'],
    ['NE', r'(?P<NE>\!\=)']
])


compiled = re.compile(r'|'.join(reversed(REGEX)), re.IGNORECASE)

for test, final in TESTS.items():
    print(test)
    print(final)
    finalized = []
    matched = compiled.finditer(test)
    prev_key = None
    for item in matched:
        key = item.lastgroup
        value = item.group(0)
        print('    {:20}:{}'.format(key, value))
