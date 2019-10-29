//Includes
#include "config.h"
#include <TimeLib.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_ADS1015.h>
#include <Adafruit_BNO055.h>

#include "SSD1306Ascii.h"
#include "SSD1306AsciiWire.h"
#include "LowPower.h"

//Defines
//#define DEBUG_ALL
#define DEBUG_STARTUP
#define DEBUG_MAIN_LOGGING
//#define DEBUG_ENVIRONMENT
//#define DEBUG_READ_BATTERY
//#define DEBUG_READ_MOTOR
#define DEBUG_IMU

#define SEALEVELPRESSURE_HPA 1013.25
#define BME_ADDRESS 0x76
#define OLED_ADDRESS 0x3C
#define OLED_RST_PIN -1

//Global Variables
bool logging_enabled = true;
unsigned long coulomb_counter;
unsigned long last_debounce_time;

//Define Sensors
Adafruit_BME280 internal_env;
Adafruit_ADS1015 adc(0x48);
Adafruit_BNO055 bno = Adafruit_BNO055(55);
SSD1306AsciiWire oled;

void setup() {
  int display;
  #if defined (DEBUG_STARTUP) || defined (DEBUG_ALL)
    Serial.begin(115200);
    Serial.println("Startup...");
  #endif
  
  pinMode(2, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(2), button_pressed, FALLING);
  //bool status;

  //status = internal_env.begin();
  if (!internal_env.begin(BME_ADDRESS)) {
    #if defined (DEBUG_STARTUP) || defined (DEBUG_ALL)
      Serial.println("Could not find a valid BME280 sensor, check wiring!");
    #endif
  }
  internal_env.setSampling(Adafruit_BME280::MODE_SLEEP);

  adc.setGain(GAIN_TWOTHIRDS);
  adc.begin();

  if (!bno.begin()) {
    #if defined (DEBUG_STARTUP) || defined (DEBUG_ALL)
      Serial.println("Could not find a valid BNO055 sensor, check wiring!");
    #endif
  } else {
    bno.setMode(Adafruit_BNO055::OPERATION_MODE_CONFIG);
    bno.setAxisRemap(0x06);  //Swap default x and z axis
    bno.setAxisSign(0x01);   //invert y and z directions
    bno.setMode(Adafruit_BNO055::OPERATION_MODE_NDOF);
  }

  #if OLED_RST_PIN >= 0
    oled.begin(&Adafruit128x64, OLED_ADDRESS, OLED_RST_PIN);
  #else // OLED_RST_PIN >= 0
    oled.begin(&Adafruit128x64, OLED_ADDRESS);
  #endif // OLED_RST_PIN >= 0

  oled.setFont(Adafruit5x7);
  oled.clear();
  oled.println("Gavin DPV v2.0");
  oled.println();
  oled.set2X();
  oled.println("ONLINE");
  
  coulomb_counter = 0;
}

void loop() {
  char main_data[54];
  String battery_data = "";
  bool header;
  unsigned long internal_temperature, internal_pressure, internal_humidity;
  unsigned long external_temperature, external_pressure;
  unsigned long mV1, mV2, mAmps, mWatts, mAmps_max;
  uint8_t percent_charge;
  int16_t quat_w, quat_x, quat_y, quat_z, accel_x, accel_y, accel_z;
  uint8_t heading;
  imu::Quaternion quat;

  mAmps_max = 0;

  //Get initial battery state
  read_battery(mV1, mV2, percent_charge);
  if (percent_charge == 100) {
    coulomb_counter = BATTERY_AMPHR * 1000;
  }
  else if (percent_charge == 0) {
    coulomb_counter = 0;
  }
  
  while(1) {
    while(logging_enabled == true) {
      read_env(internal_temperature, internal_pressure, internal_humidity, external_temperature, external_pressure);
      read_battery(mV1, mV2, percent_charge);
      read_motor(mAmps);
      read_position(quat_w, quat_x, quat_y, quat_z, accel_x, accel_y, accel_z, heading);
      mWatts = mAmps * (mV1 + mV2);
      if (mAmps > mAmps_max) {
        mAmps_max = mAmps;
      }

      //sprintf(main_data, "%d,%d %d %d %d %d %d %d %d ", now(), heading, quat_w, quat_x, quat_y, quat_z,
      //        accel_x, accel_y, accel_z);
      sprintf(main_data, "%d,%u ", now(), heading);
      
      #if defined (DEBUG_MAIN_LOGGING) || defined (DEBUG_ALL)
        Serial.println("loop(logging_enabled == true)");
        Serial.print("Env/Pos Data: "); Serial.print(main_data);
        Serial.print(internal_temperature); Serial.print(","); Serial.print(internal_pressure); Serial.print(","); Serial.print(internal_humidity); Serial.print(",");
        Serial.print(external_temperature); Serial.print(","); Serial.print(external_pressure); Serial.print(",");
        Serial.print("ERT,"); Serial.println(DPV_UUID);
        Serial.print("Battery Data: "); Serial.print(now()); Serial.print(",");
        Serial.print(mV1 + mV2), Serial.print(","); Serial.print(mV1); Serial.print(","); Serial.print(mV2); Serial.print(",");
        Serial.print(mWatts); Serial.print(","); Serial.print(mAmps); Serial.print(","); Serial.print(mAmps_max); Serial.print(","); Serial.print(coulomb_counter); Serial.print(",");
        Serial.print(percent_charge); Serial.print(","); Serial.print("ERT,"), Serial.println(BATTERY_UUID);
        Serial.println();
      #endif
      delay(LOG_INTERVAL * 1000);
    }

    
  }
}

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

void read_battery(unsigned long& battery1, unsigned long& battery2, uint8_t& percent_charge) {
  battery1 = adc.readADC_SingleEnded(1) * (unsigned long)ADC_ERROR;
  battery2 = adc.readADC_SingleEnded(2) * (unsigned long)ADC_ERROR;

  #if defined (DEBUG_READ_BATTERY) || defined (DEBUG_ALL)
    Serial.println("read_battery()");
    Serial.print("ADC Input1: "); Serial.print(battery1); Serial.print(" Battery1 Voltage: "); Serial.println(((battery1 * ADC_OFFSET) * ADC_V_DIVIDER_1) / 100000);
    Serial.print("ADC Input2: "); Serial.print(battery2); Serial.print(" Battery2 Voltage: "); Serial.println(((battery2 * ADC_OFFSET) * ADC_V_DIVIDER_2) / 100000);
    Serial.println();
  #endif

  battery1 = ((battery1 * ADC_OFFSET) * ADC_V_DIVIDER_1) / 100000;
  battery2 = ((battery2 * ADC_OFFSET) * ADC_V_DIVIDER_2) / 100000;

  if (battery1 <= BATTERY_MIN_VOLTAGE * BATTERY_MODULES) {
    percent_charge = 0;
  }
  else if (battery1 >= BATTERY_MAX_VOLTAGE * BATTERY_MODULES) {
    percent_charge = 100;
  }
  else {
    percent_charge = (battery1 - (BATTERY_MIN_VOLTAGE * BATTERY_MODULES)) * 100 / ((BATTERY_MAX_VOLTAGE * BATTERY_MODULES) - (BATTERY_MIN_VOLTAGE * BATTERY_MODULES));
  }
  battery1 = battery1 - battery2;
}

void read_motor(unsigned long& mAmps) {
  mAmps = adc.readADC_SingleEnded(3) * (unsigned long)ADC_ERROR;

  #if defined (DEBUG_READ_MOTOR) || defined (DEBUG_ALL)
    Serial.println("read_motor()");
    Serial.print("ADC Input3: "); Serial.print(mAmps); Serial.print(" milliAmps: "); Serial.println(((mAmps * ADC_OFFSET) - ACS_OFFSET) / ACS_MVPERAMP * 10);
    Serial.println();
  #endif

  mAmps = ((mAmps * ADC_OFFSET) - ACS_OFFSET) / ACS_MVPERAMP * 10;
  coulomb_counter = coulomb_counter - (mAmps / 3600);
}

void read_position(int16_t& quat_w, int16_t& quat_x, int16_t& quat_y, int16_t& quat_z, int16_t& accel_x, int16_t& accel_y, int16_t& accel_z, uint8_t& heading) {
  uint8_t system, gyro, acceleration , mag = 0;
  imu::Quaternion quat;
  imu::Vector<3> accel;
  imu::Vector<3> euler;
  bno.getCalibration(&system, &gyro, &acceleration, &mag);

  if (system > 0) {
    quat = bno.getQuat();
    accel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
    euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);

    heading = uint8_t(euler.x());
    
    quat_w = quat.w() * 10000;
    quat_x = quat.x() * 10000;
    quat_y = quat.y() * 10000;
    quat_z = quat.z() * 10000;
    
    accel_x = accel.x() * 10000;
    accel_y = accel.y() * 10000;
    accel_z = accel.z() * 10000;

    #if defined (DEBUG_IMU) || defined (DEBUG_ALL)
      Serial.print("Heading: ");
      Serial.print(heading);
      Serial.println("\t\t");
    
      Serial.print("qW: ");
      Serial.print(quat_w);
      Serial.print(" qX: ");
      Serial.print(quat_x);
      Serial.print(" qY: ");
      Serial.print(quat_y);
      Serial.print(" qZ: ");
      Serial.print(quat_z);
      Serial.println("\t\t");

      Serial.print("X: ");
      Serial.print(accel_x);
      Serial.print(" Y: ");
      Serial.print(accel_y);
      Serial.print(" Z: ");
      Serial.print(accel_z);
      Serial.println("\t\t");
    #endif
    
  } else {
    oled.clear();
    oled.set2X();
    oled.println(" ATTENTION");
    oled.set1X();
    oled.println("IMU Not Calibrated");
    oled.println("Not logging position");
  }
}

void button_pressed(){
  int button_state = digitalRead(2);
  int button_timer = 0;
  unsigned long current_time = millis();

  if (logging_enabled == true) {
    if (button_state == LOW && (current_time - last_debounce_time > 200)) {
      logging_enabled = false;
      Serial.println("Button Pressed: Stop logging");
    }
  }
  else {
    while(digitalRead(2) == LOW) {
      delay(1);
      button_timer++;
    }
    if (button_timer > 2000){
      Serial.println("Button Pressed: Long");
    }
    else if (button_timer > 200) {
      Serial.println("Button Pressed: Short");
    }
  }
  last_debounce_time = current_time;
}
