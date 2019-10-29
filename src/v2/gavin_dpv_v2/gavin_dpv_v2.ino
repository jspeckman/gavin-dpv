//Includes
#include "config.h"
#include <TimeLib.h>

#include "LowPower.h"

#include "ui.h"
#include "environment.h"
#include "power.h"

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
