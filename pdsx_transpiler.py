import logging
import json
import math # math.pi için


# Loglama yapılandırması
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# AST Düğümlerini içe aktarın (pdsx_parser.py dosyasından)
from pdsx_parser import (
    Node, Program, Statement, Expression, Identifier, Number, String, BinaryOp, UnaryOp, FunctionCall,
    VariableDeclaration, Assignment, HardwareCommand, IfStatement, LoopStatement, ForStatement,
    SelectCaseStatement, ReturnStatement, FunctionDefinition, EventDefinition, SubDefinition,
    StructDefinition, ClassDefinition, AliasDefinition, DataStatement, ReadStatement, RestoreStatement,
    PushPopEnqueueDequeue, TryCatchStatement, ThrowStatement, DelayStatement,
    ArrayType, StackType, QueueType # Yeni tip düğümleri
)

# --- Sabitler ve Global Yapılandırma ---
# Donanım Haritasını JSON'dan Yükle
def load_hardware_map(filename="hardware_map.json"):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Donanım haritası dosyası bulunamadı: {filename}. Varsayılan harita yükleniyor.")
        return {
            "ARDUINO_UNO": {
                "pins": {"0": {"digital": True, "analog": False}, "A0": {"digital": True, "analog": True}},
                "pwm": [3, 5, 6, 9, 10, 11], "interrupts": [2, 3],
                "memory": {"ram": 2048, "flash": 32768}, "libraries": ["Arduino.h", "Servo.h"], "timers": [0, 1, 2]
            },
            "ESP32": {
                "pins": {"0": {"digital": True, "analog": True}, "32": {"digital": True, "analog": True}},
                "pwm": [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25],
                "interrupts": [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
                "memory": {"ram": 520192, "flash": 4194304}, "libraries": ["WiFi.h", "HTTPClient.h", "ESP32Servo.h", "Ticker.h", "driver/ledc.h"], "timers": [0, 1, 2, 3]
            },
            "DENEYAP_KART": { # Deneyap Kart genellikle ESP32 tabanlıdır, kütüphaneler farklılaşabilir.
                "pins": {"0": {"digital": True, "analog": False}, "A0": {"digital": True, "analog": True}},
                "pwm": [0, 1, 2, 3, 4, 5], "interrupts": [0, 1, 2, 3],
                "memory": {"ram": 520192, "flash": 4194304}, "libraries": ["Deneyap_Servo.h"], "timers": [0, 1]
            }
        }

hardware_maps = load_hardware_map()

# PDSX Veri Tipleri ve C++ Eşleşmeleri (Daha kapsamlı hale getirildi)
PDSX_TYPE_MAP = {
    "INTEGER": "int",
    "DOUBLE": "double",
    "STRING": "String", # Arduino'da String sınıfı
    "BYTE": "uint8_t",
    "SHORT": "int16_t",
    "LONG": "int32_t",
    "SINGLE": "float",
    "BOOLEAN": "bool",
    "POINTER": "void*",
    # 'ARRAY', 'STACK', 'QUEUE' artık özel AST düğümleri tarafından işlenecek.
}

# C++'a özel matematiksel ve mantıksal fonksiyon eşleşmeleri
MATH_FUNCTIONS_CPP = {
    "ABS": "abs",
    "SIN": "sin",
    "COS": "cos",
    "TAN": "tan",
    "POW": "pow",
    "SQRT": "sqrt",
    "NROOT": "pow", # NROOT(val, n) -> pow(val, 1.0/n)
    "ROUND": "round",
    "MEAN": "mean",
    "MEDIAN": "median",
    "STDDEV": "stddev",
    "VARIANCE": "variance"
}

# Mantıksal operatörler için C++ eşleşmeleri
LOGICAL_OPERATORS_CPP = {
    "AND": "&&",
    "OR": "||",
    "NOT": "!",
    "NAND": "!((__LEFT__) && (__RIGHT__))", # NAND(A,B) = !(A && B)
    "NOR": "!((__LEFT__) || (__RIGHT__))",  # NOR(A,B) = !(A || B)
    "XOR": "((__LEFT__) != (__RIGHT__))",   # XOR(A,B) = (A != B)
    "EQV": "((__LEFT__) == (__RIGHT__))",   # EQV(A,B) = (A == B)
    "IMP": "(!(__LEFT__) || (__RIGHT__))",  # IMP(A,B) = (!A || B)
}


class CppTranspiler:
    def __init__(self, ast, platform="ARDUINO_UNO"):
        self.ast = ast
        self.platform = platform
        self.cpp_code = []
        self.includes = set([
            "#include <Arduino.h>",
            "#include <string>",
            "#include <vector>",  # std::vector için
            "#include <stack>",   # std::stack için
            "#include <queue>",   # std::queue için
            "#include <numeric>", # std::accumulate için (mean, stddev, variance)
            "#include <cmath>",   # abs, sin, cos, tan, pow, sqrt, round, M_PI için
            "#include <algorithm>" # std::sort için (median)
        ])
        self.global_vars = {} # {name: VariableDeclaration node}
        self.functions = {}   # {name: FunctionDefinition node}
        self.events = {}      # {name: EventDefinition node}
        self.subs = {}        # {name: SubDefinition node}
        self.classes = {}     # {name: ClassDefinition node}
        self.structs = {}     # {name: StructDefinition node}
        self.aliases = {}     # {new_name: old_name} -> #define için
        
        # Donanım ayarları için takip
        self.hardware_config = {
            "servos": {},
            "buzzers": {},
            "pins": {}, # pin: {mode: INPUT/OUTPUT, is_configured: bool}
            "timers": {},
            "interrupts": {},
            "serial_baud": None,
            "pwm_channels": {} # ESP32 için PWM kanalları
        }
        self.current_scope_vars = {} # {name: type_node} for local scope (şimdilik kullanılmıyor)
        self.indent_level = 0
        self.setup_statements = []
        self.loop_statements = []
        self.data_values = []
        self.data_pointer_var = "__pdsx_data_ptr"
        self.platform_info = hardware_maps.get(platform, {})
        self.has_delay = False # delay.h için (Arduino.h zaten delay içerir)

        # Platforma özgü kütüphaneler ekle
        for lib in self.platform_info.get("libraries", []):
            if lib not in ["Arduino.h", "string", "vector", "stack", "queue", "numeric", "cmath", "algorithm"]: # Zaten eklediklerimizi tekrar eklemeyelim
                self.includes.add(f"#include <{lib}>")
        
        # ESP32 için özel include'lar
        if self.platform == "ESP32":
            self.includes.add("#include <WiFi.h>")
            self.includes.add("#include <Ticker.h>")
            self.includes.add("#include <soc/ledc_reg.h>")
            self.includes.add("#include <driver/ledc.h>")
            
        # Arduino için Servo.h, eğer bir servo tanımlanmışsa eklenecek.
        # Bu, DEFINE SERVO komutunda ele alınacak.

        # setup() ve loop() için varsayılan olarak Serial.begin ekle
        self.setup_statements.append("Serial.begin(9600);")


    def indent(self):
        return "  " * self.indent_level

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        logging.warning(f"Ziyaretçi metodu '{type(node).__name__}' uygulanmadı. Düğüm atlanıyor.")
        return f"// UYARI: İşlenmeyen AST düğümü: {type(node).__name__}"

    def transpile(self):
        # İlk geçiş: Tanımlamaları topla (global kapsamda)
        for stmt in self.ast.statements:
            if isinstance(stmt, FunctionDefinition):
                self.functions[stmt.name] = stmt
            elif isinstance(stmt, EventDefinition):
                self.events[stmt.name] = stmt
            elif isinstance(stmt, SubDefinition):
                self.subs[stmt.name] = stmt
            elif isinstance(stmt, StructDefinition):
                self.structs[stmt.name] = stmt
            elif isinstance(stmt, ClassDefinition):
                self.classes[stmt.name] = stmt
            elif isinstance(stmt, AliasDefinition):
                self.aliases[stmt.new_name.upper()] = stmt.old_name.upper()
            elif isinstance(stmt, VariableDeclaration):
                self.global_vars[stmt.name] = stmt # Store node for full info
            elif isinstance(stmt, DataStatement):
                # DATA statement'ları global bir diziye çevir
                # Burada sadece değeri topla, tipi _transpile_expression belirleyecek
                self.data_values.extend([self._transpile_expression(val_node) for val_node in stmt.values])
            elif isinstance(stmt, HardwareCommand) and stmt.cmd_type == "HARDWARE_MAP":
                self.platform = stmt.args[0]
                self.platform_info = hardware_maps.get(self.platform, {})
                for lib in self.platform_info.get("libraries", []):
                    if lib not in ["Arduino.h", "string", "vector", "stack", "queue", "numeric", "cmath", "algorithm"]:
                        self.includes.add(f"#include <{lib}>")
        
        # --- C++ çıktısının başlangıcı: Includes ve Global Tanımlar ---
        for include in sorted(list(self.includes)):
            self.cpp_code.append(include)

        self.cpp_code.append("\n// PDSX Matematiksel ve İstatistiksel Yardımcı Fonksiyonlar")
        self.cpp_code.append(self._get_special_functions_cpp())
        self.cpp_code.append(f"#define M_PI {math.pi}") # M_PI tanımla (cmath'te olabilir ama garanti olsun)
        self.cpp_code.append("#ifndef DEG_TO_RAD")
        self.cpp_code.append("#define DEG_TO_RAD(degrees) ((degrees) * (M_PI / 180.0))")
        self.cpp_code.append("#endif\n")

        # Global değişken tanımlamaları
        for var_name, var_node in self.global_vars.items():
            self.cpp_code.append(self.visit_VariableDeclaration(var_node))
        
        # Alias tanımlamaları
        for new_name, old_name in self.aliases.items():
            # Alias'lar C++ makroları olarak tanımlanır, büyük/küçük harf duyarlılığına dikkat edilmeli
            # Ancak PDSX genellikle büyük/küçük harf duyarsızdır, bu yüzden ALIAS LED AS ledPin -> #define LED ledPin
            self.cpp_code.append(f"#define {new_name} {old_name}")

        # Data komutundan gelen verileri C++ dizisine çevir
        if self.data_values:
            # Data tipi belirlemek için basit bir guess yapalım: Eğer hepsi sayıysa int, değilse String
            is_all_numbers = True
            for val in self.data_values:
                # Basit bir kontrol, gerçek değerleri de kontrol etmek gerekebilir
                if not (val.replace('.', '', 1).isdigit() or (val.startswith('-') and val[1:].replace('.', '', 1).isdigit())):
                    is_all_numbers = False
                    break
            
            # String değerler çift tırnak içinde olduğu için tırnakları kontrol etmek gerek.
            # Şu anki _transpile_expression Stringleri zaten tırnaklı veriyor.
            # Dolayısıyla, buradaki ifadenin tipi String ise tırnaklarla birlikte gelecek.
            # Ancak C++ dizisinde farklı tipleri tutmak karmaşıktır.
            # Şimdilik, sadece sayısal veriler için int dizi oluşturalım, diğerleri hata versin.
            
            # Daha robust bir çözüm için, data array'i union veya void* tutmalı
            # Ya da PDSX DATA komutunda tip belirtilmeli.
            # Şimdilik, DATA sadece sayıları tutsun ve int diziye çevrilsin.
            
            # Eğer karmaşık tipler varsa, `std::vector<String>` veya `std::vector<int/double>` olabilir
            # Basitlik adına, sadece int veya String dizisi olarak değerlendirelim.
            data_type = "int"
            if any('"' in val for val in self.data_values): # Eğer herhangi bir eleman string ise
                data_type = "String"
                self.includes.add("#include <vector>") # String vector için
            
            # `const int` yerine `const auto` kullanmak, tip çıkarımı yapmasını sağlar.
            # Ancak Arduino'da `auto` her zaman desteklenmeyebilir.
            self.cpp_code.append(f"const {data_type} __pdsx_data[] = {{ {', '.join(self.data_values)} }};")
            self.cpp_code.append(f"int {self.data_pointer_var} = 0;")
            self.cpp_code.append(f"const int __pdsx_data_size = sizeof(__pdsx_data) / sizeof(__pdsx_data[0]);")


        # Struct tanımlamaları
        for struct_name, struct_node in self.structs.items():
            self.cpp_code.append(f"\nstruct {struct_name} {{")
            self.indent_level += 1
            for field_name, field_type_node in struct_node.fields:
                cpp_field_type = self._transpile_type_node(field_type_node)
                self.cpp_code.append(f"{self.indent()}{cpp_field_type} {field_name};")
            self.indent_level -= 1
            self.cpp_code.append(f"}};")

        # Class tanımlamaları ve metod prototipleri (sadece sınıfın kendisi)
        for class_name, class_node in self.classes.items():
            parent_str = f" : public {class_node.parent}" if class_node.parent else ""
            self.cpp_code.append(f"\nclass {class_name}{parent_str} {{")
            self.indent_level += 1
            
            current_access = "public" # C++'ta varsayılan sınıf üye erişimi 'private'tır. PDSX'te 'public' varsayalım.
            # Alanlar
            for field_name, field_type_node, access in class_node.fields:
                if access.lower() != current_access:
                    self.cpp_code.append(f"{self.indent()}{access.lower()}:")
                    current_access = access.lower()
                cpp_field_type = self._transpile_type_node(field_type_node)
                self.cpp_code.append(f"{self.indent()}{cpp_field_type} {field_name};")
            
            # Metot prototipleri
            for method_node in class_node.methods:
                params_str = ", ".join([f"{self._transpile_type_node(t_node)} {n}" for n, t_node in method_node.params])
                return_type = self._transpile_type_node(method_node.return_type)
                if current_access != "public": # Metotlar için default public
                    self.cpp_code.append(f"{self.indent()}public:")
                    current_access = "public"
                self.cpp_code.append(f"{self.indent()}{return_type} {method_node.name}({params_str});")
            self.indent_level -= 1
            self.cpp_code.append(f"}};")

        # Fonksiyon, olay ve sub prototipleri (implementasyonlardan önce)
        for func_name, func_node in self.functions.items():
            params_str = ", ".join([f"{self._transpile_type_node(t_node)} {n}" for n, t_node in func_node.params])
            return_type = self._transpile_type_node(func_node.return_type)
            self.cpp_code.append(f"{return_type} {func_name}({params_str});")
        for event_name, event_node in self.events.items():
            params_str = ", ".join([f"{self._transpile_type_node(t_node)} {n}" for n, t_node in event_node.params])
            self.cpp_code.append(f"void {event_name}({params_str});")
        for sub_name, sub_node in self.subs.items():
            params_str = ", ".join([f"{self._transpile_type_node(t_node)} {n}" for n, t_node in sub_node.params])
            self.cpp_code.append(f"void {sub_name}({params_str});")
        

        # --- setup() fonksiyonu içeriğini topla ---
        # Bu kısım, global statement'ları ve setup'a ait özel donanım komutlarını işler.
        # FunctionDefinition, EventDefinition, SubDefinition, ClassDefinition, StructDefinition, AliasDefinition, DataStatement dışındaki her şey.
        main_flow_statements = []
        for stmt in self.ast.statements:
            if not any(isinstance(stmt, T) for T in [FunctionDefinition, EventDefinition, SubDefinition, StructDefinition, ClassDefinition, AliasDefinition, DataStatement, VariableDeclaration]):
                # Zamanlayıcılar gibi loop içinde yer alması gereken komutları burada ayırt etmeliyiz.
                # Ya da her visit metodunun nerede çağrılacağını açıkça belirtmeliyiz.
                # Şimdilik, CONFIGURE TIMER haricindeki HardwareCommand'lar setup'a gidecek.
                if isinstance(stmt, HardwareCommand) and stmt.cmd_type == "CONFIGURE_TIMER":
                    # Bu doğrudan visit edilmeli ve loop_statements'a eklenmeli
                    self.loop_statements.append(self.visit(stmt))
                else:
                    main_flow_statements.append(stmt)
            # Global değişkenlerin ilk atamaları (eğer varsa) setup'a gitsin
            elif isinstance(stmt, VariableDeclaration) and hasattr(stmt, 'initial_value') and stmt.initial_value:
                var_name = stmt.name
                initial_value_str = self._transpile_expression(stmt.initial_value)
                self.setup_statements.append(f"{var_name} = {initial_value_str};")
        
        # main_flow_statements içindekileri loop_statements'a ekle
        for stmt in main_flow_statements:
            self.loop_statements.append(self.visit(stmt))


        # --- C++ setup() fonksiyonunu yaz ---
        self.cpp_code.append("\nvoid setup() {")
        self.indent_level += 1
        for line in self.setup_statements:
            if line: # Boş satırları atla
                self.cpp_code.append(self.indent() + line)
        self.indent_level -= 1
        self.cpp_code.append("}")

        # --- C++ loop() fonksiyonunu yaz ---
        self.cpp_code.append("\nvoid loop() {")
        self.indent_level += 1
        for line in self.loop_statements:
            if line: # Boş satırları atla
                self.cpp_code.append(self.indent() + line)
        self.indent_level -= 1
        self.cpp_code.append("}")

        # --- Fonksiyon, olay ve sub implementasyonları ---
        for func_name, func_node in self.functions.items():
            params_str = ", ".join([f"{self._transpile_type_node(t_node)} {n}" for n, t_node in func_node.params])
            return_type = self._transpile_type_node(func_node.return_type)
            self.cpp_code.append(f"\n{return_type} {func_name}({params_str}) {{")
            self.indent_level += 1
            for stmt in func_node.body:
                transpiled_stmt = self.visit(stmt)
                if transpiled_stmt:
                    self.cpp_code.append(self.indent() + transpiled_stmt)
            self.indent_level -= 1
            self.cpp_code.append("}")

        for event_name, event_node in self.events.items():
            params_str = ", ".join([f"{self._transpile_type_node(t_node)} {n}" for n, t_node in event_node.params])
            self.cpp_code.append(f"\nvoid {event_name}({params_str}) {{") # Event'lar C++'ta ISR olursa parametre almaz. Bu durum yönetilmeli.
            self.indent_level += 1
            for stmt in event_node.body:
                transpiled_stmt = self.visit(stmt)
                if transpiled_stmt:
                    self.cpp_code.append(self.indent() + transpiled_stmt)
            self.indent_level -= 1
            self.cpp_code.append("}")

        for sub_name, sub_node in self.subs.items():
            params_str = ", ".join([f"{self._transpile_type_node(t_node)} {n}" for n, t_node in sub_node.params])
            self.cpp_code.append(f"\nvoid {sub_name}({params_str}) {{")
            self.indent_level += 1
            for stmt in sub_node.body:
                transpiled_stmt = self.visit(stmt)
                if transpiled_stmt:
                    self.cpp_code.append(self.indent() + transpiled_stmt)
            self.indent_level -= 1
            self.cpp_code.append("}")

        # Class metod implementasyonları
        for class_name, class_node in self.classes.items():
            for method_node in class_node.methods:
                params_str = ", ".join([f"{self._transpile_type_node(t_node)} {n}" for n, t_node in method_node.params])
                return_type = self._transpile_type_node(method_node.return_type)
                self.cpp_code.append(f"\n{return_type} {class_name}::{method_node.name}({params_str}) {{")
                self.indent_level += 1
                for stmt in method_node.body:
                    transpiled_stmt = self.visit(stmt)
                    if transpiled_stmt:
                        self.cpp_code.append(self.indent() + transpiled_stmt)
                self.indent_level -= 1
                self.cpp_code.append(f"}}")

        return "\n".join(self.cpp_code)

    def _get_special_functions_cpp(self):
        # Ortak yardımcı fonksiyonlar
        cpp_helpers = """
// PDSX Matematiksel ve İstatistiksel Fonksiyonlar
double mean(const std::vector<double>& vals) {
    if (vals.empty()) return 0;
    return std::accumulate(vals.begin(), vals.end(), 0.0) / vals.size();
}
double median(std::vector<double> vals) { // Kopyalama, orijinali değiştirmemek için
    if (vals.empty()) return 0;
    std::sort(vals.begin(), vals.end());
    size_t n = vals.size();
    return n % 2 ? vals[n / 2] : (vals[n / 2 - 1] + vals[n / 2]) / 2.0;
}
double stddev(const std::vector<double>& vals) {
    if (vals.size() < 2) return 0;
    double m = mean(vals);
    double sum_sq = 0;
    for (double v : vals) sum_sq += (v - m) * (v - m);
    return sqrt(sum_sq / (vals.size() - 1));
}
double variance(const std::vector<double>& vals) {
    if (vals.size() < 2) return 0;
    double m = mean(vals);
    double sum_sq = 0;
    for (double v : vals) sum_sq += (v - m) * (v - m);
    return sum_sq / (vals.size() - 1);
}
"""
        return cpp_helpers

    def _transpile_type_node(self, type_node):
        # Tip düğümlerini C++ tiplerine çevir
        if isinstance(type_node, Identifier):
            return PDSX_TYPE_MAP.get(type_node.name.upper(), type_node.name.lower())
        elif isinstance(type_node, ArrayType):
            if hasattr(type_node.base_type, 'name'):
                base_cpp_type = PDSX_TYPE_MAP.get(type_node.base_type.name.upper(), type_node.base_type.name.lower())
            else:
                base_cpp_type = "int"  # Varsayılan
            
            # Boyut varsa sabit array, yoksa vector
            if type_node.size:
                size_str = self._transpile_expression(type_node.size)
                return f"{base_cpp_type}[{size_str}]"  # Sabit array
            else:
                return f"std::vector<{base_cpp_type}>"  # Dinamik vector
        elif isinstance(type_node, StackType):
            if hasattr(type_node.base_type, 'name'):
                base_cpp_type = PDSX_TYPE_MAP.get(type_node.base_type.name.upper(), type_node.base_type.name.lower())
            else:
                base_cpp_type = "int"  # Varsayılan
            return f"std::stack<{base_cpp_type}>"
        elif isinstance(type_node, QueueType):
            if hasattr(type_node.base_type, 'name'):
                base_cpp_type = PDSX_TYPE_MAP.get(type_node.base_type.name.upper(), type_node.base_type.name.lower())
            else:
                base_cpp_type = "int"  # Varsayılan
            return f"std::queue<{base_cpp_type}>"
        return "void*" # Bilinmeyen tip
        
    def _transpile_expression(self, expr_node):
        if isinstance(expr_node, Number):
            return str(expr_node.value)
        elif isinstance(expr_node, String):
            return f'"{expr_node.value}"'
        elif isinstance(expr_node, Identifier):
            # Alias varsa çöz
            resolved_name = self.aliases.get(expr_node.name.upper(), expr_node.name)
            # Özel sabitler (TRUE, FALSE, HIGH, LOW)
            if resolved_name.upper() == 'TRUE': return 'true'
            if resolved_name.upper() == 'FALSE': return 'false'
            if resolved_name.upper() == 'HIGH': return 'HIGH'
            if resolved_name.upper() == 'LOW': return 'LOW'
            return resolved_name # Değişken adı, dizi erişimi vb.
        elif isinstance(expr_node, BinaryOp):
            left = self._transpile_expression(expr_node.left)
            right = self._transpile_expression(expr_node.right)
            op = expr_node.op.upper() # Operatörleri büyük harf olarak al

            if op in LOGICAL_OPERATORS_CPP:
                cpp_op_template = LOGICAL_OPERATORS_CPP[op]
                # __LEFT__ ve __RIGHT__ placeholder'larını değiştir
                return cpp_op_template.replace("__LEFT__", left).replace("__RIGHT__", right)
            
            # Bitwise ve diğer standart operatörler
            return f"({left} {op} {right})"
        
        elif isinstance(expr_node, UnaryOp):
            right = self._transpile_expression(expr_node.right)
            op = expr_node.op.upper()
            if op == "NOT": # Mantıksal NOT
                return f"(!({right}))"
            if op == "~": # Bitwise NOT
                return f"(~{right})"
            # ++ ve -- için burada tekrar işlem yapma, bunlar statement olarak ele alınır
            return f"({op}{right})" 
        
        elif isinstance(expr_node, FunctionCall):
            func_name_upper = expr_node.func_name.upper()
            args_str = ", ".join([self._transpile_expression(arg) for arg in expr_node.args])
            
            if func_name_upper in MATH_FUNCTIONS_CPP:
                cpp_func_name = MATH_FUNCTIONS_CPP[func_name_upper]
                if func_name_upper in ["SIN", "COS", "TAN"]:
                    return f"{cpp_func_name}(DEG_TO_RAD({args_str}))"
                elif func_name_upper == "NROOT": # NROOT(val, n) -> pow(val, 1.0/n)
                    base = self._transpile_expression(expr_node.args[0])
                    exponent = self._transpile_expression(expr_node.args[1])
                    return f"pow({base}, 1.0 / {exponent})"
                return f"{cpp_func_name}({args_str})"
            
            # Özel bir durum: DIGITALWRITE veya CALL gibi komutlar zaten HardwareCommand veya Assignment olarak işlenmeli
            # Eğer buraya gelen bir FunctionCall bir PDSX fonksiyon çağrısıysa:
            return f"{expr_node.func_name}({args_str})"
        else:
            logging.warning(f"Bilinmeyen ifade düğümü tipi dönüştürme için: {type(expr_node).__name__}")
            return f"/* BİLİNMEYEN_İFADE_DÜĞÜMÜ: {type(expr_node).__name__} */"

    # --- Ziyaretçi Metotları ---

    def visit_VariableDeclaration(self, node):
        cpp_type = self._transpile_type_node(node.var_type)
        # Global değişkenler için sadece deklarasyon. İlk atama setup'ta yapılıyor.
        declaration = f"{cpp_type} {node.name};"
        return declaration

    def visit_Assignment(self, node):
        target = self._transpile_expression(node.target)
        value = self._transpile_expression(node.value)
        return f"{target} = {value};"

    def visit_UnaryOp(self, node):
        # ++ ve -- gibi operatörler burada statement olarak işlenir
        if node.op in ['++', '--']:
            target = self._transpile_expression(node.right)
            return f"{target}{node.op};"
        # Diğer tekli operatörler (NOT, ~, +,-) ifadelerin parçasıdır ve _transpile_expression içinde ele alınır.
        return f"// UYARI: Tekli operatör '{node.op}' beklenmeyen bir statement olarak bulundu."

    def visit_FunctionCall(self, node):
        # Bu metod, eğer FunctionCall düğümü bir ifadenin parçası değilse çağrılır (örn: CALL yerine sadece MyFunc()).
        args_str = ", ".join([self._transpile_expression(arg) for arg in node.args])
        # PDSX'in GOSUB veya CALL komutlarını burada ele al
        if node.func_name.upper() in self.functions or node.func_name.upper() in self.subs or node.func_name.upper() in self.events:
            return f"{node.func_name}({args_str});"
        
        logging.warning(f"Tanımsız fonksiyon çağrısı: {node.func_name} (Bu bir komut olmalıydı ya da bir fonksiyona atanmalıydı)")
        return f"// HATA: Tanımsız fonksiyon çağrısı: {node.func_name}({args_str})"

    def visit_HardwareCommand(self, node):
        if node.cmd_type == "HARDWARE_MAP":
            return f"// Donanım haritası {node.args[0]} olarak ayarlandı."
        elif node.cmd_type == "DEFINE_SERVO":
            servo_name = node.args[0]
            pin_num = self._transpile_expression(node.args[1])
            self.hardware_config["servos"][servo_name] = {"pin": pin_num}
            self.includes.add("#include <Servo.h>") # Servo.h'i dahil et
            # Servo objesini global alana ekleyelim, setup'ta attach edilsin
            # Global variables listesine ekleme yapamayız doğrudan burada.
            # En iyi yol, bir "global_declarations" listesi tutmak ve oraya eklemek.
            # Şimdilik, setup'a eklenmesini sağlayarak geçelim.
            # C++'ta: Servo myServo;  -> setup: myServo.attach(pin);
            self.cpp_code.insert(self.cpp_code.index("#include <Servo.h>") + 1 if "#include <Servo.h>" in self.cpp_code else len(self.includes) + 1, f"Servo {servo_name};")
            return f"{servo_name}.attach({pin_num});"
        elif node.cmd_type == "DEFINE_BUZZER":
            pin_num = self._transpile_expression(node.args[0])
            self.hardware_config["buzzers"]["default_pin"] = pin_num # Varsayılan buzzer pini
            return f"// Buzzer pin {pin_num} olarak tanımlandı."
        elif node.cmd_type == "CONFIGURE_PIN":
            pin = self._transpile_expression(node.args[0])
            mode = node.args[1] # INPUT/OUTPUT
            self.hardware_config["pins"][pin] = {"mode": mode, "is_configured": True}
            return f"pinMode({pin}, {mode});"
        elif node.cmd_type == "CONFIGURE_INTERRUPT":
            pin = self._transpile_expression(node.args[0])
            mode = node.args[1] # RISING/FALLING/CHANGE
            event_name = node.args[2]
            trigger_mode_map = {"RISING": "RISING", "FALLING": "FALLING", "CHANGE": "CHANGE"}
            trigger_mode = trigger_mode_map.get(mode, "CHANGE")
            # Arduino için ISR parametre alamaz. Event tanımı da parametresiz olmalı.
            return f"attachInterrupt(digitalPinToInterrupt({pin}), {event_name}, {trigger_mode});"
        elif node.cmd_type == "CONFIGURE_TIMER":
            timer_id = self._transpile_expression(node.args[0])
            interval = self._transpile_expression(node.args[1])
            count = self._transpile_expression(node.args[2])
            event_name = node.args[3]
            
            # Zamanlayıcı değişkenleri global olmalı
            # Bu değişkenlerin global alanda tanımlanmasını sağlamak için bir mekanizma
            self.cpp_code.insert(len(self.includes), f"unsigned long __pdsx_timer_{timer_id}_prev = 0;")
            self.cpp_code.insert(len(self.includes), f"int __pdsx_timer_{timer_id}_count = {count};")


            # Zamanlayıcı mantığı loop() içine eklenir
            timer_logic = [
                f"unsigned long currentMillis = millis();",
                f"if (currentMillis - __pdsx_timer_{timer_id}_prev >= {interval}) {{",
                f"  __pdsx_timer_{timer_id}_prev = currentMillis;",
                f"  if (__pdsx_timer_{timer_id}_count == -1 || __pdsx_timer_{timer_id}_count > 0) {{",
                f"    {event_name}();", # Parametresiz çağrı varsayıyoruz
                f"    if (__pdsx_timer_{timer_id}_count != -1) __pdsx_timer_{timer_id}_count--;",
                f"  }}",
                f"}}"
            ]
            # _transpile metodunda loop_statements'a eklemek için bu bilgiyi saklıyoruz
            # Bu, visit metodunun doğrudan C++ kodu döndürmesi prensibini bozar.
            # Alternatif: TimerLogicStatement gibi yeni bir AST düğümü tanımla.
            # Şimdilik, transpiler ana mantığında bu düğüm özel olarak işlensin.
            return "\n".join(timer_logic) # Bu doğrudan loop_statements'a eklenir.

        elif node.cmd_type == "SERIAL_BEGIN":
            baud = self._transpile_expression(node.args[0])
            self.hardware_config["serial_baud"] = baud
            return f"Serial.begin({baud});"
        elif node.cmd_type == "READ_PIN":
            pin = self._transpile_expression(node.args[0])
            var = node.args[1] # Bu bir Identifier AST düğümü olmalı, şimdilik string olarak geliyor
            return f"{var} = digitalRead({pin});"
        elif node.cmd_type == "BUZZER_CONTROL":
            action = node.args[0] # ON/OFF
            freq_arg = node.args[1]
            buzzer_pin = self.hardware_config["buzzers"].get("default_pin", "BUZZER_PIN_UNDEFINED")
            
            if buzzer_pin == "BUZZER_PIN_UNDEFINED":
                logging.warning("Buzzer pini tanımlanmadı. 'DEFINE BUZZER ON PIN <pin_num>' komutunu kullanın.")
                return f"// HATA: Buzzer pini tanımlanmamış."

            if action == "ON":
                freq = self._transpile_expression(freq_arg) if freq_arg else "0" # Frekans verilmezse 0 (tone kapatma)
                return f"tone({buzzer_pin}, {freq});"
            else: # OFF
                return f"noTone({buzzer_pin});"
        elif node.cmd_type == "MOVE_SERVO":
            servo_name = node.args[0]
            pos = self._transpile_expression(node.args[1])
            if servo_name not in self.hardware_config["servos"]:
                logging.warning(f"Servo '{servo_name}' tanımlanmamış. 'DEFINE SERVO {servo_name} ON PIN <pin_num>' komutunu kullanın.")
                return f"// HATA: Tanımlanmamış servo '{servo_name}'."
            return f"{servo_name}.write({pos});"
        elif node.cmd_type == "WIFI_CONNECT":
            ssid = self._transpile_expression(node.args[0])
            password = self._transpile_expression(node.args[1])
            if self.platform == "ESP32":
                wifi_code = [
                    f"WiFi.begin({ssid}, {password});",
                    f"while (WiFi.status() != WL_CONNECTED) {{",
                    f"  delay(500);",
                    f"  Serial.print(\".\");",
                    f"}}",
                    f"Serial.println(\"WiFi Bağlandı!\");"
                ]
                return "\n".join(wifi_code)
            else:
                return f"// WiFi bağlantısı şu anda {self.platform} üzerinde desteklenmiyor."
        elif node.cmd_type == "CONFIGURE_ADC":
            pin = self._transpile_expression(node.args[0])
            res = self._transpile_expression(node.args[1])
            if self.platform == "ESP32":
                return f"analogReadResolution({res}); // ESP32'de tüm ADC pinleri için geçerlidir."
            elif self.platform == "ARDUINO_UNO":
                return f"// Arduino Uno için analogReadResolution doğrudan desteklenmiyor veya gerekli değil (varsayılan 10-bit)."
            return f"// ADC yapılandırması pin {pin} ve çözünürlük {res} için."
        elif node.cmd_type == "CONFIGURE_PWM":
            pin = self._transpile_expression(node.args[0])
            freq = self._transpile_expression(node.args[1])
            duty = self._transpile_expression(node.args[2])
            if self.platform == "ESP32":
                # ESP32'de LEDC API kullanımı: Kanal, frekans, çözünürlük, pin ata, duty ayarla.
                # Basitlik için bir kanal id'si atayalım ve bit çözünürlüğünü varsayalım.
                # Daha gelişmiş bir sistem, uygun bir LEDC kanalı ve çözünürlük seçecektir.
                ledc_channel = 0 # Örnek kanal
                ledc_timer_bits = 10 # Örnek 10-bit çözünürlük (0-1023 duty cycle)
                # Bu setup içinde çağrılmalı, ancak bir loop statement'ı da olabilir
                # Eğer CONFIGURE PWM bir defalık bir ayarlama ise setup'a, sürekli kontrol ise loop'a.
                # Genelde ayarlamalar setup'a gider, duty cycle değişimi loop'a.
                # Burada sadece ayar kısmını setup'a ekleyelim:
                self.setup_statements.append(f"ledcSetup({ledc_channel}, {freq}, {ledc_timer_bits});")
                self.setup_statements.append(f"ledcAttachPin({pin}, {ledc_channel});")
                self.hardware_config["pwm_channels"][pin] = ledc_channel # Pini hangi kanala atadığımızı takip et
                return f"ledcWrite({ledc_channel}, {duty});" # Bu, bir sonraki `PWM pin, duty` komutlarına benzer olurdu.
            else: # Arduino için analogWrite (frekans kontrolü yok)
                return f"analogWrite({pin}, {duty}); // PWM frekansı {self.platform} üzerinde doğrudan kontrol edilemez, sadece görev döngüsü."
        elif node.cmd_type == "DIGITALWRITE": # DIGITALWRITE komutu
            pin = self._transpile_expression(node.args[0])
            value = self._transpile_expression(node.args[1])
            return f"digitalWrite({pin}, {value});"
        elif node.cmd_type == "GOTO": # GOTO komutu
            label = node.args[0]
            logging.warning(f"GOTO komutu kullanılıyor. C++ kodunda goto kullanımı önerilmez: goto {label};")
            return f"goto {label};"
        elif node.cmd_type == "EXIT_DO": # EXIT DO komutu
            return f"break;" # C++'taki break ile döngüyü kırar
        elif node.cmd_type == "LOG_INFO": # LOG komutları
            message = self._transpile_expression(node.args[0])
            return f"Serial.println({message});"
            
        return f"/* BİLİNMEYEN_DONANIM_KOMUTU: {node.cmd_type} */"

    def visit_IfStatement(self, node):
        condition = self._transpile_expression(node.condition)
        cpp_if = [f"if ({condition}) {{"]
        self.indent_level += 1
        for stmt in node.then_body:
            transpiled_stmt = self.visit(stmt)
            if transpiled_stmt:
                cpp_if.append(self.indent() + transpiled_stmt)
        self.indent_level -= 1
        cpp_if.append("}")
        if node.else_body:
            cpp_if.append("else {")
            self.indent_level += 1
            for stmt in node.else_body:
                transpiled_stmt = self.visit(stmt)
                if transpiled_stmt:
                    cpp_if.append(self.indent() + transpiled_stmt)
            self.indent_level -= 1
            cpp_if.append("}")
        return "\n".join(cpp_if)

    def visit_LoopStatement(self, node):
        body_cpp = []
        self.indent_level += 1
        for stmt in node.body:
            transpiled_stmt = self.visit(stmt)
            if transpiled_stmt:
                body_cpp.append(self.indent() + transpiled_stmt)
        self.indent_level -= 1

        # DO...LOOP: sonsuz döngü (PDSX'te EXIT DO ile kırılır)
        if node.loop_type == "DO_LOOP":
            return f"while (true) {{\n{'\n'.join(body_cpp)}\n{self.indent()}}}"
        # DO WHILE ... LOOP
        elif node.loop_type == "DO_WHILE":
            condition = self._transpile_expression(node.condition)
            return f"while ({condition}) {{\n{'\n'.join(body_cpp)}\n{self.indent()}}}"
        # DO UNTIL ... LOOP
        elif node.loop_type == "DO_UNTIL":
            condition = self._transpile_expression(node.condition)
            return f"while (!({condition})) {{\n{'\n'.join(body_cpp)}\n{self.indent()}}}"
        # DO ... LOOP WHILE
        elif node.loop_type == "DO_LOOP_WHILE":
            condition = self._transpile_expression(node.condition)
            return f"do {{\n{'\n'.join(body_cpp)}\n{self.indent()}}} while ({condition});"
        # DO ... LOOP UNTIL
        elif node.loop_type == "DO_LOOP_UNTIL":
            condition = self._transpile_expression(node.condition)
            return f"do {{\n{'\n'.join(body_cpp)}\n{self.indent()}}} while (!({condition}));"
        return f"// BİLİNMEYEN DÖNGÜ TİPİ: {node.loop_type}"

    def visit_ForStatement(self, node):
        var = node.var_name
        start = self._transpile_expression(node.start_expr)
        end = self._transpile_expression(node.end_expr)
        step = self._transpile_expression(node.step_expr) if node.step_expr else "1"

        # PDSX FOR döngüsü genellikle inclusive (<=) çalışır
        cpp_for = [f"for (int {var} = {start}; {var} <= {end}; {var} += {step}) {{"]
        self.indent_level += 1
        for stmt in node.body:
            transpiled_stmt = self.visit(stmt)
            if transpiled_stmt:
                cpp_for.append(self.indent() + transpiled_stmt)
        self.indent_level -= 1
        cpp_for.append("}")
        return "\n".join(cpp_for)

    def visit_SelectCaseStatement(self, node):
        expr = self._transpile_expression(node.expr)
        cpp_switch = [f"switch ({expr}) {{"]
        self.indent_level += 1
        for case_value_node, case_body in node.cases:
            value = self._transpile_expression(case_value_node)
            cpp_switch.append(f"{self.indent()}case {value}: {{")
            self.indent_level += 1
            for stmt in case_body:
                transpiled_stmt = self.visit(stmt)
                if transpiled_stmt:
                    cpp_switch.append(self.indent() + transpiled_stmt)
            cpp_switch.append(f"{self.indent()}break;")
            self.indent_level -= 1
            cpp_switch.append(f"{self.indent()}}}")
        self.indent_level -= 1
        cpp_switch.append("}")
        return "\n".join(cpp_switch)

    def visit_ReturnStatement(self, node):
        if node.value:
            return f"return {self._transpile_expression(node.value)};"
        return "return;"

    def visit_DataStatement(self, node):
        # Bu zaten global olarak işlendi
        return f"// DATA değerleri (global diziye işlendi)"

    def visit_ReadStatement(self, node):
        target_var = self._transpile_expression(node.target)
        return f"if ({self.data_pointer_var} < __pdsx_data_size) {{ {target_var} = __pdsx_data[{self.data_pointer_var}++]; }} else {{ Serial.println(\"Çalışma Zamanı Hatası: Okunacak başka veri yok.\"); }};"

    def visit_RestoreStatement(self, node):
        return f"{self.data_pointer_var} = 0;"

    # StackQueueDefinition için özel visit metodu gerekmez çünkü bunlar VariableDeclaration olarak işlenir.

    def visit_PushPopEnqueueDequeue(self, node):
        collection_name = self._transpile_expression(node.collection_name)
        if node.action == "PUSH": # Stack
            value = self._transpile_expression(node.value_or_var)
            return f"{collection_name}.push({value});"
        elif node.action == "POP": # Stack
            var_name = self._transpile_expression(node.value_or_var)
            return f"if (!{collection_name}.empty()) {{ {var_name} = {collection_name}.top(); {collection_name}.pop(); }} else {{ Serial.println(\"Çalışma Zamanı Hatası: Yığın boş (POP).\"); }};"
        elif node.action == "ENQUEUE": # Queue
            value = self._transpile_expression(node.value_or_var)
            return f"{collection_name}.push({value});" # std::queue için push kullanılır
        elif node.action == "DEQUEUE": # Queue
            var_name = self._transpile_expression(node.value_or_var)
            return f"if (!{collection_name}.empty()) {{ {var_name} = {collection_name}.front(); {collection_name}.pop(); }} else {{ Serial.println(\"Çalışma Zamanı Hatası: Kuyruk boş (DEQUEUE).\"); }};"
        return f"// BİLİNMEYEN YIĞIN/KUYRUK EYLEMİ: {node.action}"
    
    def visit_TryCatchStatement(self, node):
        cpp_try_catch = ["try {"]
        self.indent_level += 1
        for stmt in node.try_body:
            transpiled_stmt = self.visit(stmt)
            if transpiled_stmt:
                cpp_try_catch.append(self.indent() + transpiled_stmt)
        self.indent_level -= 1
        cpp_try_catch.append("} catch (const char* msg) {") # C++ string literal exceptions
        self.indent_level += 1
        cpp_try_catch.append(f"{self.indent()}Serial.print(\"Yakalanan İstisna: \");")
        cpp_try_catch.append(f"{self.indent()}Serial.println(msg);")
        for stmt in node.catch_body:
            transpiled_stmt = self.visit(stmt)
            if transpiled_stmt:
                cpp_try_catch.append(self.indent() + transpiled_stmt)
        self.indent_level -= 1
        cpp_try_catch.append("}")
        return "\n".join(cpp_try_catch)

    def visit_ThrowStatement(self, node):
        message = self._transpile_expression(node.message)
        return f"throw {message};"

    def visit_DelayStatement(self, node):
        duration = self._transpile_expression(node.duration)
        self.has_delay = True # Bu zaten Arduino.h'de var, ayrı include gerekmez
        return f"delay({duration});"

    # Diğer düğüm tipleri için temel ziyaretçi metotları (genellikle _transpile_expression'ı çağırır)
    def visit_Identifier(self, node):
        return self._transpile_expression(node)
    
    def visit_Number(self, node):
        return self._transpile_expression(node)

    def visit_String(self, node):
        return self._transpile_expression(node)
    
    def visit_BinaryOp(self, node):
        return self._transpile_expression(node)

    def visit_ArrayType(self, node): # Bu düğümler doğrudan ziyaret edilmez, _transpile_type_node tarafından işlenir.
        return self._transpile_type_node(node)
    
    def visit_StackType(self, node):
        return self._transpile_type_node(node)

    def visit_QueueType(self, node):
        return self._transpile_type_node(node)