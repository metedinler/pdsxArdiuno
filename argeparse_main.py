# argeparse_main.py
import argparse
import sys
import logging

# Loglama yapılandırması (hata ayıklama için faydalı)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Diğer Python dosyalarımızdan Lexer, Parser ve Transpiler sınıflarını içe aktaracağız.
from pdsx_lexer import Lexer
from pdsx_parser import Parser
from pdsx_transpiler import CppTranspiler
from pdsx_interpreter import PDSXInterpreter


def main():
    parser = argparse.ArgumentParser(description="ARGEparse PDSX Compiler/Interpreter")
    parser.add_argument("input_file", help="PDSX kaynak dosyasının yolu (.pdsx uzantılı olmalıdır)")
    parser.add_argument("--mode", choices=["transpile", "interpret"], default="transpile",
                        help="Çalışma modu: 'transpile' (C++'a çevir) veya 'interpret' (doğrudan yorumla). Varsayılan: transpile")
    parser.add_argument("--platform", choices=["ARDUINO_UNO", "ESP32", "DENEYAP_KART"], default="ARDUINO_UNO",
                        help="Hedef donanım platformu (sadece 'transpile' modu için geçerlidir). Varsayılan: ARDUINO_UNO")
    parser.add_argument("--output_file", help="Çıkış dosyasının adı (sadece 'transpile' modu için geçerlidir).")

    args = parser.parse_args()

    # Dosya uzantısı kontrolü
    if not args.input_file.endswith(".pdsx"):
        logging.error(f"Hata: Giriş dosyası '.pdsx' uzantısına sahip olmalıdır: {args.input_file}")
        sys.exit(1)

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            pdsx_code = f.read()
    except FileNotFoundError:
        logging.error(f"Hata: Giriş dosyası bulunamadı: {args.input_file}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Giriş dosyası okunurken hata oluştu: {e}")
        sys.exit(1)

    logging.info(f"PDSX kodu okundu: {args.input_file}")

    try:
        # Lexer aşaması
        lexer = Lexer(pdsx_code)
        tokens = lexer.tokenize()
        logging.info(f"Tokenizasyon tamamlandı. Toplam token: {len(tokens)}")

        # Parser aşaması
        parser = Parser(tokens)
        ast = parser.parse()
        logging.info(f"AST ayrıştırma tamamlandı. Üst düzey deyim: {len(ast.statements)}")

        if args.mode == "transpile":
            logging.info(f"Mod: Transpile (C++'a çeviriliyor) - Hedef Platform: {args.platform}")
            transpiler = CppTranspiler(ast, args.platform)
            cpp_output = transpiler.transpile()

            output_filename = args.output_file
            if not output_filename:
                # Varsayılan çıkış dosyası adı: input_file.cpp
                output_filename = args.input_file.replace(".pdsx", ".cpp")
            
            # Eğer .cpp uzantısı yoksa ekle
            if not output_filename.lower().endswith(".cpp"):
                output_filename += ".cpp"

            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(cpp_output)
            logging.info(f"Çevrilen C++ kodu başarıyla kaydedildi: {output_filename}")

        elif args.mode == "interpret":
            logging.info("Mod: Interpret (PDSX kodu doğrudan yorumlanıyor)")
            
            # Debug: AST'yi print edelim (gerekirse açabilirsiniz)
            # print("=== AST DEBUG ===")
            # for i, stmt in enumerate(ast.statements):
            #     print(f"Statement {i}: {stmt}")
            #     if hasattr(stmt, 'args'):
            #         print(f"  Args: {stmt.args}")
            #         for j, arg in enumerate(stmt.args):
            #             if hasattr(arg, 'op'):
            #                 print(f"    Arg {j} BinaryOp: left={arg.left}, op='{arg.op}', right={arg.right}")
            #     if hasattr(stmt, 'initial_value'):
            #         print(f"  Initial Value: {stmt.initial_value}")
            # print("=== END AST DEBUG ===")
            # return  # Şimdilik interpreter'ı çalıştırma
            
            # Yorumlayıcıyı çalıştır
            interpreter = PDSXInterpreter(ast)
            interpreter.run()
            logging.info("Yorumlama tamamlandı (simülasyon).")

    except SyntaxError as e:
        logging.error(f"Sözdizimi Hatası: {e}")
        sys.exit(1)
    except ValueError as e: # Geçersiz platform gibi hatalar için
        logging.error(f"Yapılandırma Hatası: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Beklenmeyen Hata: {e}", exc_info=True) # exc_info ile traceback göster
        sys.exit(1)

if __name__ == "__main__":
    main()