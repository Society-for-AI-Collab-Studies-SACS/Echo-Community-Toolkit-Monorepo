// Minimal stub for Adafruit OPT3001 to allow CI builds without registry/library resolution
#ifndef ADAFRUIT_OPT3001_H
#define ADAFRUIT_OPT3001_H

#include <Arduino.h>
#include <Adafruit_Sensor.h>

class Adafruit_OPT3001 {
 public:
  bool begin() { return true; }
  bool getEvent(sensors_event_t* event) {
    if (!event) return false;
    memset(event, 0, sizeof(sensors_event_t));
    event->light = 0.0F;
    return true;
  }
};

#endif // ADAFRUIT_OPT3001_H

