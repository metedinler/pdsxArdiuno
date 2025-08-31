# pdsx_interpreter.py
import time
import math
import logging
import re
import collections # for deque (Queue simulation)

# Loglama yapılandırması
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# AST Düğümlerini içe aktarın (pdsx_parser.py dosyasından)
from pdsx_parser import (
    Node, Program, Statement, Expression, Identifier, Number, String, BinaryOp, UnaryOp, FunctionCall,
    VariableDeclaration, Assignment, HardwareCommand, IfStatement, LoopStatement, ForStatement,
    SelectCaseStatement, ReturnStatement, FunctionDefinition, EventDefinition, SubDefinition,
    StructDefinition, ClassDefinition, AliasDefinition, DataStatement, ReadStatement, RestoreStatement,
    PushPopEnqueueDequeue, TryCatchStatement, ThrowStatement, DelayStatement,
    ArrayType, StackType, QueueType
)

# PDSX veri tipleri için Python karşılıkları (sadece referans amaçlı, doğrudan kullanılmaz)
# Interpreter, tipleri dinamik olarak yönetecek.
PDSX_TYPE_MAP_PYTHON = {
    "INTEGER": int,
    "DOUBLE": float,
    "STRING": str,
    "BYTE": int,    # uint8_t
    "SHORT": int,   # int16_t
    "LONG": int,    # int32_t
    "SINGLE": float,
    "BOOLEAN": bool,
    "POINTER": None # Python'da doğrudan bir karşılığı yok
}

# Python'daki matematiksel ve mantıksal fonksiyonlar
MATH_FUNCTIONS_PYTHON = {
    "ABS": abs,
    "SIN": math.sin,
    "COS": math.cos,
    "TAN": math.tan,
    "POW": math.pow,
    "SQRT": math.sqrt,
    "NROOT": lambda val, n: math.pow(val, 1.0/n),
    "ROUND": round,
    # İstatistiksel fonksiyonlar için Python karşılıkları:
    "MEAN": lambda vals: sum(vals) / len(vals) if vals else 0,
    "MEDIAN": lambda vals: sorted(vals)[len(vals)//2] if vals else 0 if len(vals) % 2 else (sorted(vals)[len(vals)//2 - 1] + sorted(vals)[len(vals)//2]) / 2.0 if vals else 0,
    "STDDEV": lambda vals: math.sqrt(sum((x - sum(vals)/len(vals))**2 for x in vals) / (len(vals) - 1)) if len(vals) > 1 else 0,
    "VARIANCE": lambda vals: sum((x - sum(vals)/len(vals))**2 for x in vals) / (len(vals) - 1) if len(vals) > 1 else 0,
}

# Mantıksal operatörler için Python karşılıkları
LOGICAL_OPERATORS_PYTHON = {
    "AND": lambda a, b: a and b,
    "OR": lambda a, b: a or b,
    "NOT": lambda a: not a,
    "NAND": lambda a, b: not (a and b),
    "NOR": lambda a, b: not (a or b),
    "XOR": lambda a, b: a != b, # Boolean XOR
    "EQV": lambda a, b: a == b, # Boolean Eşdeğerlik
    "IMP": lambda a, b: (not a) or b, # Boolean İmplikasyon
}


class PDSXInterpreter:
    def __init__(self, ast):
        self.ast = ast
        self.symbol_table = {}  # Global değişkenler ve fonksiyonlar için
        self.functions = {}     # Fonksiyon tanımları {isim: FunctionDefinition_node}
        self.subs = {}          # Sub tanımları {isim: SubDefinition_node}
        self.events = {}        # Event tanımları {isim: EventDefinition_node}
        self.aliases = {}       # Alias'lar {yeni_isim: eski_isim}
        self.data_store = []    # DATA komutları için depolama
        self.data_pointer = 0   # READ komutları için işaretçi
        self.call_stack = []    # Fonksiyon çağrı yığını (şimdilik basit)
        
        # Donanım simülasyonu için durum bilgisi
        self.hardware_state = {
            "pins": {},         # {pin_num: value (HIGH/LOW or analog_val)}
            "servo_positions": {}, # {servo_name: position}
            "buzzer_state": {"pin": None, "on": False, "frequency": 0},
            "serial_output": [],# Simüle edilmiş seri monitör çıktısı
            "timers": {},       # {timer_id: {"interval": int, "count": int, "event_name": str, "last_trigger_time": float}}
            "interrupts": {}    # {pin: {"mode": str, "event_name": str}}
        }
        self.current_time = 0.0 # Simüle edilmiş zaman (saniye cinsinden)

        # Sembol tablolarını önceden doldur (fonksiyonlar, alt programlar, eventler)
        self._prime_symbol_table()
        
    def _prime_symbol_table(self):
        for stmt in self.ast.statements:
            if isinstance(stmt, FunctionDefinition):
                self.functions[stmt.name.upper()] = stmt
            elif isinstance(stmt, SubDefinition):
                self.subs[stmt.name.upper()] = stmt
            elif isinstance(stmt, EventDefinition):
                self.events[stmt.name.upper()] = stmt
            elif isinstance(stmt, VariableDeclaration):
                # Global değişkenleri varsayılan değerleriyle başlat
                # Interpreter dinamik tip olduğu için tip kontrolü yapmıyoruz, sadece başlatıyoruz
                if hasattr(stmt, 'initial_value') and stmt.initial_value is not None:
                    # Initial value varsa onu kullan
                    value = self._evaluate_expression(stmt.initial_value)
                    self.symbol_table[stmt.name.upper()] = value
                else:
                    # Varsayılan değer kullan
                    default_value = self._get_default_value_for_type(stmt.var_type)
                    self.symbol_table[stmt.name.upper()] = default_value
            elif isinstance(stmt, AliasDefinition):
                self.aliases[stmt.new_name.upper()] = stmt.old_name.upper()
            elif isinstance(stmt, DataStatement):
                for val_node in stmt.values:
                    # DATA değerlerini string olarak depola, READ ederken dönüştür
                    self.data_store.append(self._evaluate_expression(val_node))

    def _get_default_value_for_type(self, type_node):
        if isinstance(type_node, Identifier):
            pdsx_type = type_node.name.upper()
            if pdsx_type in ["INTEGER", "BYTE", "SHORT", "LONG"]: return 0
            if pdsx_type in ["DOUBLE", "SINGLE"]: return 0.0
            if pdsx_type == "STRING": return ""
            if pdsx_type == "BOOLEAN": return False
            # Diğer özel tipler için varsayılan boş değerler
            return None # Bilinmeyen veya işaretçi tipleri
        elif isinstance(type_node, ArrayType):
            # Interpreter'da diziler için liste - boyut varsa o kadar eleman ayır
            if type_node.size:
                size = self._evaluate_expression(type_node.size)
                return [self._get_default_value_for_type(type_node.base_type) for _ in range(int(size))]
            else:
                return [] # Boyut yoksa boş liste
        elif isinstance(type_node, StackType):
            # Interpreter'da yığın için liste - boyut simülasyonda kullanılmaz ama bilgi olarak saklanır
            return []
        elif isinstance(type_node, QueueType):
            # Interpreter'da kuyruk için collections.deque - boyut simülasyonda kullanılmaz ama bilgi olarak saklanır
            return collections.deque()
        return None

    def _resolve_symbol(self, name_node):
        # Alias varsa çöz
        resolved_name = self.aliases.get(name_node.name.upper(), name_node.name.upper())
        
        # Özel sabitler (TRUE, FALSE, HIGH, LOW)
        if resolved_name == 'TRUE': return True
        if resolved_name == 'FALSE': return False
        if resolved_name == 'HIGH': return 1 # Simülasyonda sayısal değer
        if resolved_name == 'LOW': return 0  # Simülasyonda sayısal değer

        # Sembol tablosundan ara
        if resolved_name in self.symbol_table:
            return self.symbol_table[resolved_name]
        
        logging.warning(f"Tanımlanmamış sembol '{name_node.name}' (Satır:{name_node.tokens[0].line}, Sütun:{name_node.tokens[0].column})")
        return None # Tanımlanmamış sembol

    def _set_symbol_value(self, name_node, value):
        resolved_name = self.aliases.get(name_node.name.upper(), name_node.name.upper())
        self.symbol_table[resolved_name] = value

    def _evaluate_expression(self, expr_node):
        if isinstance(expr_node, Number):
            return expr_node.value
        elif isinstance(expr_node, String):
            return expr_node.value
        elif isinstance(expr_node, Identifier):
            # Eğer bir array elemanı veya sınıf üyesi erişimiyse
            if '[' in expr_node.name and ']' in expr_node.name: # Basit array erişimi tespiti
                match = re.match(r"(\w+)\[(.+)\]", expr_node.name)
                if match:
                    array_name = match.group(1).upper()
                    index_expr_str = match.group(2)
                    # Index ifadesini ayrı bir parser/evaluator ile değerlendirmek gerekir.
                    # Şimdilik, sadece sayısal index kabul edelim veya eval kullanalım (güvenlik riski!)
                    # Daha iyi bir çözüm için, parser ArrayAccess düğümü oluşturmalıydı.
                    try:
                        # Basit bir eval ile index hesaplama
                        index = int(eval(index_expr_str, {}, self.symbol_table)) # Dikkat: eval güvenlik açığı olabilir!
                        arr = self._resolve_symbol(Identifier(array_name))
                        if isinstance(arr, list) and 0 <= index < len(arr):
                            return arr[index]
                        logging.error(f"Dizi dışı erişim veya dizi bulunamadı: {array_name}[{index}]")
                        return None
                    except Exception as e:
                        logging.error(f"Dizi indexi değerlendirilirken hata: {index_expr_str} - {e}")
                        return None
                
            elif '.' in expr_node.name: # Basit üye erişimi tespiti (MyObject.Field)
                parts = expr_node.name.split('.')
                obj_name = parts[0].upper()
                field_name = parts[1]
                obj = self._resolve_symbol(Identifier(obj_name))
                if isinstance(obj, dict) and field_name in obj: # Obje bir sözlükle simüle edilmişse
                    return obj[field_name]
                logging.error(f"Üye erişim hatası: {obj_name}.{field_name} bulunamadı.")
                return None

            return self._resolve_symbol(expr_node)
        
        elif isinstance(expr_node, BinaryOp):
            left_val = self._evaluate_expression(expr_node.left)
            right_val = self._evaluate_expression(expr_node.right)
            op = expr_node.op.upper()

            if op in LOGICAL_OPERATORS_PYTHON:
                return LOGICAL_OPERATORS_PYTHON[op](left_val, right_val)
            
            # Aritmetik ve Bitwise Operatörler
            if op == '+': 
                # String concatenation için type coercion
                if isinstance(left_val, str) or isinstance(right_val, str):
                    return str(left_val) + str(right_val)
                return left_val + right_val
            if op == '-': return left_val - right_val
            if op == '*': return left_val * right_val
            if op == '/': 
                if right_val == 0:
                    logging.error("Sıfıra bölme hatası!")
                    return None
                return left_val / right_val
            if op == '%': return left_val % right_val
            if op == '==': return left_val == right_val
            if op == '!=': return left_val != right_val
            if op == '<': return left_val < right_val
            if op == '>': return left_val > right_val
            if op == '<=': return left_val <= right_val
            if op == '>=': return left_val >= right_val
            
            # Bitwise Operatörler
            if op == '&': return int(left_val) & int(right_val)
            if op == '|': return int(left_val) | int(right_val)
            if op == '^': return int(left_val) ^ int(right_val)
            if op == '<<': return int(left_val) << int(right_val)
            if op == '>>': return int(left_val) >> int(right_val)
            
            logging.error(f"Bilinmeyen ikili operatör: '{op}' (repr: {repr(op)})")
            return None
        
        elif isinstance(expr_node, UnaryOp):
            val = self._evaluate_expression(expr_node.right)
            op = expr_node.op.upper()
            if op == '-': return -val
            if op == '+': return +val # Etkisiz
            if op == 'NOT': return not val
            if op == '~': return ~int(val) # Bitwise NOT
            # ++ ve -- burada ifade olarak işlenmemeliydi, statement olarak ele alınır.
            logging.error(f"Bilinmeyen tekli operatör: {op}")
            return None

        elif isinstance(expr_node, FunctionCall):
            func_name_upper = expr_node.func_name.upper()
            args = [self._evaluate_expression(arg) for arg in expr_node.args]

            if func_name_upper in MATH_FUNCTIONS_PYTHON:
                if func_name_upper in ["SIN", "COS", "TAN"]:
                    # Dereceyi radyana çevir
                    args[0] = math.radians(args[0])
                return MATH_FUNCTIONS_PYTHON[func_name_upper](*args)
            elif func_name_upper in self.functions:
                return self._execute_function(self.functions[func_name_upper], args)
            elif func_name_upper in self.subs:
                self._execute_sub(self.subs[func_name_upper], args)
                return None # SUB'lar değer döndürmez
            elif func_name_upper in self.events:
                self._execute_event(self.events[func_name_upper], args)
                return None # Event'lar değer döndürmez
            else:
                logging.error(f"Fonksiyon/Sub/Event '{expr_node.func_name}' tanımlanmamış.")
                return None
        else:
            logging.error(f"Bilinmeyen ifade düğümü: {type(expr_node).__name__}")
            return None

    def _execute_function(self, func_node, args_values):
        # Fonksiyon çağrısı için global scope'u koruyarak parametreleri ekle
        if len(func_node.params) != len(args_values):
            logging.error(f"Fonksiyon '{func_node.name}' için argüman sayısı uyuşmuyor. Beklenen: {len(func_node.params)}, Alınan: {len(args_values)}")
            raise ValueError("Argüman sayısı uyuşmazlığı")
        
        # Mevcut sembol tablosunu yığına it (backup)
        self.call_stack.append(dict(self.symbol_table))  # Deep copy yaparak mevcut scope'u koru
        
        # Parametreleri mevcut sembol tablosuna ekle (global scope üzerine)
        for (param_name, param_type_node), arg_val in zip(func_node.params, args_values):
            self.symbol_table[param_name.upper()] = arg_val

        return_value = None
        try:
            for stmt in func_node.body:
                # Return ifadesiyle fonksiyonu bitir
                if isinstance(stmt, ReturnStatement):
                    return_value = self._evaluate_expression(stmt.value) if stmt.value else None
                    break # Fonksiyondan çık
                self.visit(stmt) # Diğer deyimleri yürüt
        finally:
            # Fonksiyondan çıkarken sembol tablosunu geri yükle
            if self.call_stack:
                self.symbol_table = self.call_stack.pop()
            else:
                # Bu durumda global kapsamdayız, ancak bir hata durumu olabilir.
                logging.warning("Çağrı yığını boş ama fonksiyon bitiyor. Potansiyel hata.")
        
        return return_value

    def _execute_sub(self, sub_node, args_values):
        # Alt program çağrısı için global scope'u koruyarak parametreleri ekle
        if len(sub_node.params) != len(args_values):
            logging.error(f"Alt program '{sub_node.name}' için argüman sayısı uyuşmuyor. Beklenen: {len(sub_node.params)}, Alınan: {len(args_values)}")
            raise ValueError("Argüman sayısı uyuşmazlığı")
        
        # Mevcut sembol tablosunu yığına it (backup)
        self.call_stack.append(dict(self.symbol_table))  # Deep copy yaparak mevcut scope'u koru
        
        # Parametreleri mevcut sembol tablosuna ekle (global scope üzerine)
        for (param_name, param_type_node), arg_val in zip(sub_node.params, args_values):
            self.symbol_table[param_name.upper()] = arg_val

        try:
            for stmt in sub_node.body:
                if isinstance(stmt, ReturnStatement): # SUB'larda RETURN sadece alt programı sonlandırır
                    break
                self.visit(stmt)
        finally:
            if self.call_stack:
                self.symbol_table = self.call_stack.pop()
            else:
                logging.warning("Çağrı yığını boş ama alt program bitiyor.")

    def _execute_event(self, event_node, args_values):
        # Event'lar için de benzer bir mekanizma
        # Genellikle ISR'ler gibi parametre almazlar veya çok sınırlı parametre alırlar
        if len(event_node.params) != len(args_values):
            logging.warning(f"Event '{event_node.name}' için argüman sayısı uyuşmuyor. Yoksayılıyor. Beklenen: {len(event_node.params)}, Alınan: {len(args_values)}")
        
        # Mevcut sembol tablosunu yığına it (backup)
        self.call_stack.append(dict(self.symbol_table))  # Deep copy yaparak mevcut scope'u koru
        
        # Parametreleri mevcut sembol tablosuna ekle (global scope üzerine)
        for (param_name, param_type_node), arg_val in zip(event_node.params, args_values):
            self.symbol_table[param_name.upper()] = arg_val

        try:
            for stmt in event_node.body:
                self.visit(stmt)
        finally:
            if self.call_stack:
                self.symbol_table = self.call_stack.pop()
            else:
                logging.warning("Çağrı yığını boş ama event bitiyor.")


    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        logging.warning(f"Interpreter: Ziyaretçi metodu '{type(node).__name__}' uygulanmadı. Düğüm atlanıyor.")
        # Genellikle bu bir hata durumu, çünkü her AST düğümü işlenmeli.
        return None

    def run(self):
        # Programın ana akışını yürüt
        # Global değişken başlatmaları _prime_symbol_table içinde yapıldı
        # Ana loop'a girmeden önce setup benzeri komutları işle
        
        # Simüle edilmiş setup() kısmı
        logging.info("Interpreter: Simüle edilmiş setup() başlıyor...")
        setup_statements = []
        loop_statements = []
        
        for stmt in self.ast.statements:
            # Setup'ta çalışacak statement'lar
            if isinstance(stmt, (VariableDeclaration, Assignment, HardwareCommand, 
                                ForStatement, IfStatement, LoopStatement, SelectCaseStatement)):
                # Hardware komutları, değişken atamaları, döngüler ve kontrol yapıları setup'ta çalışsın
                setup_statements.append(stmt)
            elif not any(isinstance(stmt, T) for T in [FunctionDefinition, EventDefinition, SubDefinition,
                                                       StructDefinition, ClassDefinition, AliasDefinition,
                                                       DataStatement]):
                # Fonksiyon tanımları dışında kalan diğer statement'lar loop'ta
                loop_statements.append(stmt)
        
        # Setup statement'larını çalıştır
        for stmt in setup_statements:
            self.visit(stmt)

        logging.info("Interpreter: Simüle edilmiş setup() bitti.")

        # Eğer loop statement'ları varsa sonsuz döngüde çalıştır
        if loop_statements:
            logging.info("Interpreter: Simüle edilmiş loop() başlıyor (Ctrl+C ile durdurun)...")
        else:
            logging.info("Interpreter: Loop'ta çalışacak statement yok, program tamamlandı.")
            return
        
        try:
            
            while True: # Sonsuz döngü, kullanıcı Ctrl+C ile durdurana kadar
                # Zamanlayıcıları kontrol et (simüle edilmiş zaman)
                for timer_id, timer_info in list(self.hardware_state["timers"].items()): # Kopyalama, döngü sırasında değişiklik olmaması için
                    if self.current_time - timer_info["last_trigger_time"] >= timer_info["interval"] / 1000.0: # ms -> saniye
                        if timer_info["count"] == -1 or timer_info["count"] > 0:
                            logging.info(f"Interpreter: Zamanlayıcı {timer_id} etkinleşti, Event/Function '{timer_info['event_name']}' çağrılıyor.")
                            event_name_upper = timer_info["event_name"].upper()
                            if event_name_upper in self.events:
                                self._execute_event(self.events[event_name_upper], []) # Event'lar şimdilik parametresiz
                            elif event_name_upper in self.functions:
                                self._execute_function(self.functions[event_name_upper], []) # Function'lar da parametresiz çağrılabilir
                            elif event_name_upper in self.subs:
                                self._execute_sub(self.subs[event_name_upper], []) # Sub'lar da parametresiz çağrılabilir
                            else:
                                logging.warning(f"Interpreter: Timer için belirtilen Event/Function/Sub '{timer_info['event_name']}' bulunamadı.")
                            
                            timer_info["last_trigger_time"] = self.current_time
                            if timer_info["count"] != -1:
                                timer_info["count"] -= 1
                                if timer_info["count"] == 0:
                                    logging.info(f"Interpreter: Zamanlayıcı {timer_id} sayımı bitti.")
                                    del self.hardware_state["timers"][timer_id] # Sayım bitince zamanlayıcıyı kaldır

                # Ana döngüdeki komutları yürüt
                for stmt in loop_statements:
                    self.visit(stmt)
                
                # Döngü sonunda simüle edilmiş zamanı ilerlet
                # Burada ne kadar ilerleyeceğimizi belirlemek önemli. Çok hızlı olmasın.
                # Gerçek Arduino loop'u çok hızlı çalışır. Simülasyon için küçük bir gecikme ekleyebiliriz.
                time.sleep(0.01) # 10 ms simülasyon adımı
                self.current_time += 0.01

        except KeyboardInterrupt:
            logging.info("Interpreter: Kullanıcı tarafından durduruldu (Ctrl+C).")
        except Exception as e:
            logging.error(f"Interpreter Çalışma Zamanı Hatası: {e}", exc_info=True)


    # --- Ziyaretçi Metotları (visit_...) ---

    def visit_VariableDeclaration(self, node):
        # Interpreter modunda global değişkenler _prime_symbol_table'da başlatılıyor.
        # Fonksiyon içi değişkenler _execute_function içinde ele alınır.
        # Bu metod, eğer bir deklarasyon bir ifade olarak çağrılırsa diye burada var.
        
        # Initial value varsa atamasını yap
        if hasattr(node, 'initial_value') and node.initial_value is not None:
            value = self._evaluate_expression(node.initial_value)
            # Eğer local_scope varsa ona, yoksa global symbol_table'a ata
            # Şu anki basit yapıda global_vars sadece _prime_symbol_table'da ele alınıyor.
            # Fonksiyon içindeki DIM'ler için local_scope'a atama yapılmalı.
            # Bu interpreter'da kapsam yönetimi daha iyi modellenmeli.
            if self.call_stack and self.symbol_table is not self.call_stack[-1]: # Eğer bir local scope'daysak
                self.symbol_table[node.name.upper()] = value
            else: # Global scope'tayız
                self.symbol_table[node.name.upper()] = value
        else:
            # Varsayılan değerle başlat
            default_value = self._get_default_value_for_type(node.var_type)
            if self.call_stack and self.symbol_table is not self.call_stack[-1]:
                self.symbol_table[node.name.upper()] = default_value
            else:
                self.symbol_table[node.name.upper()] = default_value
        return None # Return None as it's a statement

    def visit_Assignment(self, node):
        target = node.target
        value = self._evaluate_expression(node.value)

        # Eğer hedef bir dizi elemanı ise
        if isinstance(target, Identifier) and '[' in target.name and ']' in target.name:
            match = re.match(r"(\w+)\[(.+)\]", target.name)
            if match:
                array_name = match.group(1).upper()
                index_expr_str = match.group(2)
                try:
                    index = int(eval(index_expr_str, {}, self.symbol_table)) # Eval burada da kullanılıyor
                    arr = self._resolve_symbol(Identifier(array_name))
                    if isinstance(arr, list):
                        if 0 <= index < len(arr):
                            arr[index] = value
                        else:
                            # Python'da dizi boyutu dinamik, Basic/PDSX'te ise sabit olmalı.
                            # Simülasyonda dinamik büyütmeye izin verebiliriz veya hata verebiliriz.
                            # Şimdilik büyütmeye izin verelim.
                            while len(arr) <= index:
                                arr.append(self._get_default_value_for_type(Identifier("INTEGER"))) # Varsayılan tip, daha sonra geliştirilebilir
                            arr[index] = value
                    else:
                        logging.error(f"'{array_name}' bir dizi değil.")
                except Exception as e:
                    logging.error(f"Dizi indexi atamada hata: {index_expr_str} - {e}")
                return None
        
        # Eğer hedef bir sınıf/struct üyesi ise
        if isinstance(target, Identifier) and '.' in target.name:
            parts = target.name.split('.')
            obj_name = parts[0].upper()
            field_name = parts[1]
            obj = self._resolve_symbol(Identifier(obj_name))
            if isinstance(obj, dict):
                obj[field_name] = value
            else:
                logging.error(f"'{obj_name}' bir nesne değil.")
            return None

        # Normal değişken ataması
        self._set_symbol_value(target, value)
        return None

    def visit_UnaryOp(self, node):
        # ++ ve -- operatörleri için (önceki değer okunur, artırılır/azaltılır, geri yazılır)
        if node.op == '++':
            current_val = self._evaluate_expression(node.right)
            if isinstance(current_val, (int, float)):
                self._set_symbol_value(node.right, current_val + 1)
            else:
                logging.error(f"'{node.right.name}' tipi artırılamaz.")
            return None
        elif node.op == '--':
            current_val = self._evaluate_expression(node.right)
            if isinstance(current_val, (int, float)):
                self._set_symbol_value(node.right, current_val - 1)
            else:
                logging.error(f"'{node.right.name}' tipi azaltılamaz.")
            return None
        # Diğer tekli operatörler ifadelerin parçasıdır ve _evaluate_expression içinde ele alınır.
        logging.warning(f"Interpreter: Tekli operatör '{node.op}' beklenmeyen bir statement olarak bulundu.")
        return None

    def visit_FunctionCall(self, node):
        # Bu metod, FunctionCall'ın bir statement olarak kullanıldığı durumlarda çağrılır.
        # Fonksiyon çağrısı bir değer döndürebilir ama bu değer kullanılmaz.
        self._evaluate_expression(node)
        return None

    def visit_HardwareCommand(self, node):
        cmd_type = node.cmd_type
        args = [self._evaluate_expression(arg) if isinstance(arg, Node) else arg for arg in node.args]

        if cmd_type == "HARDWARE_MAP":
            logging.info(f"Simülasyon: Donanım haritası {args[0]} olarak ayarlandı (sadece bilgi amaçlı).")
        elif cmd_type == "DEFINE_SERVO":
            servo_name = args[0]
            pin = args[1]
            self.hardware_state["servo_positions"][servo_name] = 90 # Varsayılan orta konum
            logging.info(f"Simülasyon: Servo '{servo_name}' ({pin} pininde) tanımlandı.")
        elif cmd_type == "DEFINE_BUZZER":
            pin = args[0]
            self.hardware_state["buzzer_state"]["pin"] = pin
            logging.info(f"Simülasyon: Buzzer ({pin} pininde) tanımlandı.")
        elif cmd_type == "CONFIGURE_PIN":
            pin = args[0]
            mode = args[1]
            self.hardware_state["pins"][pin] = {"mode": mode, "value": 0} # Başlangıçta LOW
            logging.info(f"Simülasyon: Pin {pin} {mode} olarak yapılandırıldı.")
        elif cmd_type == "CONFIGURE_INTERRUPT":
            pin = args[0]
            mode = args[1]
            event_name = args[2]
            self.hardware_state["interrupts"][pin] = {"mode": mode, "event_name": event_name}
            logging.info(f"Simülasyon: Pin {pin} üzerinde {mode} modunda kesme {event_name} ile yapılandırıldı.")
        elif cmd_type == "CONFIGURE_TIMER":
            timer_id = args[0]
            interval_ms = args[1]
            count = args[2]
            event_name = args[3]
            self.hardware_state["timers"][timer_id] = {
                "interval": interval_ms,
                "count": count,
                "event_name": event_name,
                "last_trigger_time": self.current_time # Simüle edilmiş başlangıç zamanı
            }
            logging.info(f"Simülasyon: Zamanlayıcı {timer_id} ayarlandı (Aralık: {interval_ms}ms, Sayım: {count}, Event: {event_name}).")
        elif cmd_type == "SERIAL_BEGIN":
            baud = args[0]
            logging.info(f"Simülasyon: Seri haberleşme {baud} baud ile başlatıldı.")
        elif cmd_type == "READ_PIN":
            pin = args[0]
            target_var_name = args[1] # Bu bir string olarak geliyor
            # Simüle edilmiş bir değer okuyalım (örn: dijital pin için rastgele 0 veya 1)
            simulated_value = self.hardware_state["pins"].get(pin, {}).get("value", 0) # Eğer önceden ayarlı bir değeri varsa onu oku
            logging.info(f"Simülasyon: Pin {pin}'den '{simulated_value}' okundu, '{target_var_name}' değişkenine atandı.")
            self._set_symbol_value(Identifier(target_var_name), simulated_value)
        elif cmd_type == "BUZZER_CONTROL":
            action = args[0]
            freq = args[1]
            pin = self.hardware_state["buzzer_state"]["pin"]
            if pin is None:
                logging.warning("Simülasyon: Buzzer pini tanımlanmamış, kontrol edilemiyor.")
                return
            self.hardware_state["buzzer_state"]["on"] = (action == "ON")
            self.hardware_state["buzzer_state"]["frequency"] = freq
            logging.info(f"Simülasyon: Buzzer ({pin} pininde) {action} frekans: {freq}Hz.")
        elif cmd_type == "MOVE_SERVO":
            servo_name = args[0]
            pos = args[1]
            if servo_name not in self.hardware_state["servo_positions"]:
                logging.warning(f"Simülasyon: Servo '{servo_name}' tanımlanmamış, hareket ettirilemiyor.")
                return
            self.hardware_state["servo_positions"][servo_name] = pos
            logging.info(f"Simülasyon: Servo '{servo_name}' {pos} derecesine hareket ettirildi.")
        elif cmd_type == "WIFI_CONNECT":
            ssid = args[0]
            password = args[1]
            logging.info(f"Simülasyon: WiFi ağına bağlanılıyor '{ssid}' şifre ile: '{password}'. (Gerçek bağlantı yok)")
        elif cmd_type == "CONFIGURE_ADC":
            pin = args[0]
            res = args[1]
            logging.info(f"Simülasyon: ADC pin {pin} çözünürlük {res} olarak yapılandırıldı.")
        elif cmd_type == "CONFIGURE_PWM":
            pin = args[0]
            freq = args[1]
            duty = args[2]
            logging.info(f"Simülasyon: PWM pin {pin} frekans {freq}Hz, görev döngüsü %{duty/255*100:.2f} olarak yapılandırıldı.") # 0-255 duty varsayımı
        elif cmd_type == "DIGITALWRITE":
            pin = args[0]
            value = args[1]
            self.hardware_state["pins"][pin] = {"mode": self.hardware_state["pins"].get(pin, {}).get("mode", "OUTPUT"), "value": value}
            logging.info(f"Simülasyon: Pin {pin} değeri {value} olarak ayarlandı (HIGH=1, LOW=0).")
        elif cmd_type == "LOG_INFO":
            message = args[0]
            print(f"PDSX Log: {message}")
            self.hardware_state["serial_output"].append(str(message))
        elif cmd_type == "GOTO":
            label = args[0]
            logging.warning(f"Simülasyon: GOTO '{label}' komutu çalıştırıldı. (Döngü dışı atlamalar karmaşık olabilir)")
            # GOTO için gerçek bir atlama yapmak, interpreter'ın yapısını çok değiştirir.
            # Şimdilik sadece logluyoruz.
        elif cmd_type == "EXIT_DO":
            # Bu, LoopStatement'ın döngü yürütme mantığında bir istisna fırlatmalı
            raise StopIteration("EXIT DO komutuyla döngüden çıkılıyor.") # Döngüyü kırmak için özel istisna

        return None

    def visit_IfStatement(self, node):
        condition_result = self._evaluate_expression(node.condition)
        if condition_result:
            for stmt in node.then_body:
                self.visit(stmt)
        elif node.else_body:
            for stmt in node.else_body:
                self.visit(stmt)
        return None

    def visit_LoopStatement(self, node):
        if node.loop_type == "DO_LOOP":
            while True:
                try:
                    for stmt in node.body:
                        self.visit(stmt)
                except StopIteration as e: # EXIT DO yakalama
                    if str(e) == "EXIT DO komutuyla döngüden çıkılıyor.":
                        break # Döngüyü kır
                    raise e # Başka StopIteration ise tekrar fırlat
        elif node.loop_type == "DO_WHILE":
            while self._evaluate_expression(node.condition):
                try:
                    for stmt in node.body:
                        self.visit(stmt)
                except StopIteration as e:
                    if str(e) == "EXIT DO komutuyla döngüden çıkılıyor.": break
                    raise e
        elif node.loop_type == "DO_UNTIL":
            while not self._evaluate_expression(node.condition):
                try:
                    for stmt in node.body:
                        self.visit(stmt)
                except StopIteration as e:
                    if str(e) == "EXIT DO komutuyla döngüden çıkılıyor.": break
                    raise e
        elif node.loop_type == "DO_LOOP_WHILE":
            while True: # do-while'ın ilk çalışması garanti
                try:
                    for stmt in node.body:
                        self.visit(stmt)
                except StopIteration as e:
                    if str(e) == "EXIT DO komutuyla döngüden çıkılıyor.": break
                    raise e
                if not self._evaluate_expression(node.condition):
                    break
        elif node.loop_type == "DO_LOOP_UNTIL":
            while True: # do-until'ın ilk çalışması garanti
                try:
                    for stmt in node.body:
                        self.visit(stmt)
                except StopIteration as e:
                    if str(e) == "EXIT DO komutuyla döngüden çıkılıyor.": break
                    raise e
                if self._evaluate_expression(node.condition): # UNTIL olduğu için true olduğunda çık
                    break
        return None

    def visit_ForStatement(self, node):
        var_name = node.var_name.upper()
        start_val = int(self._evaluate_expression(node.start_expr))
        end_val = int(self._evaluate_expression(node.end_expr))
        step_val = int(self._evaluate_expression(node.step_expr)) if node.step_expr else 1

        # FOR döngüsü için özel bir local scope oluştur
        old_val = self.symbol_table.get(var_name, None) # Eğer varsa eski değerini sakla
        self.call_stack.append(self.symbol_table.copy()) # Mevcut symbol_table'ı kopyalayıp yığına koy
        self.symbol_table[var_name] = start_val # Yeni loop değişkeni için değer ata

        try:
            current_var_value = start_val
            while (step_val > 0 and current_var_value <= end_val) or \
                  (step_val < 0 and current_var_value >= end_val):
                
                self.symbol_table[var_name] = current_var_value # Güncel değeri ata
                for stmt in node.body:
                    try:
                        self.visit(stmt)
                    except StopIteration as e: # EXIT FOR gibi bir durum olursa
                        if str(e) == "EXIT DO komutuyla döngüden çıkılıyor.": # PDSX'te sadece EXIT DO var
                            raise e # Bu bir iç döngüden gelmiş olabilir, tekrar fırlat
                        break # FOR döngüsünü kır
                
                current_var_value += step_val
                
        except StopIteration: # Dış döngüden gelen EXIT DO'yu yakala
            pass # Bu FOR döngüsünü bitirir
        finally:
            # Döngü bitince eski sembol tablosunu geri yükle
            if self.call_stack:
                self.symbol_table = self.call_stack.pop()
                if old_val is not None: # Eğer değişken önceden tanımlıysa değerini geri yükle
                    self.symbol_table[var_name] = old_val
                elif var_name in self.symbol_table: # Eğer yeni bir değişkense temizle
                    del self.symbol_table[var_name]
            else:
                logging.warning("Interpreter: FOR döngüsü biterken çağrı yığını boş.")

        return None

    def visit_SelectCaseStatement(self, node):
        expr_value = self._evaluate_expression(node.expr)
        executed_case = False
        for case_value_node, case_body in node.cases:
            case_val = self._evaluate_expression(case_value_node)
            if expr_value == case_val:
                for stmt in case_body:
                    self.visit(stmt)
                executed_case = True
                break # İlk eşleşen case'i bulduktan sonra çık
        
        # PDSX'te SELECT CASE'in DEFAULT/ELSE mekanizması yok, ilk eşleşeni bulur.
        return None

    def visit_ReturnStatement(self, node):
        # Bu metod çağrı yığını yönetimini basitleştirmek için bir istisna fırlatır.
        return_value = self._evaluate_expression(node.value) if node.value else None
        raise RuntimeError(f"RETURN_VALUE:{return_value}") # Özel bir istisna ile değeri taşı

    def visit_DataStatement(self, node):
        # Data değerleri zaten _prime_symbol_table içinde data_store'a eklenmişti.
        # Bu düğümün çalıştırılmasına gerek yok.
        return None

    def visit_ReadStatement(self, node):
        target_var = node.target.name.upper()
        if self.data_pointer < len(self.data_store):
            value_str = self.data_store[self.data_pointer]
            # Değeri hedef değişkenin tipine uygun şekilde dönüştürmeye çalışalım
            # Basit bir guess yapalım:
            try:
                if isinstance(self.symbol_table.get(target_var), int):
                    value = int(value_str)
                elif isinstance(self.symbol_table.get(target_var), float):
                    value = float(value_str)
                elif isinstance(self.symbol_table.get(target_var), bool):
                    value = value_str.lower() == 'true'
                else: # Varsayılan olarak string
                    value = value_str
            except ValueError:
                logging.warning(f"READ hatası: '{value_str}' değeri '{target_var}' için uygun tipe dönüştürülemiyor. String olarak ele alınacak.")
                value = value_str
            
            self._set_symbol_value(Identifier(target_var), value)
            self.data_pointer += 1
        else:
            logging.error("READ hatası: DATA bloğunda okunacak veri kalmadı.")
            # Hata fırlatılabilir veya program durdurulabilir.
        return None

    def visit_RestoreStatement(self, node):
        self.data_pointer = 0
        logging.info("DATA işaretçisi sıfırlandı.")
        return None
    
    def visit_PushPopEnqueueDequeue(self, node):
        collection_name = node.collection_name.name.upper()
        collection = self._resolve_symbol(Identifier(collection_name))

        if collection is None:
            logging.error(f"Koleksiyon '{collection_name}' bulunamadı veya tanımlanmadı.")
            return None

        if node.action == "PUSH": # Stack (Python listesi ile simüle)
            value = self._evaluate_expression(node.value_or_var)
            if isinstance(collection, list):
                collection.append(value)
            else:
                logging.error(f"'{collection_name}' bir yığın değil.")
        elif node.action == "POP": # Stack
            target_var_name = node.value_or_var.name.upper() # Identifier.name
            if isinstance(collection, list):
                if collection:
                    popped_value = collection.pop()
                    self._set_symbol_value(Identifier(target_var_name), popped_value)
                else:
                    logging.error(f"Yığın '{collection_name}' boş (POP).")
            else:
                logging.error(f"'{collection_name}' bir yığın değil.")
        elif node.action == "ENQUEUE": # Queue (Python deque ile simüle)
            value = self._evaluate_expression(node.value_or_var)
            if isinstance(collection, collections.deque):
                collection.append(value)
            else:
                logging.error(f"'{collection_name}' bir kuyruk değil.")
        elif node.action == "DEQUEUE": # Queue
            target_var_name = node.value_or_var.name.upper() # Identifier.name
            if isinstance(collection, collections.deque):
                if collection:
                    dequeued_value = collection.popleft()
                    self._set_symbol_value(Identifier(target_var_name), dequeued_value)
                else:
                    logging.error(f"Kuyruk '{collection_name}' boş (DEQUEUE).")
            else:
                logging.error(f"'{collection_name}' bir kuyruk değil.")
        return None

    def visit_TryCatchStatement(self, node):
        try:
            for stmt in node.try_body:
                self.visit(stmt)
        except RuntimeError as e: # ThrowStatement'tan gelen istisnaları yakala
            if str(e).startswith("THROW_MESSAGE:"):
                message = str(e)[len("THROW_MESSAGE:"):]
                logging.info(f"Interpreter: Bir istisna yakalandı: {message}")
                # Hata işleme bloğunu çalıştır
                for stmt in node.catch_body:
                    self.visit(stmt)
            else:
                raise e # Diğer çalışma zamanı hatalarını tekrar fırlat
        except Exception as e: # Diğer Python hatalarını da yakala
            logging.error(f"Interpreter: Beklenmeyen bir hata yakalandı: {e}")
            for stmt in node.catch_body:
                self.visit(stmt)
        return None

    def visit_ThrowStatement(self, node):
        message = self._evaluate_expression(node.message)
        raise RuntimeError(f"THROW_MESSAGE:{message}") # Özel bir istisna ile mesajı taşı

    def visit_DelayStatement(self, node):
        duration_ms = self._evaluate_expression(node.duration)
        logging.info(f"Simülasyon: {duration_ms} ms gecikme.")
        time.sleep(duration_ms / 1000.0) # Milisaniyeyi saniyeye çevir
        self.current_time += duration_ms / 1000.0 # Simüle edilmiş zamanı güncelle
        return None

    # Class ve Struct Instance (örnek) oluşturma ve üye erişimi için daha karmaşık ziyaretçiler gerekebilir.
    # Şimdilik, Parser'ın oluşturduğu "myObject.field" gibi string ifadelerini _evaluate_expression içinde işliyoruz.