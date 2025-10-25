#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <ArduinoJson.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_LIS3MDL.h>
#include <Adafruit_OPT3001.h>
#include "version_auto.h"

/*
 RHZ Stylus (Maker) - ESP32-S3 Firmware Skeleton
 - ADS1220 (24-bit ADC) over SPI at ~1 kS/s
 - AD7746 (CDC) over I2C at ~100 S/s
 - LIS3MDL magnetometer, OPT3001 lux
 - DRV8833 coil driver (PWM vector)
 - microSD CSV logging per second + USB JSON snapshot
 - Zipper protocol: 6x30s stages
*/

#define PIN_SD_CS         5
#define PIN_ADS1220_CS    10
#define PIN_ADS1220_DRDY  9
#define PIN_COIL_IN1      6
#define PIN_COIL_IN2      7
#define PIN_LED           13
#define PIN_PPS_IN        2
#define PIN_TRIG_OUT      3

#define ADS1220_RESET     0x06
#define ADS1220_START     0x08
#define ADS1220_RDATA     0x10
#define ADS1220_RREG      0x20
#define ADS1220_WREG      0x40

Adafruit_LIS3MDL lis3mdl;
Adafruit_OPT3001 opt3001;

File logFile;
uint32_t lastLogMs = 0;

struct Stage {
  const char* name;
  float freqHz;
};
Stage zipper[6] = {
  {"S1", 222.0}, {"S2", 333.0}, {"S3", 444.0},
  {"S4", 555.0}, {"S5", 666.0}, {"S6", 777.0}
};
const uint32_t STAGE_MS = 30000;
uint32_t stageStartMs = 0;
int currentStage = 0;

bool inEmitWindow(uint32_t nowMs) {
  uint32_t stageElapsed = nowMs - stageStartMs;
  return stageElapsed > (STAGE_MS - 10000);
}

void ads1220WriteReg(uint8_t addr, uint8_t val) {
  digitalWrite(PIN_ADS1220_CS, LOW);
  SPI.transfer(ADS1220_WREG | (addr & 0x03));
  SPI.transfer(0x00);
  SPI.transfer(val);
  digitalWrite(PIN_ADS1220_CS, HIGH);
}

uint8_t ads1220ReadReg(uint8_t addr) {
  uint8_t val;
  digitalWrite(PIN_ADS1220_CS, LOW);
  SPI.transfer(ADS1220_RREG | (addr & 0x03));
  SPI.transfer(0x00);
  val = SPI.transfer(0x00);
  digitalWrite(PIN_ADS1220_CS, HIGH);
  return val;
}

void ads1220Command(uint8_t cmd) {
  digitalWrite(PIN_ADS1220_CS, LOW);
  SPI.transfer(cmd);
  digitalWrite(PIN_ADS1220_CS, HIGH);
}

bool ads1220DataReady() {
  return digitalRead(PIN_ADS1220_DRDY) == LOW;
}

int32_t ads1220ReadRaw() {
  digitalWrite(PIN_ADS1220_CS, LOW);
  SPI.transfer(ADS1220_RDATA);
  int32_t b1 = SPI.transfer(0x00);
  int32_t b2 = SPI.transfer(0x00);
  int32_t b3 = SPI.transfer(0x00);
  digitalWrite(PIN_ADS1220_CS, HIGH);
  int32_t raw = (b1 << 16) | (b2 << 8) | b3;
  if (raw & 0x800000) raw |= 0xFF000000;
  return raw;
}

void ads1220Init() {
  pinMode(PIN_ADS1220_CS, OUTPUT);
  pinMode(PIN_ADS1220_DRDY, INPUT_PULLUP);
  digitalWrite(PIN_ADS1220_CS, HIGH);
  delay(5);
  ads1220Command(ADS1220_RESET);
  delay(5);
  ads1220WriteReg(0x00, 0x01);
  ads1220WriteReg(0x01, 0x10);
  ads1220WriteReg(0x02, 0x00);
  ads1220WriteReg(0x03, 0x00);
  ads1220Command(ADS1220_START);
}

#define AD7746_ADDR 0x48
bool ad7746Init() {
  return true;
}

bool ad7746ReadCapRaw(uint16_t &capRaw) {
  Wire.beginTransmission(AD7746_ADDR);
  Wire.write(0x00);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(AD7746_ADDR, 3) != 3) return false;
  uint8_t msb = Wire.read();
  uint8_t mid = Wire.read();
  uint8_t lsb = Wire.read();
  capRaw = (msb << 8) | mid;
  (void)lsb;
  return true;
}

void coilSet(float duty) {
  duty = constrain(duty, 0.0f, 1.0f);
  int v = static_cast<int>(255.0f * duty);
  ledcWrite(0, v);
  ledcWrite(1, 0);
}

void emitControl(uint32_t nowMs) {
  if (inEmitWindow(nowMs)) {
    coilSet(0.10f);
  } else {
    coilSet(0.0f);
  }
}

String csvHeader() {
  return F("t_ms,stage,emit,ads1220_raw,cap_raw,lux,mag_x,mag_y,mag_z");
}

void openLog() {
  if (!SD.begin(PIN_SD_CS)) {
    Serial.println(F("{\"log\":\"sd_init_failed\"}"));
    return;
  }
  char fname[64];
  snprintf(fname, sizeof(fname), "/rhz_%lu.csv", static_cast<unsigned long>(millis()));
  logFile = SD.open(fname, FILE_WRITE);
  if (logFile) {
    logFile.println(csvHeader());
    logFile.flush();
    Serial.print(F("{\"log_file\":\""));
    Serial.print(fname);
    Serial.println(F("\"}"));
  } else {
    Serial.println(F("{\"log\":\"open_failed\"}"));
  }
}

void setup() {
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  pinMode(PIN_PPS_IN, INPUT_PULLUP);
  pinMode(PIN_TRIG_OUT, OUTPUT);
  digitalWrite(PIN_TRIG_OUT, LOW);

  Serial.begin(115200);
  delay(1000);
  #ifndef RHZZ_VERSION_STR
  #define RHZZ_VERSION_STR "dev"
  #endif
  Serial.print(F("{\"boot\":\"rhz_stylus_maker\",\"ver\":\""));
  Serial.print(RHZZ_VERSION_STR);
  Serial.println(F("\"}"));
  // Version printed above is injected by CI via RHZZ_VERSION_STR or defaults to "dev".

  Wire.begin();
  SPI.begin();

  ledcSetup(0, 2000, 8);
  ledcAttachPin(PIN_COIL_IN1, 0);
  ledcSetup(1, 2000, 8);
  ledcAttachPin(PIN_COIL_IN2, 1);
  coilSet(0.0f);

  if (!lis3mdl.begin_I2C()) {
    Serial.println(F("{\"lis3mdl\":\"init_fail\"}"));
  }
  if (!opt3001.begin()) {
    Serial.println(F("{\"opt3001\":\"init_fail\"}"));
  }

  lis3mdl.setPerformanceMode(LIS3MDL_MEDIUMMODE);
  lis3mdl.setDataRate(LIS3MDL_DATARATE_1000_HZ);
  lis3mdl.setRange(LIS3MDL_RANGE_4_GAUSS);

  ads1220Init();
  ad7746Init();
  openLog();
  stageStartMs = millis();
  currentStage = 0;
}

void loop() {
  uint32_t now = millis();

  if (now - stageStartMs >= STAGE_MS) {
    stageStartMs += STAGE_MS;
    currentStage = (currentStage + 1) % 6;
    digitalWrite(PIN_LED, HIGH);
    digitalWrite(PIN_TRIG_OUT, HIGH);
    delay(50);
    digitalWrite(PIN_LED, LOW);
    digitalWrite(PIN_TRIG_OUT, LOW);
  }

  emitControl(now);

  int32_t adsRaw = INT32_MIN;
  if (ads1220DataReady()) {
    adsRaw = ads1220ReadRaw();
  }

  static uint32_t lastCap = 0;
  uint16_t capRaw = 0;
  if (now - lastCap > 10) {
    (void)ad7746ReadCapRaw(capRaw);
    lastCap = now;
  }

  float lux = NAN;
  static uint32_t lastLux = 0;
  if (now - lastLux > 50) {
    sensors_event_t ev;
    if (opt3001.getEvent(&ev)) {
      lux = ev.light;
    }
    lastLux = now;
  }

  sensors_event_t mag;
  float mx = NAN;
  float my = NAN;
  float mz = NAN;
  if (lis3mdl.getEvent(&mag)) {
    mx = mag.magnetic.x;
    my = mag.magnetic.y;
    mz = mag.magnetic.z;
  }

  if (now - lastLogMs >= 1000) {
    lastLogMs = now;
    bool emit = inEmitWindow(now);

    if (logFile) {
      logFile.print(now); logFile.print(",");
      logFile.print(zipper[currentStage].name); logFile.print(",");
      logFile.print(emit ? 1 : 0); logFile.print(",");
      logFile.print(adsRaw); logFile.print(",");
      logFile.print(capRaw); logFile.print(",");
      logFile.print(isnan(lux) ? -1 : lux); logFile.print(",");
      logFile.print(isnan(mx) ? -1 : mx); logFile.print(",");
      logFile.print(isnan(my) ? -1 : my); logFile.print(",");
      logFile.println(isnan(mz) ? -1 : mz);
      logFile.flush();
    }

    StaticJsonDocument<256> doc;
    doc["t_ms"] = now;
    doc["stage"] = zipper[currentStage].name;
    doc["emit"] = emit;
    doc["tx"]["f"] = zipper[currentStage].freqHz;
    doc["rx"]["ads_raw"] = adsRaw;
    doc["cap_raw"] = capRaw;
    doc["lux"] = lux;
    JsonArray m = doc.createNestedArray("mag_uT");
    m.add(mx);
    m.add(my);
    m.add(mz);
    serializeJson(doc, Serial);
    Serial.println();
  }
}

// Notes:
// - Tune ADS1220 registers and INA gain to match hardware characteristics.
// - Expand AD7746 configuration to program excitation and convert to femtofarads.
// - Implement full coil drive safety with current sensing before field use.
// - Align PPS and trigger I/O with external DAQ by timestamping transitions.
