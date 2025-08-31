# pdsx_parser.py
import logging

# Loglama yapılandırması
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- AST Düğümleri (pdsX tranX.py dosyasından alınmıştır) ---

# Token sınıfı
class Token:
    def __init__(self, type, value, line=None, column=None):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value}, Line:{self.line}, Col:{self.column})"

# Base Node sınıfı
class Node:
    def __init__(self, tokens=None):
        self.tokens = tokens if tokens is not None else []
    def __repr__(self):
        return f"{self.__class__.__name__}"

class Program(Node):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements # List of Statement nodes

class Statement(Node):
    pass

class Expression(Node):
    pass

class VariableDeclaration(Statement):
    def __init__(self, name, var_type, tokens=None):
        super().__init__(tokens)
        self.name = name
        self.var_type = var_type

    def __repr__(self):
        return f"VarDecl({self.name}, {self.var_type})"

class Assignment(Statement):
    def __init__(self, target, value, tokens=None):
        super().__init__(tokens)
        self.target = target # Variable, ArrayAccess, FieldAccess etc.
        self.value = value # Expression node

    def __repr__(self):
        return f"Assignment({self.target}, {self.value})"

class Identifier(Expression):
    def __init__(self, name, tokens=None):
        super().__init__(tokens)
        self.name = name

    def __repr__(self):
        return f"Identifier({self.name})"

class Number(Expression):
    def __init__(self, value, tokens=None):
        super().__init__(tokens)
        self.value = float(value) if '.' in value else int(value)

    def __repr__(self):
        return f"Number({self.value})"

class String(Expression):
    def __init__(self, value, tokens=None):
        super().__init__(tokens)
        self.value = value.strip('"')

    def __repr__(self):
        return f"String({self.value})"

class BinaryOp(Expression):
    def __init__(self, left, op, right, tokens=None):
        super().__init__(tokens)
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"BinOp({self.left}, {self.op}, {self.right})"

class UnaryOp(Expression):
    def __init__(self, op, right, tokens=None):
        super().__init__(tokens)
        self.op = op
        self.right = right

    def __repr__(self):
        return f"UnOp({self.op}, {self.right})"

class FunctionCall(Expression): # Also used for CALL command
    def __init__(self, func_name, args, tokens=None):
        super().__init__(tokens)
        self.func_name = func_name
        self.args = args # List of Expression nodes

    def __repr__(self):
        return f"FuncCall({self.func_name}, Args: {self.args})"

class HardwareCommand(Statement):
    def __init__(self, cmd_type, args, tokens=None):
        super().__init__(tokens)
        self.cmd_type = cmd_type # e.g., "CONFIGURE_PIN", "DEFINE_SERVO"
        self.args = args # List of arguments (can be Expressions or raw values)

    def __repr__(self):
        return f"HwCmd({self.cmd_type}, Args: {self.args})"

class IfStatement(Statement):
    def __init__(self, condition, then_body, else_body=None, tokens=None):
        super().__init__(tokens)
        self.condition = condition # Expression node
        self.then_body = then_body # List of Statement nodes
        self.else_body = else_body # List of Statement nodes

    def __repr__(self):
        return f"If({self.condition}, Then: {len(self.then_body)} cmds, Else: {len(self.else_body) if self.else_body else 0} cmds)"

class LoopStatement(Statement):
    def __init__(self, body, loop_type="DO_LOOP", condition=None, tokens=None):
        super().__init__(tokens)
        self.body = body # List of Statement nodes
        self.loop_type = loop_type # "DO_LOOP", "DO_WHILE", "DO_UNTIL"
        self.condition = condition # Expression node for WHILE/UNTIL

    def __repr__(self):
        return f"Loop({self.loop_type}, {self.condition if self.condition else ''}, Body: {len(self.body)} cmds)"

class ForStatement(Statement):
    def __init__(self, var_name, start_expr, end_expr, step_expr=None, body=None, tokens=None):
        super().__init__(tokens)
        self.var_name = var_name
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.step_expr = step_expr
        self.body = body if body is not None else []

    def __repr__(self):
        return f"For({self.var_name} from {self.start_expr} to {self.end_expr}, Body: {len(self.body)} cmds)"

class SelectCaseStatement(Statement):
    def __init__(self, expr, cases, tokens=None):
        super().__init__(tokens)
        self.expr = expr # Expression node
        self.cases = cases # List of (value, body) tuples

    def __repr__(self):
        return f"SelectCase({self.expr}, Cases: {len(self.cases)})"

class ReturnStatement(Statement):
    def __init__(self, value=None, tokens=None):
        super().__init__(tokens)
        self.value = value # Optional Expression node for return value

    def __repr__(self):
        return f"Return({self.value if self.value else 'void'})"

class FunctionDefinition(Node):
    def __init__(self, name, params, body, return_type="VOID", tokens=None):
        super().__init__(tokens)
        self.name = name
        self.params = params # List of (name, type) tuples
        self.body = body # List of Statement nodes
        self.return_type = return_type

    def __repr__(self):
        return f"FuncDef({self.name}, Params: {self.params}, Return: {self.return_type}, Body: {len(self.body)} cmds)"

class EventDefinition(Node):
    def __init__(self, name, params, body, tokens=None):
        super().__init__(tokens)
        self.name = name
        self.params = params # List of (name, type) tuples
        self.body = body # List of Statement nodes

    def __repr__(self):
        return f"EventDef({self.name}, Params: {self.params}, Body: {len(self.body)} cmds)"

class SubDefinition(Node):
    def __init__(self, name, params, body, tokens=None):
        super().__init__(tokens)
        self.name = name
        self.params = params # List of (name, type) tuples
        self.body = body # List of Statement nodes

    def __repr__(self):
        return f"SubDef({self.name}, Params: {self.params}, Body: {len(self.body)} cmds)"

class StructDefinition(Node):
    def __init__(self, name, fields, tokens=None):
        super().__init__(tokens)
        self.name = name
        self.fields = fields # List of (name, type) tuples

    def __repr__(self):
        return f"StructDef({self.name}, Fields: {self.fields})"

class ClassDefinition(Node):
    def __init__(self, name, parent=None, fields=None, methods=None, tokens=None):
        super().__init__(tokens)
        self.name = name
        self.parent = parent
        self.fields = fields if fields is not None else [] # List of (name, type, access) tuples
        self.methods = methods if methods is not None else [] # List of FunctionDefinition nodes

    def __repr__(self):
        return f"ClassDef({self.name}, Parent: {self.parent}, Fields: {len(self.fields)}, Methods: {len(self.methods)})"

class AliasDefinition(Statement):
    def __init__(self, new_name, old_name, tokens=None):
        super().__init__(tokens)
        self.new_name = new_name
        self.old_name = old_name

    def __repr__(self):
        return f"Alias({self.new_name} AS {self.old_name})"

class DataStatement(Statement):
    def __init__(self, values, tokens=None):
        super().__init__(tokens)
        self.values = values # List of Expression nodes

    def __repr__(self):
        return f"Data({self.values})"

class ReadStatement(Statement):
    def __init__(self, target, tokens=None):
        super().__init__(tokens)
        self.target = target # Identifier node

    def __repr__(self):
        return f"Read({self.target})"

class RestoreStatement(Statement):
    def __init__(self, tokens=None):
        super().__init__(tokens)

    def __repr__(self):
        return "Restore"

class StackQueueDefinition(Statement):
    def __init__(self, name, sq_type, tokens=None):
        super().__init__(tokens)
        self.name = name
        self.sq_type = sq_type # "STACK" or "QUEUE"

    def __repr__(self):
        return f"{self.sq_type}Def({self.name})"

class PushPopEnqueueDequeue(Statement):
    def __init__(self, action, value_or_var, collection_name, tokens=None):
        super().__init__(tokens)
        self.action = action # "PUSH", "POP", "ENQUEUE", "DEQUEUE"
        self.value_or_var = value_or_var # Expression for PUSH/ENQUEUE, Identifier for POP/DEQUEUE
        self.collection_name = collection_name # Identifier for stack/queue

    def __repr__(self):
        return f"{self.action}({self.value_or_var} {('TO' if self.action in ['PUSH', 'ENQUEUE'] else 'FROM')} {self.collection_name})"

class TryCatchStatement(Statement):
    def __init__(self, try_body, catch_body, tokens=None):
        super().__init__(tokens)
        self.try_body = try_body
        self.catch_body = catch_body

    def __repr__(self):
        return f"TryCatch(Try: {len(self.try_body)}, Catch: {len(self.catch_body)})"

class ThrowStatement(Statement):
    def __init__(self, message, tokens=None):
        super().__init__(tokens)
        self.message = message

    def __repr__(self):
        return f"Throw({self.message})"

class DelayStatement(Statement):
    def __init__(self, duration, tokens=None):
        super().__init__(tokens)
        self.duration = duration

# Yeni eklenen sınıflar (Array, Stack, Queue için)
class ArrayType(Node):
    def __init__(self, base_type, size=None, tokens=None):
        super().__init__(tokens)
        self.base_type = base_type # INTEGER, STRING vb.
        self.size = size # Opsiyonel boyut ifadesi

class StackType(Node):
    def __init__(self, base_type, size=None, tokens=None):
        super().__init__(tokens)
        self.base_type = base_type
        self.size = size # Opsiyonel boyut ifadesi

class QueueType(Node):
    def __init__(self, base_type, size=None, tokens=None):
        super().__init__(tokens)
        self.base_type = base_type
        self.size = size # Opsiyonel boyut ifadesi

# Eksik sabitler
PDSX_TYPE_MAP = {
    'INTEGER': 'int',
    'STRING': 'String',
    'FLOAT': 'float',
    'BOOLEAN': 'bool',
    'ARRAY': 'array',
    'STACK': 'stack',
    'QUEUE': 'queue'
}

MATH_FUNCTIONS_CPP = {
    'SIN': 'sin',
    'COS': 'cos',
    'TAN': 'tan',
    'SQRT': 'sqrt',
    'ABS': 'abs',
    'POW': 'pow',
    'LOG': 'log',
    'EXP': 'exp',
    'NROOT': 'pow', # N'inci kök: pow(val, 1.0/n)
    'ROUND': 'round',
    'MEAN': 'mean',
    'MEDIAN': 'median'
}

# --- Parser Sınıfı ---
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if self.tokens else None
        self.defined_symbols = {} # Global sembol tablosu (fonksiyonlar, tipler, değişkenler)

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def eat(self, expected_type, expected_value=None):
        if not self.current_token:
            raise SyntaxError(f"Beklenmeyen Giriş Sonu. Beklenen {expected_type} ('{expected_value}')")

        # Yorum satırlarını atla
        while self.current_token.type.startswith('COMMENT'):
            self.advance()
            if not self.current_token:
                raise SyntaxError(f"Beklenmeyen Giriş Sonu. Beklenen {expected_type} ('{expected_value}')")

        # IDENTIFIER beklenirken KEYWORD olması özel durumu (PIN, SERVO, BUZZER, HIGH, LOW gibi)
        if expected_type == 'IDENTIFIER' and self.current_token.type == 'KEYWORD' and \
           self.current_token.value.upper() in ['PIN', 'SERVO', 'BUZZER', 'HIGH', 'LOW', 'INPUT', 'OUTPUT', 'OF', 'TIMER', 'ADC', 'PWM', 'ARRAY', 'STACK', 'QUEUE', 'INTEGER', 'DOUBLE', 'STRING', 'BOOLEAN', 'BYTE', 'SHORT', 'LONG', 'SINGLE']:
            if expected_value is None or self.current_token.value.upper() == expected_value.upper():
                token = self.current_token
                self.advance()
                return token

        # LOGICAL_KEYWORD_OPERATOR, ASSIGNMENT_OPERATOR gibi özel tipleri ele al
        if expected_type in ['LOGICAL_KEYWORD_OPERATOR', 'ASSIGNMENT_OPERATOR', 'OPERATOR']:
            if self.current_token.type == expected_type and \
               (expected_value is None or self.current_token.value.upper() == expected_value.upper()):
                token = self.current_token
                self.advance()
                return token
            else:
                raise SyntaxError(f"Beklenmeyen token: {self.current_token}. Beklenen {expected_type} ('{expected_value}') (Satır:{self.current_token.line}, Sütun:{self.current_token.column})")

        # Genel durum:
        if self.current_token.type == expected_type:
            # expected_value kontrolü - hem string hem liste desteği
            if expected_value is None:
                # Herhangi bir değer kabul
                token = self.current_token
                self.advance()
                return token
            elif isinstance(expected_value, list):
                # Liste halinde değerler - herhangi biri eşleşirse kabul
                if self.current_token.value.upper() in [v.upper() for v in expected_value]:
                    token = self.current_token
                    self.advance()
                    return token
                else:
                    raise SyntaxError(f"Beklenmeyen token: {self.current_token}. Beklenen {expected_type} değerlerinden biri: {expected_value} (Satır:{self.current_token.line}, Sütun:{self.current_token.column})")
            else:
                # Tek string değer kontrolü
                if self.current_token.value.upper() == expected_value.upper():
                    token = self.current_token
                    self.advance()
                    return token
                else:
                    raise SyntaxError(f"Beklenmeyen token: {self.current_token}. Beklenen {expected_type} ('{expected_value}') (Satır:{self.current_token.line}, Sütun:{self.current_token.column})")
        else:
            raise SyntaxError(f"Beklenmeyen token: {self.current_token}. Beklenen {expected_type} ('{expected_value}') (Satır:{self.current_token.line}, Sütun:{self.current_token.column})")

    def peek(self, offset=1):
        idx = self.pos + offset
        while idx < len(self.tokens) and self.tokens[idx].type.startswith('COMMENT'):
            idx += 1 # Yorumları atla
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def parse(self):
        statements = []
        while self.current_token:
            # Yorum satırlarını baştan atla
            if self.current_token.type.startswith('COMMENT'):
                self.advance()
                continue
                
            # Üst düzey tanımlamalar (global scope'ta yer alırlar)
            if self.current_token.type == 'KEYWORD':
                keyword_val = self.current_token.value.upper()
                if keyword_val == 'FUNC':
                    statements.append(self.parse_function_definition())
                elif keyword_val == 'EVENT':
                    statements.append(self.parse_event_definition())
                elif keyword_val == 'SUB':
                    statements.append(self.parse_sub_definition())
                elif keyword_val == 'TYPE':
                    statements.append(self.parse_struct_definition())
                elif keyword_val == 'CLASS':
                    statements.append(self.parse_class_definition())
                elif keyword_val == 'ALIAS':
                    statements.append(self.parse_alias_definition())
                else: # Diğer statement'lar (main program veya loop içinde)
                    statements.append(self.parse_statement())
            else:
                statements.append(self.parse_statement()) # Identifier, number vb. ile başlayan ifadeler

        return Program(statements)

    def parse_statement(self):
        token = self.current_token
        
        # Yorum satırlarını atla
        while token and token.type.startswith('COMMENT'):
            self.advance()
            token = self.current_token
        
        if not token: # Son token yorumsa ve bittiyse
            raise SyntaxError(f"Beklenmeyen Giriş Sonu.")

        if token.type == 'KEYWORD':
            keyword_val = token.value.upper()
            
            if keyword_val == 'DIM':
                self.eat('KEYWORD', 'DIM')
                name_token = self.eat('IDENTIFIER')
                self.eat('KEYWORD', 'AS')
                
                # Değişken tipi ayrıştırma (normal tip veya ARRAY OF/STACK OF/QUEUE OF)
                type_token = self.eat('IDENTIFIER')
                var_type_node = Identifier(type_token.value.upper(), [type_token]) # Varsayılan olarak Identifier
                
                if type_token.value.upper() in ['ARRAY', 'STACK', 'QUEUE']:
                    size_expr = None
                    if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'OF':
                        self.eat('KEYWORD', 'OF')
                        base_type_token = self.eat('IDENTIFIER')
                        
                        # SIZE desteği: ARRAY OF INTEGER SIZE 10
                        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'SIZE':
                            self.eat('KEYWORD', 'SIZE')
                            size_expr = self.parse_expression()
                        
                        if type_token.value.upper() == 'ARRAY':
                            var_type_node = ArrayType(Identifier(base_type_token.value.upper(), [base_type_token]), size_expr, [type_token, base_type_token])
                        elif type_token.value.upper() == 'STACK':
                            var_type_node = StackType(Identifier(base_type_token.value.upper(), [base_type_token]), size_expr, [type_token, base_type_token])
                        elif type_token.value.upper() == 'QUEUE':
                            var_type_node = QueueType(Identifier(base_type_token.value.upper(), [base_type_token]), size_expr, [type_token, base_type_token])
                    else:
                        logging.warning(f"ARRAY/STACK/QUEUE için 'OF' anahtar kelimesi ve eleman tipi bekleniyordu. Varsayılan olarak INTEGER kullanılacak. (Satır:{type_token.line}, Sütun:{type_token.column})")
                        if type_token.value.upper() == 'ARRAY':
                             var_type_node = ArrayType(Identifier("INTEGER"), size_expr, [type_token]) # Varsayılan
                        elif type_token.value.upper() == 'STACK':
                            var_type_node = StackType(Identifier("INTEGER"), size_expr, [type_token])
                        elif type_token.value.upper() == 'QUEUE':
                            var_type_node = QueueType(Identifier("INTEGER"), size_expr, [type_token])
                            
                initial_value = None
                if self.current_token and self.current_token.type == 'ASSIGNMENT_OPERATOR' and self.current_token.value == '=':
                    self.eat('ASSIGNMENT_OPERATOR', '=')
                    initial_value = self.parse_expression()
                
                var_decl = VariableDeclaration(name_token.value, var_type_node, [token, name_token, type_token])
                
                # Eğer initial value varsa, bu bir assignment statement'ı da oluşturur
                if initial_value is not None:
                    # Birden fazla statement döndürebilmek için özel bir yapı kullanmamız gerekiyor
                    # Şimdilik, tek bir VariableDeclaration döndürüp, initial value'yu interpreter'da ele alalım
                    # Bu geçici bir çözüm - gerçek çözüm için MultiStatement wrapper'ı gerekebilir
                    var_decl.initial_value = initial_value
                
                return var_decl

            elif keyword_val == 'SET':
                self.eat('KEYWORD', 'SET')
                
                # SET komutunun hangi türde olduğunu belirlemek için lookahead yap
                # SET PIN ... (donanım komutu) vs SET variable = value (assignment)
                if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'PIN':
                    # Donanım komutu: SET PIN
                    self.eat('KEYWORD', 'PIN')
                    pin_expr = self.parse_expression()
                    self.eat('KEYWORD', 'TO')
                    state_token = self.eat('KEYWORD', ['HIGH', 'LOW'])
                    return HardwareCommand("SET_PIN", [pin_expr, state_token.value.upper()], [token, state_token])
                else:
                    # Variable assignment: SET variable = value veya SET array[index] = value
                    target_token = self.eat('IDENTIFIER')
                    target = Identifier(target_token.value)
                    
                    # Array indexing kontrolü
                    if self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == '[':
                        self.eat('PUNCTUATION', '[')
                        index_expr = self.parse_expression()
                        self.eat('PUNCTUATION', ']')
                        # Array access için string oluştur (daha sonra ArrayAccess AST düğümü kullanılabilir)
                        target = Identifier(f"{target_token.value}[{self._expr_to_str(index_expr)}]", [target_token])
                    
                    # Assignment operatörü
                    self.eat('ASSIGNMENT_OPERATOR', '=')
                    value_expr = self.parse_expression()
                    return Assignment(target, value_expr, [token, target_token])

            elif keyword_val == 'DIGITALWRITE': # Yeni eklenen DigitalWrite desteği
                self.eat('KEYWORD', 'DIGITALWRITE')
                pin_expr = self.parse_expression()
                self.eat('PUNCTUATION', ',')
                value_expr = self.parse_expression()
                return HardwareCommand("DIGITALWRITE", [pin_expr, value_expr], [token])

            elif keyword_val == 'LOG':
                cmd_token = self.eat('KEYWORD', 'LOG')
                # LOG INFO durumunu kontrol et
                if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'INFO':
                    self.eat('KEYWORD', 'INFO')
                message_expr = self.parse_expression()
                return HardwareCommand("LOG_INFO", [message_expr], [cmd_token])
            
            elif keyword_val == 'INFO':
                # Tek başına INFO komutunu da destekle
                cmd_token = self.eat('KEYWORD', 'INFO')
                message_expr = self.parse_expression()
                return HardwareCommand("LOG_INFO", [message_expr], [cmd_token])

            elif keyword_val == 'RETURN':
                self.eat('KEYWORD', 'RETURN')
                value_expr = None
                # Eğer bir sonraki token bir anahtar kelime veya block sonu değilse ifadeyi oku
                if self.current_token and self.current_token.value.upper() not in ['END', 'SUB', 'FUNC', 'EVENT', 'CLASS', 'TYPE', 'LOOP', 'IF', 'SELECT', 'NEXT', 'CASE', 'CATCH']:
                     value_expr = self.parse_expression()
                return ReturnStatement(value_expr, [token])

            elif keyword_val == 'CALL':
                return self.parse_function_call(is_call_command=True)

            elif keyword_val == 'IF':
                return self.parse_if_statement()

            elif keyword_val == 'FOR':
                return self.parse_for_statement()

            elif keyword_val == 'DO':
                return self.parse_loop_statement()

            elif keyword_val == 'SELECT':
                return self.parse_select_case_statement()

            elif keyword_val == 'DATA':
                self.eat('KEYWORD', 'DATA')
                values = []
                while self.current_token and (self.current_token.type in ['NUMBER', 'STRING', 'IDENTIFIER'] or \
                      (self.current_token.type == 'OPERATOR' and self.current_token.value == '-') or \
                      (self.current_token.type == 'LOGICAL_KEYWORD_OPERATOR' and self.current_token.value.upper() in ['TRUE', 'FALSE'])): # Boolean değerleri de DATA'ya eklenebilir
                    values.append(self.parse_expression())
                    if self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ',':
                        self.eat('PUNCTUATION', ',')
                    else:
                        break
                return DataStatement(values, [token])

            elif keyword_val == 'READ':
                self.eat('KEYWORD', 'READ')
                target_id = self.eat('IDENTIFIER')
                return ReadStatement(Identifier(target_id.value), [token, target_id])

            elif keyword_val == 'RESTORE':
                self.eat('KEYWORD', 'RESTORE')
                return RestoreStatement([token])

            elif keyword_val in ['PUSH', 'ENQUEUE']:
                action_token = self.eat('KEYWORD', keyword_val)
                value_expr = self.parse_expression()
                self.eat('KEYWORD', 'TO')
                collection_id = self.eat('IDENTIFIER')
                return PushPopEnqueueDequeue(action_token.value.upper(), value_expr, Identifier(collection_id.value), [action_token, collection_id])

            elif keyword_val in ['POP', 'DEQUEUE']:
                action_token = self.eat('KEYWORD', keyword_val)
                collection_id = self.eat('IDENTIFIER')
                self.eat('KEYWORD', 'INTO')
                var_id = self.eat('IDENTIFIER')
                return PushPopEnqueueDequeue(action_token.value.upper(), Identifier(var_id.value), Identifier(collection_id.value), [action_token, collection_id, var_id])

            elif keyword_val == 'TRY':
                self.eat('KEYWORD', 'TRY')
                try_body = self.parse_block(['CATCH'])
                self.eat('KEYWORD', 'CATCH')
                catch_body = self.parse_block(['END', 'TRY'])
                self.eat('KEYWORD', 'END')
                self.eat('KEYWORD', 'TRY')
                return TryCatchStatement(try_body, catch_body, [token])

            elif keyword_val == 'THROW':
                self.eat('KEYWORD', 'THROW')
                message_expr = self.parse_expression()
                return ThrowStatement(message_expr, [token])

            elif keyword_val == 'DELAY': # DELAY komutu
                self.eat('KEYWORD', 'DELAY')
                duration = self.parse_expression()
                return DelayStatement(duration, [token])
            
            elif keyword_val == 'GOSUB': # GOSUB komutu
                self.eat('KEYWORD', 'GOSUB')
                label = self.eat('IDENTIFIER') # Fonksiyon adı veya etiket
                return FunctionCall(label.value, [], [token]) # Basit bir fonksiyon çağrısı gibi ele alalım şimdilik

            elif keyword_val == 'GOTO': # GOTO komutu
                self.eat('KEYWORD', 'GOTO')
                label = self.eat('IDENTIFIER')
                # GOTO için özel bir düğüm tanımlayabiliriz veya bir istisna fırlatabiliriz.
                # C++'ta goto kullanımı genellikle tercih edilmez.
                # Şimdilik bir HardwareCommand gibi ele alalım, ancak interpreter için farklı bir yapıda olabilir.
                return HardwareCommand("GOTO", [label.value], [token])


            # Donanım Komutları (önceki gibi)
            elif keyword_val == 'HARDWARE':
                self.eat('KEYWORD', 'HARDWARE')
                self.eat('KEYWORD', 'MAP')
                platform_name = self.eat('IDENTIFIER')
                return HardwareCommand("HARDWARE_MAP", [platform_name.value], [token, platform_name])

            elif keyword_val == 'DEFINE':
                self.eat('KEYWORD', 'DEFINE')
                
                # DEFINE sonrası gelen kelimeyi kontrol et (SERVO, BUZZER)
                if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'SERVO':
                    self.eat('KEYWORD', 'SERVO')
                    servo_name = self.eat('IDENTIFIER')
                    self.eat('KEYWORD', 'ON')
                    self.eat('KEYWORD', 'PIN')
                    pin_num = self.parse_expression()
                    return HardwareCommand("DEFINE_SERVO", [servo_name.value, pin_num], [token])
                elif self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'BUZZER':
                    self.eat('KEYWORD', 'BUZZER')
                    self.eat('KEYWORD', 'ON')
                    self.eat('KEYWORD', 'PIN')
                    pin_num = self.parse_expression()
                    return HardwareCommand("DEFINE_BUZZER", [pin_num], [token])
                else:
                    # Diğer DEFINE tipleri IDENTIFIER olarak gelebilir
                    type_name_token = self.eat('IDENTIFIER') 
                    if type_name_token.value.upper() == 'SERVO':
                        servo_name = self.eat('IDENTIFIER')
                        self.eat('KEYWORD', 'ON')
                        self.eat('KEYWORD', 'PIN')
                        pin_num = self.parse_expression()
                        return HardwareCommand("DEFINE_SERVO", [servo_name.value, pin_num], [token, servo_name])
                    elif type_name_token.value.upper() == 'BUZZER':
                        self.eat('KEYWORD', 'ON')
                        self.eat('KEYWORD', 'PIN')
                        pin_num = self.parse_expression()
                        return HardwareCommand("DEFINE_BUZZER", [pin_num], [token, type_name_token])
                    else:
                        raise SyntaxError(f"Tanımsız DEFINE tipi: {type_name_token.value} (Satır:{token.line}, Sütun:{token.column})")

            elif keyword_val == 'CONFIGURE':
                self.eat('KEYWORD', 'CONFIGURE')
                
                # CONFIGURE sonrası gelen kelimeyi kontrol et (PIN, INTERRUPT, TIMER, ADC, PWM)
                if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'PIN':
                    cmd_type_token = self.eat('KEYWORD', 'PIN')
                    pin = self.parse_expression()
                    self.eat('KEYWORD', 'AS')
                    mode = self.eat('KEYWORD', ['INPUT', 'OUTPUT'])
                    return HardwareCommand("CONFIGURE_PIN", [pin, mode.value.upper()], [token, cmd_type_token])
                elif self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'TIMER':
                    cmd_type_token = self.eat('KEYWORD', 'TIMER')
                    timer_id = self.parse_expression()
                    self.eat('KEYWORD', 'INTERVAL')
                    interval = self.parse_expression()
                    self.eat('KEYWORD', 'COUNT')
                    count = self.parse_expression()
                    self.eat('KEYWORD', 'CALL')
                    event_name = self.eat('IDENTIFIER')
                    return HardwareCommand("CONFIGURE_TIMER", [timer_id, interval, count, event_name.value], [token, cmd_type_token])
                else:
                    # INTERRUPT, ADC, PWM gibi diğer komutlar IDENTIFIER olarak gelebilir
                    cmd_type = self.eat('IDENTIFIER')
                    if cmd_type.value.upper() == 'INTERRUPT':
                        pin = self.parse_expression()
                        self.eat('KEYWORD', 'ON')
                        mode = self.eat('KEYWORD', ['RISING', 'FALLING', 'CHANGE'])
                        self.eat('KEYWORD', 'CALL')
                        event_name = self.eat('IDENTIFIER')
                        return HardwareCommand("CONFIGURE_INTERRUPT", [pin, mode.value.upper(), event_name.value], [token, cmd_type])
                    elif cmd_type.value.upper() == 'TIMER':
                        timer_id = self.parse_expression()
                        self.eat('KEYWORD', 'INTERVAL')
                        interval = self.parse_expression()
                        self.eat('KEYWORD', 'COUNT')
                        count = self.parse_expression()
                        self.eat('KEYWORD', 'CALL')
                        event_name = self.eat('IDENTIFIER')
                        return HardwareCommand("CONFIGURE_TIMER", [timer_id, interval, count, event_name.value], [token, cmd_type])
                    elif cmd_type.value.upper() == 'ADC':
                        pin = self.parse_expression()
                        self.eat('KEYWORD', 'RESOLUTION')
                        res = self.parse_expression()
                        return HardwareCommand("CONFIGURE_ADC", [pin, res], [token, cmd_type])
                    elif cmd_type.value.upper() == 'PWM':
                        pin = self.parse_expression()
                        self.eat('KEYWORD', 'FREQUENCY')
                        freq = self.parse_expression()
                        self.eat('KEYWORD', 'DUTY')
                        duty = self.parse_expression()
                        return HardwareCommand("CONFIGURE_PWM", [pin, freq, duty], [token, cmd_type])
                    else:
                        raise SyntaxError(f"Desteklenmeyen CONFIGURE komutu: {cmd_type.value} (Satır:{token.line}, Sütun:{token.column})")

            elif keyword_val == 'READ' and self.peek() and self.peek().value.upper() == 'PIN':
                self.eat('KEYWORD', 'READ')
                self.eat('KEYWORD', 'PIN')
                pin_expr = self.parse_expression()
                self.eat('KEYWORD', 'INTO')
                var_id = self.eat('IDENTIFIER')
                return HardwareCommand("READ_PIN", [pin_expr, var_id.value], [token, var_id])
            
            elif keyword_val == 'SERIAL':
                self.eat('KEYWORD', 'SERIAL')
                self.eat('KEYWORD', 'BEGIN')
                baud = self.parse_expression()
                return HardwareCommand("SERIAL_BEGIN", [baud], [token])

            elif keyword_val == 'BUZZER':
                self.eat('KEYWORD', 'BUZZER')
                action = self.eat('KEYWORD', ['ON', 'OFF'])
                freq = None
                if action.value.upper() == 'ON':
                    freq = self.parse_expression()
                return HardwareCommand("BUZZER_CONTROL", [action.value.upper(), freq], [token])

            elif keyword_val == 'MOVE':
                self.eat('KEYWORD', 'MOVE')
                self.eat('KEYWORD', 'SERVO')
                servo_name = self.eat('IDENTIFIER')
                self.eat('KEYWORD', 'TO')
                pos_expr = self.parse_expression()
                return HardwareCommand("MOVE_SERVO", [servo_name.value, pos_expr], [token])

            elif keyword_val == 'WIFI':
                self.eat('KEYWORD', 'WIFI')
                self.eat('KEYWORD', 'CONNECT')
                ssid = self.parse_expression()
                password = self.parse_expression()
                return HardwareCommand("WIFI_CONNECT", [ssid, password], [token])

            else:
                raise SyntaxError(f"Desteklenmeyen anahtar kelime veya komut: {token.value} (Satır:{token.line}, Sütun:{token.column})")

        # Atama veya C-style tekli/ikili işlem (örn: counter++, var += 5)
        elif token.type == 'IDENTIFIER':
            var_name_token = self.eat('IDENTIFIER')
            next_token = self.current_token
            
            # Array indexleme veya üye erişimi (myArray[0], myObject.field)
            if next_token and next_token.type == 'PUNCTUATION' and next_token.value == '[':
                # Dizi erişimi
                self.eat('PUNCTUATION', '[')
                index_expr = self.parse_expression()
                self.eat('PUNCTUATION', ']')
                # Şimdilik basit bir Identifier olarak döndürelim, Transpiler'da ele alabiliriz.
                # Daha sonra ArrayAccess AST düğümü tanımlanabilir.
                target = Identifier(f"{var_name_token.value}[{self._expr_to_str(index_expr)}]", [var_name_token]) 
            elif next_token and next_token.type == 'PUNCTUATION' and next_token.value == '.':
                # Üye erişimi (myObject.field)
                self.eat('PUNCTUATION', '.')
                member_name = self.eat('IDENTIFIER').value
                # Şimdilik basit bir Identifier olarak döndürelim, Transpiler'da ele alabiliriz.
                # Daha sonra MemberAccess AST düğümü tanımlanabilir.
                target = Identifier(f"{var_name_token.value}.{member_name}", [var_name_token])
            else:
                target = Identifier(var_name_token.value)

            next_token_after_target = self.current_token # Hedef ayrıştırıldıktan sonraki token

            if next_token_after_target and next_token_after_target.type == 'ASSIGNMENT_OPERATOR':
                op_token = self.eat('ASSIGNMENT_OPERATOR')
                if op_token.value in ['++', '--']:
                    return UnaryOp(op_token.value, target, [var_name_token, op_token])
                elif op_token.value == '=': # Basit atama
                    value_expr = self.parse_expression()
                    return Assignment(target, value_expr, [var_name_token, op_token])
                else: # +=, -=, *=, /=, %=, &=, |=, ^=, <<=, >>=
                    value_expr = self.parse_expression()
                    # Bileşik atamayı bir ikili işlem ve atamaya dönüştür (x += 5 -> x = x + 5)
                    simple_op = op_token.value[:-1] # += ise +, *= ise *
                    return Assignment(target, BinaryOp(target, simple_op, value_expr), [var_name_token, op_token])
            elif next_token_after_target and next_token_after_target.type == 'OPERATOR' and next_token_after_target.value == '=':
                self.eat('OPERATOR', '=') # Tek = operatörü
                value_expr = self.parse_expression()
                return Assignment(target, value_expr, [var_name_token])
            else:
                # Tanımlayıcı tek başına bir ifade olabilir (örn: CALL MyFunc gibi bir ifadenin parçası)
                # veya hatalı kullanım olabilir. Şimdilik hata fırlatabiliriz.
                raise SyntaxError(f"Atama veya işlem olmadan beklenmeyen tanımlayıcı '{var_name_token.value}' (Satır:{token.line}, Sütun:{token.column})")

        else:
            raise SyntaxError(f"Deyim için beklenmeyen token: {token} (Satır:{token.line}, Sütun:{token.column})")

    def _expr_to_str(self, expr_node):
        # Sadece hata mesajlarında veya geçici AST düğümü oluşturmada kullanılır.
        # Tam teşekküllü bir ifade dönüştürücü değildir.
        if isinstance(expr_node, Number):
            return str(expr_node.value)
        elif isinstance(expr_node, String):
            return f'"{expr_node.value}"'
        elif isinstance(expr_node, Identifier):
            return expr_node.name
        elif isinstance(expr_node, BinaryOp):
            return f"{self._expr_to_str(expr_node.left)} {expr_node.op} {self._expr_to_str(expr_node.right)}"
        elif isinstance(expr_node, UnaryOp):
            return f"{expr_node.op}{self._expr_to_str(expr_node.right)}"
        elif isinstance(expr_node, FunctionCall):
            args_str = ", ".join([self._expr_to_str(arg) for arg in expr_node.args])
            return f"{expr_node.func_name}({args_str})"
        return str(expr_node) # Bilinmeyen durumlar için

    def parse_expression(self):
        return self._parse_binary_expression(0)

    def _parse_binary_expression(self, precedence):
        left = self._parse_unary_expression()

        while self.current_token and \
              ((self.current_token.type == 'OPERATOR' and self._get_precedence(self.current_token.value) >= precedence) or \
               (self.current_token.type == 'LOGICAL_KEYWORD_OPERATOR' and self._get_precedence(self.current_token.value.upper()) >= precedence) or \
               (self.current_token.type == 'COMPARISON_OPERATOR' and self._get_precedence(self.current_token.value) >= precedence)):
            
            op_token = self.current_token
            if op_token.type == 'OPERATOR':
                self.eat('OPERATOR', op_token.value)
            elif op_token.type == 'LOGICAL_KEYWORD_OPERATOR':
                self.eat('LOGICAL_KEYWORD_OPERATOR', op_token.value)
            elif op_token.type == 'COMPARISON_OPERATOR':
                self.eat('COMPARISON_OPERATOR', op_token.value)
            
            right = self._parse_binary_expression(self._get_precedence(op_token.value.upper()) + 1)
            left = BinaryOp(left, op_token.value.upper(), right, [op_token])
        return left

    def _parse_unary_expression(self):
        token = self.current_token
        if token.type == 'OPERATOR' and token.value in ['+', '-', '~']: # Bitwise NOT (~) eklendi
            op_token = self.eat('OPERATOR', token.value)
            right = self._parse_unary_expression()
            return UnaryOp(op_token.value, right, [op_token])
        elif token.type == 'LOGICAL_KEYWORD_OPERATOR' and token.value.upper() == 'NOT':
            op_token = self.eat('LOGICAL_KEYWORD_OPERATOR', 'NOT')
            right = self._parse_unary_expression()
            return UnaryOp(op_token.value.upper(), right, [op_token])
        else:
            return self._parse_primary_expression()

    def _parse_primary_expression(self):
        token = self.current_token
        if token.type == 'NUMBER':
            self.advance()
            return Number(token.value, [token])
        elif token.type == 'STRING':
            self.advance()
            return String(token.value, [token])
        elif token.type == 'IDENTIFIER':
            if self.peek() and self.peek().type == 'PUNCTUATION' and self.peek().value == '(':
                # Fonksiyon çağrısı
                return self.parse_function_call(is_call_command=False)
            elif self.peek() and self.peek().type == 'PUNCTUATION' and self.peek().value == '[': # Array indexleme
                ident_token = self.eat('IDENTIFIER')
                self.eat('PUNCTUATION', '[')
                index_expr = self.parse_expression()
                self.eat('PUNCTUATION', ']')
                # Dizi elemanı erişimi için özel bir AST düğümü kullanılabilir (örneğin ArrayAccess)
                # Şimdilik String olarak döndürelim, transpiler daha sonra ayrıştırır.
                return Identifier(f"{ident_token.value}[{self._expr_to_str(index_expr)}]", [ident_token])
            else:
                self.advance()
                return Identifier(token.value, [token])
        elif token.type == 'PUNCTUATION' and token.value == '(':
            self.eat('PUNCTUATION', '(')
            expr = self.parse_expression()
            self.eat('PUNCTUATION', ')')
            return expr
        elif token.type == 'LOGICAL_KEYWORD_OPERATOR' and token.value.upper() in ['TRUE', 'FALSE']:
            self.advance()
            return Identifier(token.value.upper(), [token])
        elif token.type == 'KEYWORD' and token.value.upper() in ['TRUE', 'FALSE', 'HIGH', 'LOW']:
            self.advance()
            return Identifier(token.value.upper(), [token])
        elif token.type == 'KEYWORD' and token.value.upper() in PDSX_TYPE_MAP: # Tip adları (şimdilik sadece identifier gibi)
            self.advance()
            return Identifier(token.value.upper(), [token])
        elif token.type == 'KEYWORD' and token.value.upper() in MATH_FUNCTIONS_CPP: # Matematiksel fonksiyon çağrıları
            func_name = self.eat('KEYWORD', token.value.upper())
            self.eat('PUNCTUATION', '(')
            args = []
            if not (self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ')'):
                args.append(self.parse_expression())
                while self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ',':
                    self.eat('PUNCTUATION', ',')
                    args.append(self.parse_expression())
            self.eat('PUNCTUATION', ')')
            return FunctionCall(func_name.value.upper(), args, [func_name])
        else:
            raise SyntaxError(f"Birincil ifade için beklenmeyen token: {token} (Satır:{token.line}, Sütun:{token.column})")

    def _get_precedence(self, op):
        # Operatör öncelikleri (C++'a yakın, bitwise ve mantıksal operatörler dahil)
        op = op.upper()
        if op in ['OR', 'XOR', 'EQV', 'IMP']: return 1 # Mantıksal OR, XOR, Eşdeğer, İmplikasyon
        if op in ['AND', 'NAND', 'NOR']: return 2    # Mantıksal AND, NAND, NOR
        if op in ['==', '!=', '<', '>', '<=', '>=']: return 3 # Karşılaştırma
        if op in ['<<', '>>']: return 4              # Bitwise Shift
        if op in ['&']: return 5                     # Bitwise AND
        if op in ['^']: return 6                     # Bitwise XOR
        if op in ['|']: return 7                     # Bitwise OR
        if op in ['+', '-']: return 8                # Toplama/Çıkarma
        if op in ['*', '/', '%']: return 9           # Çarpma/Bölme/Mod alma
        if op in ['~', 'NOT']: return 10             # Unary Bitwise NOT, Mantıksal NOT
        return 0

    def parse_function_call(self, is_call_command=False):
        start_token = self.current_token

        if is_call_command:
            self.eat('KEYWORD', 'CALL')
            func_name_token = self.eat('IDENTIFIER')
        else:
            func_name_token = self.eat('IDENTIFIER')

        self.eat('PUNCTUATION', '(')
        args = []
        if not (self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ')'):
            args.append(self.parse_expression())
            while self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ',':
                self.eat('PUNCTUATION', ',')
                args.append(self.parse_expression())
        self.eat('PUNCTUATION', ')')

        if is_call_command and self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'INTO':
            self.eat('KEYWORD', 'INTO')
            target_id = self.eat('IDENTIFIER')
            return Assignment(Identifier(target_id.value), FunctionCall(func_name_token.value, args, [func_name_token]), [start_token, target_id])
        
        return FunctionCall(func_name_token.value, args, [start_token])

    def parse_block(self, end_keywords):
        body = []
        while self.current_token and not (self.current_token.type == 'KEYWORD' and \
                                          (self.current_token.value.upper() in end_keywords or \
                                           (self.current_token.value.upper() == 'END' and self.peek() and self.peek().value.upper() in end_keywords))):
            # Yorumları atla
            if self.current_token.type.startswith('COMMENT'):
                self.advance()
                continue
            body.append(self.parse_statement())
        return body


    def parse_function_definition(self):
        start_token = self.eat('KEYWORD', 'FUNC')
        name_token = self.eat('IDENTIFIER')
        self.eat('PUNCTUATION', '(')
        params = []
        if not (self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ')'):
            param_name = self.eat('IDENTIFIER')
            self.eat('KEYWORD', 'AS')
            param_type_token = self.eat('IDENTIFIER')
            param_type_node = Identifier(param_type_token.value.upper()) # Varsayılan Identifier
            if param_type_token.value.upper() == 'ARRAY':
                if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'OF':
                    self.eat('KEYWORD', 'OF')
                    base_type_token = self.eat('IDENTIFIER')
                    param_type_node = ArrayType(Identifier(base_type_token.value.upper()))
                else:
                    logging.warning(f"Fonksiyon parametresi ARRAY için 'OF' ve eleman tipi bekleniyordu. Varsayılan INTEGER. (Satır:{param_type_token.line}, Sütun:{param_type_token.column})")
                    param_type_node = ArrayType(Identifier("INTEGER"))
            params.append((param_name.value, param_type_node))

            while self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ',':
                self.eat('PUNCTUATION', ',')
                param_name = self.eat('IDENTIFIER')
                self.eat('KEYWORD', 'AS')
                param_type_token = self.eat('IDENTIFIER')
                param_type_node = Identifier(param_type_token.value.upper())
                if param_type_token.value.upper() == 'ARRAY':
                    if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'OF':
                        self.eat('KEYWORD', 'OF')
                        base_type_token = self.eat('IDENTIFIER')
                        param_type_node = ArrayType(Identifier(base_type_token.value.upper()))
                    else:
                        logging.warning(f"Fonksiyon parametresi ARRAY için 'OF' ve eleman tipi bekleniyordu. Varsayılan INTEGER. (Satır:{param_type_token.line}, Sütun:{param_type_token.column})")
                        param_type_node = ArrayType(Identifier("INTEGER"))
                params.append((param_name.value, param_type_node))
        self.eat('PUNCTUATION', ')')

        return_type_node = Identifier("VOID") # Varsayılan
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'AS':
            self.eat('KEYWORD', 'AS')
            return_type_token = self.eat('IDENTIFIER')
            return_type_node = Identifier(return_type_token.value.upper())

        body = self.parse_block(['END', 'FUNC'])
        self.eat('KEYWORD', 'END')
        self.eat('KEYWORD', 'FUNC')
        return FunctionDefinition(name_token.value, params, body, return_type_node, [start_token])

    def parse_event_definition(self):
        start_token = self.eat('KEYWORD', 'EVENT')
        name_token = self.eat('IDENTIFIER')
        self.eat('PUNCTUATION', '(')
        params = []
        if not (self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ')'):
            param_name = self.eat('IDENTIFIER')
            self.eat('KEYWORD', 'AS')
            param_type_token = self.eat('IDENTIFIER')
            param_type_node = Identifier(param_type_token.value.upper())
            params.append((param_name.value, param_type_node))
            while self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ',':
                self.eat('PUNCTUATION', ',')
                param_name = self.eat('IDENTIFIER')
                self.eat('KEYWORD', 'AS')
                param_type_token = self.eat('IDENTIFIER')
                param_type_node = Identifier(param_type_token.value.upper())
                params.append((param_name.value, param_type_node))
        self.eat('PUNCTUATION', ')')

        body = self.parse_block(['END', 'EVENT'])
        self.eat('KEYWORD', 'END')
        self.eat('KEYWORD', 'EVENT')
        return EventDefinition(name_token.value, params, body, [start_token])

    def parse_sub_definition(self):
        start_token = self.eat('KEYWORD', 'SUB')
        name_token = self.eat('IDENTIFIER')
        self.eat('PUNCTUATION', '(')
        params = []
        if not (self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ')'):
            param_name = self.eat('IDENTIFIER')
            self.eat('KEYWORD', 'AS')
            param_type_token = self.eat('IDENTIFIER')
            param_type_node = Identifier(param_type_token.value.upper())
            params.append((param_name.value, param_type_node))
            while self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ',':
                self.eat('PUNCTUATION', ',')
                param_name = self.eat('IDENTIFIER')
                self.eat('KEYWORD', 'AS')
                param_type_token = self.eat('IDENTIFIER')
                param_type_node = Identifier(param_type_token.value.upper())
                params.append((param_name.value, param_type_node))
        self.eat('PUNCTUATION', ')')

        body = self.parse_block(['END', 'SUB'])
        self.eat('KEYWORD', 'END')
        self.eat('KEYWORD', 'SUB')
        return SubDefinition(name_token.value, params, body, [start_token])

    def parse_struct_definition(self):
        start_token = self.eat('KEYWORD', 'TYPE')
        name_token = self.eat('IDENTIFIER')
        fields = []
        while not (self.current_token and self.current_token.type == 'KEYWORD' and \
                   self.current_token.value.upper() == 'END' and self.peek() and self.peek().value.upper() == 'TYPE'):
            field_name = self.eat('IDENTIFIER')
            self.eat('KEYWORD', 'AS')
            field_type_token = self.eat('IDENTIFIER')
            field_type_node = Identifier(field_type_token.value.upper())
            fields.append((field_name.value, field_type_node))
        self.eat('KEYWORD', 'END')
        self.eat('KEYWORD', 'TYPE')
        return StructDefinition(name_token.value, fields, [start_token])

    def parse_class_definition(self):
        start_token = self.eat('KEYWORD', 'CLASS')
        name_token = self.eat('IDENTIFIER')
        parent_name = None
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'INHERITS':
            self.eat('KEYWORD', 'INHERITS')
            parent_name = self.eat('IDENTIFIER').value

        fields = []
        methods = []
        while not (self.current_token and self.current_token.type == 'KEYWORD' and \
                   self.current_token.value.upper() == 'END' and self.peek() and self.peek().value.upper() == 'CLASS'):
            access_specifier = "PUBLIC"
            if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() in ['PUBLIC', 'PRIVATE']:
                access_specifier = self.eat('KEYWORD', self.current_token.value.upper()).value.upper()

            if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'SUB':
                sub_start_token = self.eat('KEYWORD', 'SUB')
                method_name = self.eat('IDENTIFIER')
                self.eat('PUNCTUATION', '(')
                params = []
                if not (self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ')'):
                    param_name = self.eat('IDENTIFIER')
                    self.eat('KEYWORD', 'AS')
                    param_type_token = self.eat('IDENTIFIER')
                    param_type_node = Identifier(param_type_token.value.upper())
                    params.append((param_name.value, param_type_node))
                    while self.current_token and self.current_token.type == 'PUNCTUATION' and self.current_token.value == ',':
                        self.eat('PUNCTUATION', ',')
                        param_name = self.eat('IDENTIFIER')
                        self.eat('KEYWORD', 'AS')
                        param_type_token = self.eat('IDENTIFIER')
                        param_type_node = Identifier(param_type_token.value.upper())
                        params.append((param_name.value, param_type_node))
                self.eat('PUNCTUATION', ')')
                method_body = self.parse_block(['END', 'SUB'])
                self.eat('KEYWORD', 'END')
                self.eat('KEYWORD', 'SUB')
                methods.append(FunctionDefinition(method_name.value, params, method_body, Identifier("VOID"), [sub_start_token]))
            else: # Sınıf alanı
                field_name = self.eat('IDENTIFIER')
                self.eat('KEYWORD', 'AS')
                field_type_token = self.eat('IDENTIFIER')
                field_type_node = Identifier(field_type_token.value.upper())
                fields.append((field_name.value, field_type_node, access_specifier))
        self.eat('KEYWORD', 'END')
        self.eat('KEYWORD', 'CLASS')
        return ClassDefinition(name_token.value, parent_name, fields, methods, [start_token])

    def parse_alias_definition(self):
        start_token = self.eat('KEYWORD', 'ALIAS')
        new_name_token = self.eat('IDENTIFIER')
        self.eat('KEYWORD', 'AS')
        old_name_token = self.eat('IDENTIFIER')
        return AliasDefinition(new_name_token.value, old_name_token.value, [start_token])

    def parse_if_statement(self):
        start_token = self.eat('KEYWORD', 'IF')
        condition = self.parse_expression()
        self.eat('KEYWORD', 'THEN')
        then_body = self.parse_block(['ELSE', 'END', 'IF'])
        else_body = None

        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'ELSE':
            self.eat('KEYWORD', 'ELSE')
            else_body = self.parse_block(['END', 'IF'])

        self.eat('KEYWORD', 'END')
        self.eat('KEYWORD', 'IF')
        return IfStatement(condition, then_body, else_body, [start_token])

    def parse_for_statement(self):
        start_token = self.eat('KEYWORD', 'FOR')
        var_name = self.eat('IDENTIFIER').value
        self.eat('ASSIGNMENT_OPERATOR', '=')
        start_expr = self.parse_expression()
        self.eat('KEYWORD', 'TO')
        end_expr = self.parse_expression()
        step_expr = None
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'STEP':
            self.eat('KEYWORD', 'STEP')
            step_expr = self.parse_expression()

        body = self.parse_block(['NEXT'])
        self.eat('KEYWORD', 'NEXT')
        if self.current_token and self.current_token.type == 'IDENTIFIER': # NEXT ile gelen değişken adı
            self.advance()
        return ForStatement(var_name, start_expr, end_expr, step_expr, body, [start_token])

    def parse_loop_statement(self):
        start_token = self.eat('KEYWORD', 'DO')
        loop_type_prefix_is_while_until = False
        condition = None

        # Check for DO WHILE / DO UNTIL
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() in ['WHILE', 'UNTIL']:
            loop_type_prefix_is_while_until = True
            loop_type = self.eat('KEYWORD', self.current_token.value.upper()).value.upper() # WHILE/UNTIL
            condition = self.parse_expression()
            actual_loop_type = "DO_" + loop_type
            body = self.parse_block(['LOOP'])
            self.eat('KEYWORD', 'LOOP')
            return LoopStatement(body, actual_loop_type, condition, [start_token])

        # If not DO WHILE/UNTIL, then it's a simple DO...LOOP or DO...LOOP WHILE/UNTIL
        body = self.parse_block(['LOOP', 'EXIT', 'DO']) # EXIT DO'yu da işle
        
        # Check for EXIT DO
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() == 'EXIT':
            self.eat('KEYWORD', 'EXIT')
            self.eat('KEYWORD', 'DO')
            # EXIT DO için özel bir düğüm veya doğrudan döngüyü kesme mantığı gerekebilir.
            # Şimdilik, body'ye bir boş ifade ekleyelim veya özel bir ExitDoStatement düğümü kullanalım.
            # Transpiler/Interpreter tarafında bu ele alınmalı.
            body.append(HardwareCommand("EXIT_DO", [], [])) # Geçici bir çözüm

        self.eat('KEYWORD', 'LOOP')

        # Check for LOOP WHILE / LOOP UNTIL suffix
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() in ['WHILE', 'UNTIL']:
            loop_type_suffix = self.eat('KEYWORD', self.current_token.value.upper()).value.upper()
            condition = self.parse_expression()
            actual_loop_type = "DO_LOOP_" + loop_type_suffix # e.g. DO_LOOP_WHILE
            return LoopStatement(body, actual_loop_type, condition, [start_token])

        return LoopStatement(body, "DO_LOOP", None, [start_token]) # Simple DO...LOOP

    def parse_select_case_statement(self):
        start_token = self.eat('KEYWORD', 'SELECT')
        self.eat('KEYWORD', 'CASE')
        expr = self.parse_expression()
        cases = []

        while not (self.current_token and self.current_token.type == 'KEYWORD' and \
                   self.current_token.value.upper() == 'END' and self.peek() and self.peek().value.upper() == 'SELECT'):
            self.eat('KEYWORD', 'CASE')
            case_value = self.parse_expression()
            case_body = self.parse_block(['CASE', 'END', 'SELECT'])
            cases.append((case_value, case_body))
        
        self.eat('KEYWORD', 'END')
        self.eat('KEYWORD', 'SELECT')
        return SelectCaseStatement(expr, cases, [start_token])