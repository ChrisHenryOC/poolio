/**
 * Pool Node - Battery-powered pool sensor
 *
 * Sensors:
 *   - DS18X20 temperature sensor (OneWire)
 *   - Float switch for water level
 *   - LC709203F battery gauge (I2C)
 *
 * Operation:
 *   1. Wake from deep sleep
 *   2. Read sensors
 *   3. Publish status to Adafruit IO
 *   4. Return to deep sleep
 */

#include <Arduino.h>

#ifndef ENVIRONMENT
#define ENVIRONMENT "unknown"
#endif

#ifndef FEED_PREFIX
#define FEED_PREFIX ""
#endif

#ifndef DEBUG_LOGGING
#define DEBUG_LOGGING 0
#endif

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("=================================");
    Serial.println("Pool Node Starting");
    Serial.print("Environment: ");
    Serial.println(ENVIRONMENT);
    Serial.print("Feed prefix: ");
    Serial.println(FEED_PREFIX);
#if DEBUG_LOGGING
    Serial.println("Debug logging: enabled");
#else
    Serial.println("Debug logging: disabled");
#endif
    Serial.println("=================================");
}

void loop() {
    // Main loop will be replaced with deep sleep cycle
    delay(10000);
}
