#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Servo.h>

// ── Pines
#define TRIG    4
#define ECHO    5
#define SERVO   6
#define BUZZER  8
#define RGB_R   9
#define RGB_G   10
#define RGB_B   11
#define SONIDO  A0
#define LLAMA   A1

// ── OLED
#define SCREEN_W 128
#define SCREEN_H  64
Adafruit_SSD1306 oled(SCREEN_W, SCREEN_H, &Wire, -1);

Servo barrera;

bool plazaOcupada = false;
bool incendio = false;
unsigned long ultimaLectura = 0;

void setRGB(int r, int g, int b) {
  analogWrite(RGB_R, r);
  analogWrite(RGB_G, g);
  analogWrite(RGB_B, b);
}

void actualizarOLED(float distancia, bool ocupada, int sonido, bool fuego) {
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SSD1306_WHITE);

  oled.setCursor(0, 0);
  oled.println("=PARQUEO INTELIGENTE=");

  oled.setCursor(0, 12);
  oled.print("Dist: ");
  oled.print(distancia, 1);
  oled.println(" cm");

  oled.setCursor(0, 22);
  oled.print("Ruido: ");
  oled.println(sonido);

  oled.setCursor(0, 32);
  oled.setTextSize(2);
  if (fuego) {
    oled.println("INCENDIO!");
  } else if (ocupada) {
    oled.println("OCUPADO");
  } else {
    oled.println("LIBRE");
  }
  oled.display();
}

float medirDistancia() {
  float suma = 0;
  for (int i = 0; i < 5; i++) {
    digitalWrite(TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG, LOW);
    long duracion = pulseIn(ECHO, HIGH);
    suma += duracion * 0.034 / 2;
    delay(10);
  }
  return suma / 5;
}

// ── Promedio de 5 lecturas para evitar falsas alarmas
int medirLlama() {
  int suma = 0;
  for (int i = 0; i < 5; i++) {
    suma += analogRead(LLAMA);
    delay(5);
  }
  return suma / 5;
}

void sonarBuzzer() {
  tone(BUZZER, 1000);
  delay(200);
  noTone(BUZZER);
  delay(100);
  tone(BUZZER, 1000);
  delay(200);
  noTone(BUZZER);
  delay(100);
  tone(BUZZER, 1000);
  delay(200);
  noTone(BUZZER);
}

void alarmaIncendio() {
  for (int i = 0; i < 6; i++) {
    tone(BUZZER, 2000);
    delay(100);
    noTone(BUZZER);
    delay(100);
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(RGB_R, OUTPUT);
  pinMode(RGB_G, OUTPUT);
  pinMode(RGB_B, OUTPUT);
  pinMode(SONIDO, INPUT);
  pinMode(LLAMA, INPUT);

  barrera.attach(SERVO);
  barrera.write(90);

  if (!oled.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("ERROR:OLED");
    while (true);
  }

  setRGB(0, 255, 0);
  actualizarOLED(0, false, 0, false);
  Serial.println("LISTO");
}

void loop() {
  // ── Leer flame sensor con promedio (prioridad maxima)
  int valorLlama = medirLlama();
  bool hayFuego = valorLlama < 1000; // umbral estricto

  if (hayFuego && !incendio) {
    incendio = true;
    barrera.write(90);        // abrir para evacuar
    setRGB(255, 0, 0);
    Serial.println("INCENDIO");
    actualizarOLED(0, plazaOcupada, 0, true);

  } else if (!hayFuego && incendio) {
    incendio = false;
    Serial.println("INCENDIO_OFF");
    setRGB(plazaOcupada ? 255 : 0, plazaOcupada ? 0 : 255, 0);
  }

  // Si hay incendio sonar alarma y no hacer nada mas
  if (incendio) {
    alarmaIncendio();
    return;
  }

  // ── Leer sensores cada 1 segundo
  if (millis() - ultimaLectura >= 1000) {
    ultimaLectura = millis();

    float distancia = medirDistancia();
    int sonido = analogRead(SONIDO);
    bool hayAuto = distancia < 30.0;

    if (hayAuto && !plazaOcupada) {
      plazaOcupada = true;
      barrera.write(0);
      setRGB(255, 0, 0);
      sonarBuzzer();
      Serial.println("OCUPADO");

    } else if (!hayAuto && plazaOcupada) {
      plazaOcupada = false;
      barrera.write(90);
      setRGB(0, 255, 0);
      Serial.println("LIBRE");
    }

    // Formato: DATOS,distancia,sonido,llama,estado
    Serial.print("DATOS,");
    Serial.print(distancia, 1);
    Serial.print(",");
    Serial.print(sonido);
    Serial.print(",");
    Serial.print(valorLlama);
    Serial.print(",");
    Serial.println(plazaOcupada ? "OCUPADO" : "LIBRE");

    actualizarOLED(distancia, plazaOcupada, sonido, false);
  }

  if (Serial.available() > 0) {
    String orden = Serial.readStringUntil('\n');
    orden.trim();
    if (orden == "PING") {
      Serial.println("PONG");
    } else if (orden == "ESTADO?") {
      Serial.println(plazaOcupada ? "OCUPADO" : "LIBRE");
    }
  }
}