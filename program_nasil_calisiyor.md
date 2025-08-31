-----

Harika bir merak\! Bilgisayar bilimleri dünyasında derleyicilerin nasıl çalıştığını anlamak, kodlamaya bakış açını zenginleştirecektir. Temel döngülerin, koşullu yapıların, değişkenlerin ve sınıfların bir derleyici tarafından nasıl işlendiğini adım adım inceleyelim. Bu, soyut sözdizimi ağacı (AST) ve kod üretimi süreçlerini somutlaştırmamızı sağlayacak.

Bir derleyicinin, PDSX gibi üst düzey bir dilde yazdığın kodun anlamını anlayıp, bunu daha düşük seviyeli bir dile (bizim örneğimizde C++) nasıl çevirdiğini görelim.

### 1\. Temel Döngüler: `FOR...NEXT` ve `DO...LOOP`

Döngüler, derleyicinin karmaşık kontrol akışını nasıl yönettiğini gösteren güzel örneklerdir.

#### `FOR...NEXT` Döngüsü

**PDSX Kodu:**

```pdsx
DIM i AS INTEGER
FOR i = 1 TO 10 STEP 1
    LOG "Sayı: " + i
NEXT i
```

**Derleyicinin İçsel İşleyişi:**

1.  **Lexer (Sözcüksel Analiz):** Kodu token'lara (kelimelere) ayırır: `DIM`, `i`, `AS`, `INTEGER`, `FOR`, `i`, `=`, `1`, `TO`, `10`, `STEP`, `1`, `LOG`, `"Sayı: "`, `+`, `i`, `NEXT`, `i`.

2.  **Parser (Sözdizimsel Analiz & AST Oluşturma):** Bu token'ları bir **Soyut Sözdizimi Ağacı (AST)** yapısına dönüştürür. `ForStatement` adında bir düğüm oluşturulur ve içine aşağıdaki bilgiler yerleştirilir:

      * **Değişken Adı (`var_name`):** `i`
      * **Başlangıç İfadesi (`start_expr`):** `Number(1)` düğümü
      * **Bitiş İfadesi (`end_expr`):** `Number(10)` düğümü
      * **Adım İfadesi (`step_expr`):** `Number(1)` düğümü
      * **Gövde (`body`):** İçindeki `LOG "Sayı: " + i` ifadesini temsil eden bir `LogInfoCommand` (veya `HardwareCommand` alt sınıfı) düğümü.
        AST, kodun hiyerarşik yapısını temsil eder.

3.  **Semantic Analyzer (Anlamsal Analiz - Opsiyonel ama Önemli):** (Bizim derleyicimizde bu adım sadeleştirilmişti ama gerçek bir derleyicide olur) `i` değişkeninin `INTEGER` tipinde olduğunu doğrular, `FOR` döngüsünün parametrelerinin uyumlu olduğundan emin olur.

4.  **Code Generation (Kod Üretimi - Transpilerımızdaki `CppTranspiler`):** `ForStatement` AST düğümünü C++ karşılığına çevirir. Genellikle bir `for` döngüsü:

    ```cpp
    // ... C++ kod çıktısı ...
    void loop() {
      // PDSX: FOR i = 1 TO 10 STEP 1
      for (int i = 1; i <= 10; i += 1) { // i'nin tipi burada belirlenir
        Serial.print("Sayı: ");
        Serial.println(i);
      }
    }
    ```

    Burada `i` değişkeninin tipi (`int`), döngü koşulu (`i <= 10`) ve adım (`i += 1`) PDSX yapısından türetilir.

#### `DO...LOOP` Döngüsü

**PDSX Kodu:**

```pdsx
DIM counter AS INTEGER = 0
DO WHILE counter < 5
    LOG "Sayaç: " + counter
    counter++
LOOP
```

**Derleyicinin İçsel İşleyişi:**

1.  **Lexer/Parser:** Kodu token'lara ayırır ve bir `LoopStatement` AST düğümü oluşturur.

      * **Gövde (`body`):** `LOG` ve `counter++` deyimleri.
      * **Döngü Tipi (`loop_type`):** `DO_WHILE`
      * **Koşul (`condition`):** `BinaryOp(Identifier(counter), <, Number(5))` düğümü.

2.  **Code Generation:** `LoopStatement` düğümünü uygun C++ döngüsüne çevirir.

    ```cpp
    // ... C++ kod çıktısı ...
    void loop() {
      int counter = 0; // DIM counter AS INTEGER = 0
      // PDSX: DO WHILE counter < 5 ... LOOP
      while (counter < 5) { // Koşul burada
        Serial.print("Sayaç: ");
        Serial.println(counter);
        counter++; // counter++ operatörü
      }
    }
    ```

    `DO...LOOP UNTIL`, `DO...LOOP WHILE`, `DO...LOOP` (sonsuz) gibi diğer varyasyonlar da benzer şekilde C++'ın `while` veya `do-while` döngülerine çevrilir. `EXIT DO` komutu ise C++'ta `break;` olarak karşılık bulur.

-----

### 2\. Koşullu İfadeler: `IF...THEN...ELSE...END IF`

Koşullu ifadeler, derleyicinin dallanmaları nasıl yönettiğini gösterir.

**PDSX Kodu:**

```pdsx
DIM sıcaklık AS INTEGER = 25
IF sıcaklık > 30 THEN
    LOG "Çok sıcak!"
ELSE IF sıcaklık > 20 THEN
    LOG "Ilık."
ELSE
    LOG "Soğuk."
END IF
```

**Derleyicinin İçsel İşleyişi:**

1.  **Lexer/Parser:** `IfStatement` AST düğümleri oluşturur. İç içe `IF`'ler için birden fazla `IfStatement` düğümü oluşur.

      * **Koşul (`condition`):** `BinaryOp(Identifier(sıcaklık), >, Number(30))`
      * **Then Bloğu (`then_body`):** `LOG "Çok sıcak!"`
      * **Else Bloğu (`else_body`):** Başka bir `IfStatement` düğümü (içteki `ELSE IF` için), onun `ELSE` bloğunda ise son `LOG "Soğuk."` ifadesi yer alır.

2.  **Code Generation:** AST'deki bu `IfStatement` hiyerarşisini C++'ın `if-else if-else` yapısına çevirir.

    ```cpp
    // ... C++ kod çıktısı ...
    void loop() {
      int sıcaklık = 25;
      if ((sıcaklık > 30)) {
        Serial.println("Çok sıcak!");
      } else if ((sıcaklık > 20)) { // Else if yapısı
        Serial.println("Ilık.");
      } else {
        Serial.println("Soğuk.");
      }
    }
    ```

-----

### 3\. Çoklu Durum Seçimi: `SELECT CASE`

`SELECT CASE`, belirli bir değişkenin veya ifadenin farklı değerlerine göre farklı kod bloklarını yürütmek için kullanılır.

**PDSX Kodu:**

```pdsx
DIM renkKodu AS INTEGER = 2
SELECT CASE renkKodu
    CASE 1
        LOG "Kırmızı"
    CASE 2
        LOG "Mavi"
    CASE 3
        LOG "Yeşil"
    CASE ELSE // Bu kısım PDSX'te henüz desteklemiyor ama ekleyebiliriz.
        LOG "Bilinmeyen Renk"
END SELECT
```

**Derleyicinin İçsel İşleyişi:**

1.  **Lexer/Parser:** `SelectCaseStatement` AST düğümü oluşturulur.

      * **İfade (`expr`):** `Identifier(renkKodu)`
      * **Durumlar (`cases`):** Her `CASE` bloğu için bir liste (`[(değer, gövde), (değer, gövde)]`). Örneğin `(Number(1), [LogCommand("Kırmızı")])`.

2.  **Code Generation:** `SelectCaseStatement` düğümünü C++ `switch` yapısına çevirir.

    ```cpp
    // ... C++ kod çıktısı ...
    void loop() {
      int renkKodu = 2;
      switch (renkKodu) {
        case 1: {
          Serial.println("Kırmızı");
          break;
        }
        case 2: {
          Serial.println("Mavi");
          break;
        }
        case 3: {
          Serial.println("Yeşil");
          break;
        }
        // Eğer PDSX'te CASE ELSE olsaydı buraya default: eklenecekti
        // default: {
        //   Serial.println("Bilinmeyen Renk");
        //   break;
        // }
      }
    }
    ```

    Her `CASE` bloğunun sonunda otomatik olarak `break;` eklenir.

-----

### 4\. Değişkenler ve Tipler

Değişkenler, derleyicinin en temel yapı taşlarındandır.

**PDSX Kodu:**

```pdsx
DIM isRunning AS BOOLEAN
DIM sensorValue AS INTEGER
DIM message AS STRING
DIM temperatures AS ARRAY OF DOUBLE
DIM myStack AS STACK OF INTEGER
```

**Derleyicinin İçsel İşleyişi:**

1.  **Lexer/Parser:** Her `DIM` ifadesi için bir `VariableDeclaration` AST düğümü oluşturur. Bu düğümler, değişkenin adını ve tipini (veya koleksiyon tipini ve temel tipini) içerir.

      * `isRunning`: `Identifier("isRunning")`, `Identifier("BOOLEAN")`
      * `temperatures`: `Identifier("temperatures")`, `ArrayType(Identifier("DOUBLE"))`

2.  **Semantic Analyzer:** Değişken adlarının geçerli olup olmadığını, ayrılmış kelime olup olmadığını, aynı kapsamda tekrar tanımlanıp tanımlanmadığını kontrol eder. Tip sistemi için, atanacak değerin veya işlemdeki değerlerin değişkenin tipiyle uyumlu olup olmadığını kontrol eder.

3.  **Code Generation:** PDSX tiplerini C++ karşılıklarına çevirir ve değişken tanımlamalarını uygun kapsamda (global veya fonksiyon içi) yapar.

    ```cpp
    // ... C++ kod çıktısı (global alanda) ...
    bool isRunning;
    int sensorValue;
    String message;
    std::vector<double> temperatures; // ARRAY OF DOUBLE -> std::vector<double>
    std::stack<int> myStack;         // STACK OF INTEGER -> std::stack<int>
    ```

    Bu noktada, `PDSX_TYPE_MAP` ve `_transpile_type_node` fonksiyonumuz devreye girer.

-----

### 5\. Sınıflar (`CLASS` ve `TYPE` - Struct)

Nesne yönelimli yapılar, kodun daha modüler ve yönetilebilir olmasını sağlar.

#### Yapı/Struct Tanımı (`TYPE...END TYPE`)

**PDSX Kodu:**

```pdsx
TYPE Point2D
    x AS DOUBLE
    y AS DOUBLE
END TYPE

DIM myPoint AS Point2D
SET myPoint.x = 10.5
SET myPoint.y = 20.0
LOG "Nokta X: " + myPoint.x
```

**Derleyicinin İçsel İşleyişi:**

1.  **Lexer/Parser:** `StructDefinition` AST düğümü oluşturur.

      * **Adı (`name`):** `Point2D`
      * **Alanlar (`fields`):** `[(x, Identifier(DOUBLE)), (y, Identifier(DOUBLE))]`

2.  **Code Generation:** C++ `struct` yapısına çevirir. Alanlara erişim de `.` operatörü ile yapılır.

    ```cpp
    // ... C++ kod çıktısı ...
    struct Point2D {
        double x;
        double y;
    };

    void setup() {
        // ...
        Point2D myPoint; // DIM myPoint AS Point2D
        myPoint.x = 10.5;
        myPoint.y = 20.0;
        Serial.print("Nokta X: ");
        Serial.println(myPoint.x);
    }
    ```

#### Sınıf Tanımı (`CLASS...END CLASS`)

**PDSX Kodu:**

```pdsx
CLASS MyRobot INHERITS BaseRobot // INHERITS opsiyonel
    PRIVATE motorSpeed AS INTEGER
    PUBLIC color AS STRING

    SUB initRobot(speed AS INTEGER)
        SET motorSpeed = speed
        LOG "Robot başlatıldı, hız: " + motorSpeed
    END SUB

    PUBLIC FUNC getSpeed() AS INTEGER
        RETURN motorSpeed
    END FUNC
END CLASS

DIM robot1 AS MyRobot
// SET robot1.color = "Mavi" // Transpiler/Interpreter'da nesne oluşturma ve üye ataması desteklenmeli
// CALL robot1.initRobot(100)
// LOG "Robot hızı: " + robot1.getSpeed()
```

**Derleyicinin İçsel İşleyişi:**

1.  **Lexer/Parser:** `ClassDefinition` AST düğümü oluşturur.

      * **Adı (`name`):** `MyRobot`
      * **Ebeveyn (`parent`):** `BaseRobot` (varsa)
      * **Alanlar (`fields`):** `[(motorSpeed, INTEGER, PRIVATE), (color, STRING, PUBLIC)]`
      * **Metotlar (`methods`):** `FunctionDefinition` veya `SubDefinition` düğümleri.

2.  **Code Generation:** C++ `class` yapısına çevirir. Erişim belirleyicileri (`public`, `private`) ve metotların sınıf dışı implementasyonu (`MyRobot::initRobot`) dikkate alınır.

    ```cpp
    // ... C++ kod çıktısı ...
    class MyRobot : public BaseRobot { // INHERITS BaseRobot -> : public BaseRobot
    private: // PRIVATE alanı
        int motorSpeed;
    public:  // PUBLIC alanı
        String color;

        // Metot prototipleri (sınıf tanımında)
        void initRobot(int speed);
        int getSpeed();
    };

    // Metot implementasyonları (sınıf dışı)
    void MyRobot::initRobot(int speed) {
        motorSpeed = speed;
        Serial.print("Robot başlatıldı, hız: ");
        Serial.println(motorSpeed);
    }

    int MyRobot::getSpeed() {
        return motorSpeed;
    }

    void setup() {
        // ...
        MyRobot robot1; // DIM robot1 AS MyRobot
        // robot1.color = "Mavi";
        // robot1.initRobot(100);
        // Serial.print("Robot hızı: ");
        // Serial.println(robot1.getSpeed());
    }
    ```

    Bu örnekler, bir derleyicinin kaynak kodu nasıl ayrıştırdığını, bir AST oluşturduğunu 
    ve bu AST'yi hedef dile (C++) nasıl çevirdiğini temel düzeyde gösterir. Her adım, 
    programın yapısını ve anlamını korurken, onu bir dilden diğerine dönüştürmenin farklı katmanlarını temsil eder.

Umarım bu detaylı açıklama, derleyicilerin iç dünyasına dair merakını gidermeye yardımcı olmuştur.
 Bu, sadece bir başlangıç ve derleyici teknolojileri çok daha derin ve karmaşıktır\!

## Şimdi, bu bilgileri sindirip, projenin mevcut haliyle nasıl ilerlemek istediğini bana bildirebilirsin.