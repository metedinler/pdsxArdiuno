-----

Harika\! PDSX dilinin komutlarını ve kullanım amaçlarını detaylı bir şekilde inceleyelim. Bu hem sana hem de kızına PDSX'i öğrenirken yol gösterecek kapsamlı bir başvuru kaynağı olacak. PDSX, özellikle mikrodenetleyicileri programlamak için Basic benzeri basit ve anlaşılır bir sözdizimi sunar.

PDSX komutlarını iki ana kategoriye ayırabiliriz: **Temel Dil Komutları** ve **Donanım Kontrol Komutları**.

-----

## Temel Dil Komutları

Bu komutlar, değişken tanımlama, matematiksel işlemler, mantıksal kararlar ve döngüler gibi programlamanın temel yapı taşlarını oluşturur.

### 1\. Değişken Tanımlama ve Atama

  * **`DIM <değişken_adı> AS <veri_tipi>`**
      * **Amaç:** Bir değişken tanımlamak ve veri tipini belirtmek için kullanılır. Program içinde kullanacağın tüm değişkenleri `DIM` ile tanımlaman gerekir.
      * **Veri Tipleri:**
          * `INTEGER`: Tam sayılar (örn: 10, -5, 0). C++'ta `int`, `long`, `short` gibi karşılıkları olabilir.
          * `DOUBLE` / `SINGLE`: Ondalıklı sayılar (örn: 3.14, -0.5). C++'ta `double` veya `float` karşılığıdır.
          * `STRING`: Metin ifadeleri (örn: "Merhaba Dünya\!"). C++'ta `String` (Arduino'ya özgü) karşılığıdır.
          * `BOOLEAN`: Mantıksal değerler (`TRUE` veya `FALSE`). C++'ta `bool` karşılığıdır.
          * `BYTE`: 0-255 arası değerler için tek baytlık tam sayı. C++'ta `uint8_t` karşılığıdır.
          * `POINTER`: Bir bellek adresini işaret eden değişken. C++'ta `void*` veya belirli bir tipin işaretçisi olabilir.
      * **Örnek:**
        ```pdsx
        DIM counter AS INTEGER
        DIM userName AS STRING
        DIM isLightOn AS BOOLEAN
        ```
  * **`DIM <dizi_adı> AS ARRAY OF <veri_tipi>`**
      * **Amaç:** Belirli bir veri tipindeki elemanları tutan bir dizi (liste) tanımlamak için kullanılır.
      * **Örnek:**
        ```pdsx
        DIM sensorReadings AS ARRAY OF DOUBLE
        DIM names AS ARRAY OF STRING
        ```
  * **`DIM <yığın_adı> AS STACK OF <veri_tipi>`**
      * **Amaç:** Belirli bir veri tipindeki elemanları "Son Giren İlk Çıkar" (LIFO) mantığıyla tutan bir yığın (stack) tanımlamak için kullanılır.
      * **Örnek:**
        ```pdsx
        DIM commandHistory AS STACK OF STRING
        ```
  * **`DIM <kuyruk_adı> AS QUEUE OF <veri_tipi>`**
      * **Amaç:** Belirli bir veri tipindeki elemanları "İlk Giren İlk Çıkar" (FIFO) mantığıyla tutan bir kuyruk (queue) tanımlamak için kullanılır.
      * **Örnek:**
        ```pdsx
        DIM taskQueue AS QUEUE OF INTEGER
        ```
  * **`SET <değişken_adı> = <değer_ifadesi>`**
      * **Amaç:** Bir değişkene bir değer atamak veya bir ifadenin sonucunu bir değişkene kaydetmek için kullanılır.
      * **Örnek:**
        ```pdsx
        SET counter = 0
        SET userName = "Ali Veli"
        SET isLightOn = TRUE
        SET sensorReadings[0] = 25.5 // Dizi elemanına atama
        ```
  * **`ALIAS <yeni_ad> AS <eski_ad>`**
      * **Amaç:** Bir değişkene veya pine başka bir isim (takma ad) vermek için kullanılır. Bu, kodun okunabilirliğini artırır.
      * **Örnek:**
        ```pdsx
        ALIAS LED_BUILTIN AS 13 // 13 numaralı pine LED_BUILTIN adını ver
        ALIAS activeLed AS myPin // myPin değişkenine activeLed adını ver
        ```

### 2\. Matematiksel ve Mantıksal İşlemler

  * **Aritmetik Operatörler:** `+` (toplama), `-` (çıkarma), `*` (çarpma), `/` (bölme), `%` (mod alma).
      * **Örnek:** `result = a + b * 2`
  * **Karşılaştırma Operatörleri:** `==` (eşit), `!=` (eşit değil), `<` (küçük), `>` (büyük), `<=` (küçük eşit), `>=` (büyük eşit).
      * **Örnek:** `IF temp > 25 THEN ...`
  * **Bileşik Atama Operatörleri:** `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=`, `>>=`.
      * **Amaç:** Bir değişkene bir işlem yapıp sonucu tekrar aynı değişkene atamak için kısa yollar.
      * **Örnek:** `counter += 1` (counter = counter + 1 ile aynı)
  * **Artırma/Azaltma Operatörleri:** `++`, `--`.
      * **Amaç:** Bir değişkenin değerini 1 artırmak veya 1 azaltmak için.
      * **Örnek:** `index++` (index = index + 1 ile aynı)
  * **Mantıksal Operatörler:**
      * `AND`: Ve (İki koşul da doğruysa doğru)
      * `OR`: Veya (Koşullardan biri doğruysa doğru)
      * `NOT`: Değil (Koşulun tersini alır)
      * `NAND`: Değil VE (AND'in tersi)
      * `NOR`: Değil VEYA (OR'un tersi)
      * `XOR`: Özel Veya (İki koşul farklıysa doğru)
      * `EQV`: Eşdeğerlik (İki koşul aynıysa doğru)
      * `IMP`: İmplikasyon (İlk koşul yanlışsa veya ikinci koşul doğruysa doğru)
      * **Örnek:** `IF (temp > 20 AND humidity < 60) THEN ...`
  * **Bitwise Operatörler:** `&` (Bitwise AND), `|` (Bitwise OR), `^` (Bitwise XOR), `~` (Bitwise NOT), `<<` (Sol Kaydırma), `>>` (Sağ Kaydırma).
      * **Amaç:** Sayıların ikili (binary) gösterimleri üzerinde bit düzeyinde işlemler yapmak. Donanım kontrolünde sıkça kullanılır.
      * **Örnek:** `flags = flags & mask` (belirli bitleri sıfırlama)
  * **Matematiksel Fonksiyonlar:**
      * `ABS(<sayı>)`: Mutlak değer.
      * `SIN(<derece>)`: Sinüs değeri (derece cinsinden).
      * `COS(<derece>)`: Kosinüs değeri (derece cinsinden).
      * `TAN(<derece>)`: Tanjant değeri (derece cinsinden).
      * `POW(<taban>, <üs>)`: Üslü sayı.
      * `SQRT(<sayı>)`: Karekök.
      * `NROOT(<sayı>, <derece>)`: N. dereceden kök (örn: `NROOT(8, 3)` 8'in küpkökünü verir).
      * `ROUND(<sayı>)`: Sayıyı en yakın tam sayıya yuvarlar.
      * `MEAN(<dizi>)`: Bir dizideki sayıların ortalaması.
      * `MEDIAN(<dizi>)`: Bir dizideki sayıların medyanı (ortanca değeri).
      * `STDDEV(<dizi>)`: Bir dizideki sayıların standart sapması.
      * `VARIANCE(<dizi>)`: Bir dizideki sayıların varyansı.
      * **Örnek:** `result = SQRT(value)`

### 3\. Kontrol Akışı Komutları

  * **`IF <koşul> THEN ... [ELSEIF <koşul> THEN ...] [ELSE ...] END IF`**
      * **Amaç:** Belirli bir koşula bağlı olarak kod bloklarını çalıştırmak.
      * **Örnek:**
        ```pdsx
        IF temperature > 30 THEN
            LOG "Hava çok sıcak!"
        ELSE IF temperature > 20 THEN
            LOG "Hava ılık."
        ELSE
            LOG "Hava soğuk."
        END IF
        ```
  * **`FOR <sayaç> = <başlangıç> TO <bitiş> [STEP <adım>] ... NEXT <sayaç>`**
      * **Amaç:** Belirli bir sayıda tekrarlanan döngüler oluşturmak.
      * **Örnek:**
        ```pdsx
        FOR i = 1 TO 5 STEP 1
            LOG "Döngü Adımı: " + i
        NEXT i
        ```
  * **`DO ... LOOP`**
      * **Amaç:** Bir koşul doğru olduğu sürece veya yanlış olduğu sürece tekrar eden döngüler oluşturmak.
      * **Varyasyonlar:**
          * `DO ... LOOP`: Sonsuz döngü (kullanıcı müdahalesi veya `EXIT DO` ile sonlandırılır).
          * `DO WHILE <koşul> ... LOOP`: Koşul doğru olduğu sürece döngüye devam eder.
          * `DO UNTIL <koşul> ... LOOP`: Koşul doğru olana kadar döngüye devam eder.
          * `DO ... LOOP WHILE <koşul>`: Döngü en az bir kez çalışır, sonra koşul doğru olduğu sürece devam eder.
          * `DO ... LOOP UNTIL <koşul>`: Döngü en az bir kez çalışır, sonra koşul doğru olana kadar devam eder.
      * **Örnek:**
        ```pdsx
        DIM count AS INTEGER = 0
        DO WHILE count < 3
            LOG "Döngü Sayısı: " + count
            count++
        LOOP
        ```
  * **`EXIT DO`**
      * **Amaç:** İçinde bulunduğu `DO...LOOP` döngüsünden anında çıkmak için kullanılır.
      * **Örnek:**
        ```pdsx
        DO
            LOG "Çalışıyor..."
            IF someCondition THEN
                EXIT DO
            END IF
        LOOP
        ```
  * **`SELECT CASE <ifade> ... CASE <değer> ... [CASE <değer>, <değer> ...] END SELECT`**
      * **Amaç:** Bir ifadenin değerine göre farklı kod bloklarını çalıştırmak.
      * **Örnek:**
        ```pdsx
        DIM choice AS INTEGER = 2
        SELECT CASE choice
            CASE 1
                LOG "Seçim 1."
            CASE 2, 3 // Birden fazla değer için
                LOG "Seçim 2 veya 3."
            // PDSX'te şimdilik CASE ELSE desteklenmiyor.
        END SELECT
        ```
  * **`GOSUB <alt_program_adı>`**
      * **Amaç:** Belirtilen alt programa (SUB) atlar, alt program bittikten sonra `GOSUB` komutunun bir sonraki satırından yürütmeye devam eder. Geleneksel Basic'ten kalan bir yapı.
      * **Örnek:**
        ```pdsx
        LOG "Ana Program"
        GOSUB MySub
        LOG "Ana Program Devam Ediyor"

        SUB MySub()
            LOG "Alt Program İçinde"
        END SUB
        ```
  * **`GOTO <etiket_adı>`**
      * **Amaç:** Kodun belirli bir etiketlenmiş satırına atlar. Yapısal programlamada genellikle kaçınılması tavsiye edilir.
      * **Örnek:**
        ```pdsx
        DIM x AS INTEGER = 0
        StartLoop: // Etiket
        LOG "X: " + x
        x++
        IF x < 3 THEN
            GOTO StartLoop
        END IF
        ```

### 4\. Fonksiyonlar ve Alt Programlar (Subroutines)

  * **`FUNC <fonksiyon_adı>([<parametre> AS <tip>, ...]) [AS <dönüş_tipi>] ... END FUNC`**
      * **Amaç:** Değer döndüren yeniden kullanılabilir kod blokları tanımlamak.
      * **Örnek:**
        ```pdsx
        FUNC addNumbers(a AS INTEGER, b AS INTEGER) AS INTEGER
            RETURN a + b
        END FUNC

        DIM sum AS INTEGER
        SET sum = addNumbers(5, 7)
        LOG "Toplam: " + sum
        ```
  * **`SUB <alt_program_adı>([<parametre> AS <tip>, ...]) ... END SUB`**
      * **Amaç:** Değer döndürmeyen yeniden kullanılabilir kod blokları tanımlamak. Genellikle bir görevi yerine getirmek için kullanılır.
      * **Örnek:**
        ```pdsx
        SUB printMessage(msg AS STRING)
            LOG msg
        END SUB

        CALL printMessage("Merhaba PDSX!")
        ```
  * **`EVENT <olay_adı>([<parametre> AS <tip>, ...]) ... END EVENT`**
      * **Amaç:** Donanım kesmeleri veya zamanlayıcılar gibi dış olaylar tetiklendiğinde çalışacak kod blokları tanımlamak. Genellikle `attachInterrupt` veya `CONFIGURE TIMER` ile ilişkilendirilir.
      * **Örnek:**
        ```pdsx
        EVENT onButtonPress()
            LOG "Butona basıldı!"
        END EVENT

        CONFIGURE INTERRUPT 2 ON RISING CALL onButtonPress
        ```
  * **`CALL <fonksiyon_adı/alt_program_adı>([<argüman>, ...]) [INTO <değişken>]`**
      * **Amaç:** Bir fonksiyonu veya alt programı çağırmak. `INTO` anahtar kelimesi ile fonksiyonun döndürdüğü değeri bir değişkene atayabilirsin.
      * **Örnek:**
        ```pdsx
        CALL printMessage("Merhaba!")
        CALL addNumbers(10, 20) INTO myResult
        ```
  * **`RETURN [değer]`**
      * **Amaç:** Bir `FUNC` veya `SUB`'dan çıkmak. `FUNC` içinde kullanılırsa bir değer döndürür. `SUB` içinde kullanılırsa sadece alt programı sonlandırır.

### 5\. Veri Yönetimi

  * **`DATA <değer1>, <değer2>, ...`**
      * **Amaç:** Program içinde okunacak sabit veri listeleri tanımlamak.
      * **Örnek:**
        ```pdsx
        DATA 10, 20, "Elma", 3.14
        ```
  * **`READ <değişken_adı>`**
      * **Amaç:** `DATA` komutunda tanımlanan listeden sırayla bir değer okuyup bir değişkene atamak. Her `READ` komutu, işaretçiyi bir sonraki değere ilerletir.
      * **Örnek:**
        ```pdsx
        DIM num1 AS INTEGER
        DIM fruit AS STRING
        READ num1
        READ fruit
        LOG "Okunan sayı: " + num1 + ", Meyve: " + fruit
        ```
  * **`RESTORE`**
      * **Amaç:** `READ` komutunun işaretçisini `DATA` listesinin başına sıfırlamak. Böylece `DATA` listesi baştan tekrar okunabilir.
      * **Örnek:**
        ```pdsx
        DATA 1, 2, 3
        DIM x AS INTEGER
        READ x // x = 1
        RESTORE
        READ x // x = 1 (tekrar)
        ```
  * **`PUSH <değer> TO <yığın_adı>`**
      * **Amaç:** Bir değeri yığının (STACK) en üstüne eklemek.
      * **Örnek:**
        ```pdsx
        PUSH 5 TO myStack
        ```
  * **`POP <yığın_adı> INTO <değişken_adı>`**
      * **Amaç:** Yığının (STACK) en üstündeki değeri çıkarmak ve belirtilen değişkene atamak.
      * **Örnek:**
        ```pdsx
        POP myStack INTO poppedValue
        ```
  * **`ENQUEUE <değer> TO <kuyruk_adı>`**
      * **Amaç:** Bir değeri kuyruğun (QUEUE) sonuna eklemek.
      * **Örnek:**
        ```pdsx
        ENQUEUE "Görev A" TO taskQueue
        ```
  * **`DEQUEUE <kuyruk_adı> INTO <değişken_adı>`**
      * **Amaç:** Kuyruğun (QUEUE) başındaki değeri çıkarmak ve belirtilen değişkene atamak.
      * **Örnek:**
        ```pdsx
        DEQUEUE taskQueue INTO nextTask
        ```

### 6\. Hata Yönetimi

  * **`TRY ... CATCH ... END TRY`**
      * **Amaç:** Kod blokları içindeki olası hataları yakalamak ve özel bir hata işleme kodu çalıştırmak.
      * **Örnek:**
        ```pdsx
        TRY
            DIM result AS DOUBLE = 10 / 0 // Sıfıra bölme hatası
            LOG "Bu satır çalışmaz."
        CATCH
            LOG "Bir hata oluştu!"
        END TRY
        ```
  * **`THROW <mesaj>`**
      * **Amaç:** Bilinçli olarak bir hata durumu yaratmak ve bir `TRY...CATCH` bloğu tarafından yakalanabilecek bir istisna fırlatmak.
      * **Örnek:**
        ```pdsx
        DIM temperature AS INTEGER = 150
        IF temperature > 100 THEN
            THROW "Sıcaklık eşik değerini aştı!"
        END IF
        ```

-----

## Donanım Kontrol Komutları

Bu komutlar, Arduino ve Deneyap Kart gibi mikrodenetleyicilerin fiziksel pinlerini, sensörlerini ve aktüatörlerini kontrol etmek için kullanılır.

### 1\. Genel Pin Kontrolü

  * **`CONFIGURE PIN <pin_numarası> AS <mod>`**
      * **Amaç:** Bir dijital pini giriş (`INPUT`) veya çıkış (`OUTPUT`) olarak yapılandırmak.
      * **Modlar:** `INPUT`, `OUTPUT`.
      * **Örnek:**
        ```pdsx
        CONFIGURE PIN 13 AS OUTPUT // LED pini
        CONFIGURE PIN 2 AS INPUT   // Buton pini
        ```
  * **`DIGITALWRITE <pin_numarası_veya_adı>, <değer>`**
      * **Amaç:** Bir dijital pini `HIGH` (yüksek voltaj, AÇIK) veya `LOW` (düşük voltaj, KAPALI) olarak ayarlamak.
      * **Değerler:** `HIGH`, `LOW`.
      * **Örnek:**
        ```pdsx
        DIGITALWRITE 13, HIGH // 13 numaralı pindeki LED'i yak
        DIGITALWRITE MY_LED, LOW // MY_LED adını verdiğin pindeki LED'i söndür
        ```
  * **`READ PIN <pin_numarası_veya_adı> INTO <değişken_adı>`**
      * **Amaç:** Bir dijital pindeki voltaj seviyesini okuyup (`HIGH` veya `LOW`) bir değişkene atamak.
      * **Örnek:**
        ```pdsx
        DIM buttonState AS INTEGER
        READ PIN 2 INTO buttonState // 2 numaralı pindeki butonun durumunu oku
        ```
  * **`SET PIN <pin_numarası_veya_adı> TO <değer>`**
      * **Amaç:** `DIGITALWRITE` ile aynı işlevi gören alternatif bir sözdizimi.
      * **Örnek:**
        ```pdsx
        SET PIN 13 TO HIGH
        ```

### 2\. Zamanlama

  * **`DELAY <milisaniye_süresi>`**
      * **Amaç:** Programın belirli bir süre (milisaniye cinsinden) duraklamasını sağlamak.
      * **Örnek:**
        ```pdsx
        DIGITALWRITE 13, HIGH
        DELAY 1000 // 1 saniye bekle
        DIGITALWRITE 13, LOW
        ```

### 3\. Seri Haberleşme

  * **`SERIAL BEGIN <baud_rate>`**
      * **Amaç:** Bilgisayar ile mikrodenetleyici arasında seri haberleşmeyi başlatmak ve iletişim hızını (baud rate) ayarlamak.
      * **Örnek:**
        ```pdsx
        SERIAL BEGIN 9600 // 9600 baud hızında seri haberleşmeyi başlat
        ```
  * **`LOG <mesaj>`** / **`INFO <mesaj>`**
      * **Amaç:** Seri monitöre metin mesajları yazdırmak. Hata ayıklama veya bilgi mesajları için kullanılır. `Serial.println()` C++ karşılığıdır.
      * **Örnek:**
        ```pdsx
        LOG "Program Başladı."
        INFO "Sensör değeri: " + sensorValue
        ```

### 4\. Servo Motor Kontrolü

  * **`DEFINE SERVO <servo_adı> ON PIN <pin_numarası>`**
      * **Amaç:** Bir servo motoru belirli bir pine bağlamak ve program içinde kullanmak üzere bir isimle tanımlamak.
      * **Örnek:**
        ```pdsx
        DEFINE SERVO myServo ON PIN 9
        ```
  * **`MOVE SERVO <servo_adı> TO <derece>`**
      * **Amaç:** Tanımlanmış bir servo motoru belirli bir açıya (0-180 derece arası) hareket ettirmek.
      * **Örnek:**
        ```pdsx
        MOVE SERVO myServo TO 90 // Servoyu 90 dereceye getir
        ```

### 5\. Buzzer Kontrolü

  * **`DEFINE BUZZER ON PIN <pin_numarası>`**
      * **Amaç:** Bir buzzer (sesli uyarıcı) modülünü belirli bir pine bağlamak ve tanımlamak.
      * **Örnek:**
        ```pdsx
        DEFINE BUZZER ON PIN 8
        ```
  * **`BUZZER ON [frekans]`**
      * **Amaç:** Buzzer'ı belirli bir frekansta ses çıkarması için açmak. Frekans belirtilmezse varsayılan bir ses çıkarabilir veya hiçbir şey yapmayabilir.
      * **Örnek:**
        ```pdsx
        BUZZER ON 1000 // 1000 Hz frekansta ses çıkar
        ```
  * **`BUZZER OFF`**
      * **Amaç:** Buzzer'ı kapatmak.
      * **Örnek:**
        ```pdsx
        BUZZER OFF
        ```

### 6\. Zamanlayıcılar (Timers)

  * **`CONFIGURE TIMER <id> INTERVAL <milisaniye> COUNT <sayım_sınırı> CALL <event_adı>`**
      * **Amaç:** Belirli aralıklarla (milisaniye cinsinden) tetiklenecek bir yazılımsal veya donanımsal zamanlayıcı yapılandırmak. Zamanlayıcı, her tetiklendiğinde belirtilen `EVENT`'ı çağırır. `COUNT` değeri `-1` ise sonsuz kez çalışır.
      * **Örnek:**
        ```pdsx
        EVENT toggleLedEvent()
            DIGITALWRITE 13, HIGH
            DELAY 100
            DIGITALWRITE 13, LOW
        END EVENT

        CONFIGURE TIMER 1 INTERVAL 500 COUNT 10 CALL toggleLedEvent // Her 500ms'de bir, 10 kez
        ```

### 7\. Kesmeler (Interrupts)

  * **`CONFIGURE INTERRUPT <pin_numarası> ON <mod> CALL <event_adı>`**
      * **Amaç:** Belirli bir dijital pin üzerindeki voltaj değişimlerini (kesmeler) dinlemek. Değişim algılandığında belirtilen `EVENT`'ı çağırır.
      * **Modlar:**
          * `RISING`: Voltaj LOW'dan HIGH'a yükseldiğinde.
          * `FALLING`: Voltaj HIGH'dan LOW'a düştüğünde.
          * `CHANGE`: Voltaj herhangi bir şekilde değiştiğinde (hem yükselme hem düşme).
      * **Örnek:**
        ```pdsx
        EVENT onButtonPress()
            LOG "Buton Kesmesi Tetiklendi!"
        END EVENT

        CONFIGURE INTERRUPT 2 ON FALLING CALL onButtonPress // Pin 2'deki düşen kenarda kesme tetikle
        ```

### 8\. Analog Okuma (ADC)

  * **`CONFIGURE ADC <pin_numarası> RESOLUTION <bit_çözünürlüğü>`**
      * **Amaç:** Analog-Dijital Dönüştürücü (ADC) pinlerinin okuma çözünürlüğünü ayarlamak. Bu, pinin 0 ile belirli bir maksimum voltaj arasındaki analog değerleri kaç farklı seviyede okuyacağını belirler (örn: 10 bit = 0-1023, 12 bit = 0-4095).
      * **Örnek:**
        ```pdsx
        CONFIGURE ADC A0 RESOLUTION 10 // A0 pinini 10 bit çözünürlükte oku
        ```
  * **`READ ADC PIN <pin_numarası_veya_adı> INTO <değişken_adı>`**
      * **Amaç:** Bir analog pinden analog bir değer okuyup (voltaj seviyesine bağlı olarak 0 ile çözünürlük maksimumu arasında) bir değişkene atamak.
      * **Örnek:**
        ```pdsx
        DIM lightSensorValue AS INTEGER
        READ ADC PIN A0 INTO lightSensorValue // A0 pinindeki analog değeri oku
        ```

### 9\. PWM (Darbe Genişlik Modülasyonu)

  * **`CONFIGURE PWM <pin_numarası> FREQUENCY <Hz> DUTY <değer>`**
      * **Amaç:** Bir pinde PWM sinyali oluşturmak. Bu, LED parlaklığını kontrol etmek veya motor hızını ayarlamak gibi analog davranışları dijital pinler aracılığıyla simüle etmek için kullanılır.
      * **Frekans:** Hertz (Hz) cinsinden sinyal frekansı.
      * **Duty:** PWM sinyalinin açık kalma süresi (genellikle 0-255 veya 0-1023 gibi bir aralıkta bir sayı). Yüksek değer daha parlak LED veya daha hızlı motor anlamına gelir.
      * **Örnek:**
        ```pdsx
        CONFIGURE PWM 5 FREQUENCY 1000 DUTY 128 // Pin 5'te 1000Hz, %50 görev döngülü PWM
        ```

### 10\. WiFi Bağlantısı

  * **`WIFI CONNECT <ssid> <password>`**
      * **Amaç:** Mikrodenetleyicinizi bir Wi-Fi ağına bağlamak. Genellikle ESP32 veya Deneyap Kart gibi Wi-Fi özellikli kartlarda kullanılır.
      * **ssid:** Bağlanılacak Wi-Fi ağının adı (String).
      * **password:** Wi-Fi ağının şifresi (String).
      * **Örnek:**
        ```pdsx
        WIFI CONNECT "MyHomeNetwork" "MySecretPassword"
        LOG "WiFi'ye bağlanmaya çalışılıyor..."
        ```

### 11\. Diğer Donanım Ayarları

  * **`HARDWARE MAP <platform_adı>`**
      * **Amaç:** Derleyiciye veya yorumlayıcıya hangi donanım platformunu hedeflediğini bildirmek. Bu, `hardware_map.json` dosyasındaki bilgileri yükler ve platforma özgü kütüphanelerin dahil edilmesini ve komutların doğru çevrilmesini sağlar.
      * **Platformlar:** `ARDUINO_UNO`, `ESP32`, `DENEYAP_KART`.
      * **Örnek:**
        ```pdsx
        HARDWARE MAP DENEYAP_KART
        ```

-----

Bu detaylı PDSX komut listesi, dilin sunduğu tüm temel programlama yapılarını ve donanım kontrol yeteneklerini kapsamaktadır. Bu bilgileri kullanarak, PDSX kodlarını daha bilinçli bir şekilde yazabilir ve kızınla birlikte projeler geliştirmeye başlayabilirsin.

Umarım bu komut referansı işine yarar\! Şimdi, bu komutlarla ilgili aklına takılan herhangi bir soru varsa veya belirli bir komutun kullanımı hakkında daha fazla örnek istersen, çekinmeden sorabilirsin.