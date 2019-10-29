/*
 * Functions related to environment data
 */

void read_env(unsigned long& internal_temperature, unsigned long& internal_pressure, unsigned long& internal_humidity, unsigned long& external_temperature, unsigned long& external_pressure) {
  internal_env.setSampling(Adafruit_BME280::MODE_NORMAL);
  internal_temperature = internal_env.readTemperature() * 100;  //convert to integer, units in c
  internal_pressure = internal_env.readPressure() * 100 ;       //convert to integer, units in mBar
  internal_humidity = internal_env.readHumidity() * 1000;       //convert to integer, percentage
  external_temperature = 0;
  external_pressure = 0;
  internal_env.setSampling(Adafruit_BME280::MODE_SLEEP);
  
  #ifdef UNITS == imperial
    internal_temperature = (internal_temperature * 18) + 32000;
  #endif

  #if defined (DEBUG_ENVIRONMENT) || defined (DEBUG_ALL)
    Serial.println("read_env()");
    Serial.print("Internal Temperature = "); Serial.println(internal_temperature);
    Serial.print("Internal Pressure: "); Serial.println(internal_pressure);
    Serial.print("Internal Humidity: "); Serial.println(internal_humidity);
    Serial.print("External Temperature: "); Serial.println(external_temperature);
    Serial.print("External Pressure: "); Serial.println(external_pressure);
    Serial.println();
  #endif
}
