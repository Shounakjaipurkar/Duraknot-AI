#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// =====================================================
// ROTARY ENCODER
// =====================================================

#define ENCODER_PIN 25

// Calibration:
// 600 pulses = 34 cm
const float PULSES_PER_REV = 600.0;
const float DISTANCE_PER_REV_CM = 34.0;

const float CM_PER_PULSE =
  DISTANCE_PER_REV_CM / PULSES_PER_REV;

volatile unsigned long pulseCount = 0;


// =====================================================
// SERVO
// =====================================================

#define SERVO_PIN 13

Servo servo;

float requiredLengthCm = 0.0;
bool servoTriggered = false;


// =====================================================
// LCD
// =====================================================

#define LCD_ADDRESS 0x27

LiquidCrystal_I2C lcd(LCD_ADDRESS, 16, 2);


// =====================================================
// WIFI
// =====================================================

const char* WIFI_SSID = "ROG13";
const char* WIFI_PASSWORD = "99234423";


// =====================================================
// FLASK SERVER
// =====================================================

const char* SERVER_URL =
  "http://192.168.137.1:5000/update_production";


// =====================================================
// ENCODER INTERRUPT
// =====================================================

void IRAM_ATTR encoderPulse()
{
  pulseCount++;
}


// =====================================================
// SETUP
// =====================================================

void setup()
{
  Serial.begin(115200);

  // ===================================================
  // ROTARY ENCODER
  // ===================================================

  pinMode(ENCODER_PIN, INPUT);

  attachInterrupt(
    digitalPinToInterrupt(ENCODER_PIN),
    encoderPulse,
    FALLING
  );


  // ===================================================
  // SERVO
  // ===================================================

  servo.attach(SERVO_PIN);

  // Initial position
  servo.write(0);


  // ===================================================
  // LCD
  // ===================================================

  Wire.begin(21, 22);

  lcd.init();
  lcd.backlight();

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("DuraKnot");

  lcd.setCursor(0, 1);
  lcd.print("Starting...");

  delay(2000);


  // ===================================================
  // SERIAL INFORMATION
  // ===================================================

  Serial.println();
  Serial.println("--------------------------------");
  Serial.println("DuraKnot Length Counter");
  Serial.println("--------------------------------");

  Serial.print("Encoder GPIO: ");
  Serial.println(ENCODER_PIN);

  Serial.print("Pulses per revolution: ");
  Serial.println(PULSES_PER_REV);

  Serial.print("Distance per revolution: ");
  Serial.print(DISTANCE_PER_REV_CM);
  Serial.println(" cm");

  Serial.print("Distance per pulse: ");
  Serial.print(CM_PER_PULSE, 5);
  Serial.println(" cm");


  // ===================================================
  // WIFI
  // ===================================================

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  Serial.println("WiFi Connected!");

  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());

  Serial.println();
  Serial.println("Rotary Encoder Ready");
  Serial.println("Servo Ready");
  Serial.println("--------------------------------");
}


// =====================================================
// SEND DATA TO FLASK
// =====================================================

bool sendProductionData()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("WiFi disconnected");
    return false;
  }


  HTTPClient http;

  http.begin(SERVER_URL);

  http.addHeader(
    "Content-Type",
    "application/json"
  );


  // ===================================================
  // GET CURRENT PULSE COUNT
  // ===================================================

  noInterrupts();

  unsigned long currentPulseCount =
    pulseCount;

  interrupts();


  // ===================================================
  // CALCULATE LENGTH
  // ===================================================

  float lengthCm =
    currentPulseCount * CM_PER_PULSE;

  float lengthMeters =
    lengthCm / 100.0;


  // ===================================================
  // CREATE JSON
  // ===================================================

  String jsonData = "{";

  jsonData += "\"pulse_count\":";
  jsonData += String(currentPulseCount);

  jsonData += ",";

  jsonData += "\"length_cm\":";
  jsonData += String(lengthCm, 2);

  jsonData += ",";

  jsonData += "\"length_m\":";
  jsonData += String(lengthMeters, 3);

  jsonData += "}";


  // ===================================================
  // SERIAL
  // ===================================================

  Serial.println();
  Serial.println("Sending data to server:");
  Serial.println(jsonData);


  // ===================================================
  // SEND POST REQUEST
  // ===================================================

  int responseCode =
    http.POST(jsonData);

  Serial.print("HTTP Response: ");
  Serial.println(responseCode);


  // ===================================================
  // SERVER RESPONSE
  // ===================================================

  if (responseCode == 200)
  {
    String response =
      http.getString();

    Serial.print("Server Response: ");
    Serial.println(response);


    // =================================================
    // PARSE JSON
    // =================================================

    JsonDocument doc;

    DeserializationError error =
      deserializeJson(doc, response);


    if (!error)
    {

      // ===============================================
      // GET REQUIRED LENGTH
      // ===============================================

      if (doc.containsKey("required_length_cm"))
      {
        requiredLengthCm =
          doc["required_length_cm"];

        Serial.print("Required Length: ");
        Serial.print(requiredLengthCm);
        Serial.println(" cm");
      }


      // ===============================================
      // CHECK RESET
      // ===============================================

      bool resetRoll =
        doc["reset"];


      if (resetRoll == true)
      {
        lcd.clear();

        lcd.setCursor(0, 0);
        lcd.print("ROLL COMPLETED");

        lcd.setCursor(0, 1);
        lcd.print("Starting new...");

        Serial.println("ROLL COMPLETED");
        Serial.println("Starting new roll...");

        delay(2000);


        // =============================================
        // RESET ENCODER
        // =============================================

        noInterrupts();

        pulseCount = 0;

        interrupts();


        // Reset servo trigger
        servoTriggered = false;


        Serial.println("Pulse: 0");
        Serial.println("Length: 0 cm");
      }
    }
    else
    {
      Serial.println("JSON parsing failed!");
    }
  }


  http.end();

  return responseCode == 200;
}


// =====================================================
// MAIN LOOP
// =====================================================

void loop()
{

  // ===================================================
  // GET CURRENT PULSE COUNT
  // ===================================================

  unsigned long currentPulses;

  noInterrupts();

  currentPulses =
    pulseCount;

  interrupts();


  // ===================================================
  // CALCULATE FENCE LENGTH
  // ===================================================

  float lengthCm =
    currentPulses * CM_PER_PULSE;

  float lengthMeters =
    lengthCm / 100.0;


  // ===================================================
  // UPDATE LCD
  // ===================================================

  lcd.clear();

  lcd.setCursor(0, 0);

  lcd.print("Req:");

  if (requiredLengthCm > 0)
  {
    lcd.print(requiredLengthCm, 0);
    lcd.print("cm");
  }
  else
  {
    lcd.print("--");
  }


  lcd.setCursor(0, 1);

  lcd.print("Cur:");
  lcd.print(lengthCm, 1);
  lcd.print("cm");


  // ===================================================
  // SERIAL MONITOR
  // ===================================================

  static unsigned long lastDisplayedPulse = 0;

  if (currentPulses != lastDisplayedPulse)
  {
    Serial.println();

    Serial.print("Pulse: ");
    Serial.print(currentPulses);

    Serial.print(" | Length: ");
    Serial.print(lengthCm, 2);

    Serial.print(" cm | ");

    Serial.print(lengthMeters, 3);

    Serial.println(" m");

    lastDisplayedPulse =
      currentPulses;
  }


  // ===================================================
  // CHECK REQUIRED LENGTH
  // ===================================================

  if (
    requiredLengthCm > 0 &&
    lengthCm >= requiredLengthCm &&
    !servoTriggered
  )
  {
    Serial.println();
    Serial.println("================================");
    Serial.println("REQUIRED LENGTH REACHED");
    Serial.println("Activating servo...");
    Serial.println("================================");


    // Prevent another trigger
    servoTriggered = true;


    // =================================================
    // SERVO 0 -> 90
    // =================================================

    servo.write(0);

    Serial.println("Servo: 0 -> 90");

    delay(500);


    // =================================================
    // SERVO 90 -> 0
    // =================================================

    servo.write(0);

    Serial.println("Servo: 90 -> 0");

    Serial.println("Servo cycle completed");
  }


  // ===================================================
  // SEND DATA TO FLASK
  // ===================================================

  static unsigned long lastSendTime = 0;

  if (millis() - lastSendTime >= 1000)
  {
    sendProductionData();

    lastSendTime = millis();
  }


  // ===================================================
  // SMALL DELAY
  // ===================================================

  delay(50);
}