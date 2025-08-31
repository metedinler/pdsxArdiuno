import re
import logging

# Loglama yapılandırması
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Token sınıfını pdsx_parser.py dosyasından import ediyoruz
from pdsx_parser import Token

# TOKEN_SPECIFICATIONS güncellendi
TOKEN_SPECIFICATIONS = [
    # Yorum satırları için en üstte yer almalı ki diğer pattern'lerle çakışmasın
    ('COMMENT_REM', r'REM.*'), # REM anahtar kelimesi ile başlayan yorumlar
    ('COMMENT_HASH', r'#.*'),  # # karakteri ile başlayan yorumlar
    ('COMMENT_SLASH', r'\/\/.*'), # // karakteri ile başlayan yorumlar (mevcut C++ tarzı)

    ('WHITESPACE', r'\s+'),
    
    # Yeni ve Genişletilmiş Operatörler
    # Mantıksal Operatörler (Anahtar Kelimeler)
    ('LOGICAL_KEYWORD_OPERATOR', r'(AND|OR|NOT|NAND|NOR|XOR|EQV|IMP)\b'), 
    
    # Karşılaştırma Operatörleri
    ('COMPARISON_OPERATOR', r'(\=\=|\!\=|\<\=|\>\=|\<|\>)'),
    
    # Atama ve Artırma/Azaltma Operatörleri
    ('ASSIGNMENT_OPERATOR', r'(\+\+|\-\-|\+\=|\-\=|\*\=|\/\=|\%\=|&\=|\|\=|\^\=|\<\<\=|\>\>\=|\=)'), # = eklendi en sona
    
    # Aritmetik, Bitwise ve Diğer Operatörler
    ('OPERATOR', r'(\+|\-|\*|\/|\%|&|\||\^|\~|\<\<|\>\>)'), # &, |, ^, ~, <<, >> eklendi (Bitwise)

    ('PUNCTUATION', r'[\(\),:\[\]]'),
    ('STRING', r'"[^"]*"'),
    ('NUMBER', r'\b\d+(\.\d*)?\b'), # Tam sayılar ve ondalık sayılar
    
    # Anahtar Kelimeler (Alfabetik sıraya göre düzenlenebilir, okunabilirliği artırmak için)
    ('KEYWORD', r'\b(ABS|ADC|ALIAS|AND|AS|BEGIN|BUZZER|CALL|CASE|CATCH|CHANGE|CLASS|CONFIGURE|CONNECT|COS|COUNT|DATA|DEFINE|DELAY|DEQUEUE|DIM|DIGITALWRITE|DO|DUTY|ELSE|END|ENQUEUE|EQV|EVENT|EXIT|FALLING|FALSE|FOR|FREQUENCY|FUNC|GOSUB|GOTO|HARDWARE|HIGH|IF|IMP|INFO|INHERITS|INPUT|INTERVAL|INTERRUPT|INTO|LOOP|LOW|LOG|MAP|MEAN|MEDIAN|MOVE|NAND|NEXT|NOR|NOT|NROOT|OF|OFF|ON|OR|OUTPUT|PIN|POINTER|POP|POW|PRIVATE|PROGRAM|PUBLIC|PUSH|PWM|QUEUE|READ|RESOLUTION|RESTORE|RETURN|RISING|ROUND|SELECT|SERIAL|SERVO|SET|SIN|SINGLE|SIZE|SQRT|STACK|STEP|STDDEV|SUB|TAN|THEN|THROW|TIMER|TO|TRUE|TRY|TYPE|UNTIL|VARIANCE|WHILE|WIFI)\b'),
    
    ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
]

class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.line_start_pos = 0 # Her satırın başlangıç pozisyonunu takip etmek için

    def tokenize(self):
        while self.pos < len(self.code):
            matched = False
            current_line_start = self.pos - (self.column - 1) # Güncel satırın başlangıç pozisyonu

            for token_type, pattern in TOKEN_SPECIFICATIONS:
                regex = re.compile(pattern, re.IGNORECASE)
                match = regex.match(self.code, self.pos)

                if match:
                    value = match.group(0)
                    if token_type == 'WHITESPACE':
                        for char in value:
                            if char == '\n':
                                self.line += 1
                                self.column = 1
                                self.line_start_pos = self.pos + value.find('\n') + 1 # Yeni satırın başlangıcı
                            else:
                                self.column += 1
                    elif token_type.startswith('COMMENT'): # Tüm yorum tipleri için
                        # Yorumun içinde kaç satır atlandığını hesapla
                        num_newlines = value.count('\n')
                        self.line += num_newlines
                        if num_newlines > 0:
                            self.column = len(value.split('\n')[-1]) + 1
                        else:
                            self.column += len(value)
                    else:
                        # Token'ın başlangıç sütununu doğru hesapla
                        # Bu sütun, token'ın bulunduğu satırın başından itibaren olan uzaklıktır.
                        token_start_column = self.column
                        self.tokens.append(Token(token_type, value, self.line, token_start_column))
                        self.column += len(value)
                    self.pos = match.end()
                    matched = True
                    break
            
            if not matched:
                # Hata durumunda, hatanın satır ve sütun bilgisini doğru ver
                error_char = self.code[self.pos]
                error_line = self.line
                error_column = self.column # Hata anındaki güncel sütun
                raise SyntaxError(f"Beklenmeyen Karakter '{error_char}' (Satır:{error_line}, Sütun:{error_column})")
        return self.tokens