/*
 * Functions related to power system
 */

Adafruit_ADS1015 adc(0x48);

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
