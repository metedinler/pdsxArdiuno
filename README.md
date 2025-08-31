PDSX'in arkasındaki vizyonu ve teknik yapısını yabancı bir programcıya tanıtmak için hazırlanan bu kapsamlı rehber, dilin temel özelliklerini, mimarisini ve benzersiz yeteneklerini derinlemesine inceliyor. Turkce tanitim yazisi ingilizcenin ardindan verilmistir.

-----

### PDSX: Bridging the Gap Between Simplicity and Power

PDSX, a novel programming language, stands out by blending the approachable syntax of classic BASIC with the robust capabilities required for modern embedded systems. Designed specifically for microcontrollers like Arduino, ESP32, and DENEYAP Kart, PDSX serves as a powerful yet intuitive tool for both educational purposes and rapid prototyping. It operates on a two-pronged system: a **Transpiler** that converts PDSX code into highly optimized C++ and a comprehensive **Interpreter** that simulates hardware behavior for a seamless development experience.

-----

### Language Features and Syntax

PDSX's syntax is clean and straightforward, making it highly readable and easy to learn for programmers familiar with imperative languages.

#### Core Language Constructs

  * **Variable Declaration**: Variables are explicitly typed using the `DIM` keyword, which enhances code clarity and type safety.
    ```pdsx
    DIM counter AS INTEGER
    DIM userName AS STRING
    DIM isLightOn AS BOOLEAN
    ```
  * **Data Structures**: Beyond simple types, PDSX supports advanced data structures critical for complex applications. It includes **Arrays** (`ARRAY OF`), **Stacks** (`STACK OF`), and **Queues** (`QUEUE OF`), each with dedicated commands for manipulation.
    ```pdsx
    DIM temperatures AS ARRAY OF DOUBLE
    DIM commandHistory AS STACK OF STRING
    DIM taskQueue AS QUEUE OF INTEGER
    ```
  * **Control Flow**: PDSX provides all the essential control flow statements. The `FOR...NEXT` loop is perfect for definite iterations, while `DO...LOOP` offers flexible indefinite looping with `WHILE` or `UNTIL` conditions. For multi-way branching, `IF...THEN...ELSEIF...END IF` and `SELECT CASE` offer clear, structured options.
  * **Functions and Subroutines**: The language differentiates between `FUNC` (functions that return a value) and `SUB` (subroutines that do not). The `CALL` keyword provides a clear way to invoke these routines, with an optional `INTO` clause to capture a returned value.
  * **Error Handling**: A robust `TRY...CATCH...END TRY` block allows for graceful error management. Programmers can intentionally trigger exceptions using the `THROW` command to handle unexpected states.

#### Unique Hardware Integration

PDSX isn't just a general-purpose language; it's purpose-built for embedded systems, offering direct and high-level control over hardware components.

  * **Pin Configuration**: The `CONFIGURE PIN` command simplifies the setup process, abstracting C++ functions like `pinMode()`.
    ```pdsx
    CONFIGURE PIN 13 AS OUTPUT
    ```
  * **Sensors and Actuators**: PDSX includes high-level commands for common peripherals. `MOVE SERVO` and `DEFINE BUZZER` provide a clean API for controlling these devices, eliminating the need to manage low-level PWM signals or library objects manually.
  * **Event-Driven Programming**: PDSX excels in event-driven architectures, which are fundamental to embedded systems. The `EVENT` keyword defines interrupt service routines (ISRs) and timer callbacks. These events can be linked to hardware triggers using `CONFIGURE INTERRUPT` (for pin changes) or `CONFIGURE TIMER` (for time-based actions).
  * **WiFi Connectivity**: For IoT projects, the `WIFI CONNECT` command streamlines the often-complex process of network setup on boards like the ESP32.

-----

### Architectural Deep Dive: The PDSX Compiler/Interpreter Pipeline

The power of PDSX lies in its modular and well-defined architecture, which separates concerns into distinct phases, a hallmark of professional language design.

#### 1\. The Lexer (`pdsx_lexer.py`)

The journey begins here. The Lexer's sole purpose is to perform **lexical analysis**, breaking down the source code into a stream of tokens. It uses regular expressions to categorize each word or symbol as a keyword, identifier, operator, or literal value. This step is crucial as it removes comments and whitespace, preparing a clean input for the next phase.

#### 2\. The Parser (`pdsx_parser.py`)

The Parser is the brain of the operation. It takes the stream of tokens and constructs an **Abstract Syntax Tree (AST)**. This tree is a hierarchical representation of the code's structure, reflecting the relationships between different language constructs (e.g., `IfStatement` nodes containing a `condition` and `then_body` child nodes). This structured representation is what allows for a deeper understanding of the code's meaning, not just its words. The parser's `_get_precedence()` function is a key element, ensuring that mathematical and logical operations are evaluated in the correct order.

#### 3\. The Transpiler (`pdsx_transpiler.py`)

The Transpiler transforms the AST into C++ code, acting as the bridge to the hardware. It traverses the AST, converting each PDSX construct into its C++ equivalent. For example, a `FOR...NEXT` loop AST node becomes a C++ `for` loop, and a `DIGITALWRITE` command becomes a `digitalWrite()` function call. This approach allows developers to write in the simple PDSX language while benefiting from the speed and efficiency of compiled C++ code.

#### 4\. The Interpreter (`pdsx_interpreter.py`)

Complementing the Transpiler is the Interpreter. Instead of generating C++ code, it directly executes the AST. This is invaluable for rapid prototyping and debugging. The Interpreter simulates the hardware environment, managing a virtual symbol table for variables and a `hardware_state` dictionary for pin values, servo positions, and serial output. This allows programmers to test their logic without needing to physically flash code to a microcontroller, a significant advantage for iterative development.

PDSX is more than just a language; it is a complete ecosystem designed to make embedded systems programming accessible and enjoyable. By offering a high-level syntax with direct hardware control and a flexible transpiler/interpreter pipeline, it empowers creators to bring their ideas to life, from blinking an LED to controlling complex robotic systems.
