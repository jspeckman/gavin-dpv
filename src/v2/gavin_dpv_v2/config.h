/*
  Config Params

  
*/

//Debugging
//#define DEBUG_ALL
#define DEBUG_STARTUP
#define DEBUG_MAIN_LOGGING
//#define DEBUG_ENVIRONMENT
//#define DEBUG_READ_BATTERY
//#define DEBUG_READ_MOTOR
#define DEBUG_IMU

//General
#define DPV_UUID "gue-1845"
#define UNITS imperial                //Comment out for metric
#define LOG_INTERVAL 1                //Seconds
#define SEALEVELPRESSURE_HPA 101325   //1013.25 x 100

//ADC Tuning
#define ADC_OFFSET 3              //3mV for ADS1015, .1875mV for ADS1115
#define ADC_SCALING               //Enable or disable voltage scaling in the ADS1x15
#define ADC_ERROR 107             //ADC Calibration factor.  (1.07) x 100
#define ADC_V_DIVIDER_1 5545      //Voltage divider value.  (5.545) x 1000
#define ADC_V_DIVIDER_2 5000      //Voltage divider value.  (5) x 1000

//ACS7xx Tuning
#define ACS_MVPERAMP 40           //ACS7xx Offset in mV per Amp
#define ACS_OFFSET 250000         //ACS7xx directional offset.  (2500) x 100

//Motor Properties
#define MOTOR_WATTS 500           //Gavin motor per Tahoe benchmark

//Battery Properties (Update when installing new batteries)
#define BATTERY_UUID "gue-2135"
#define BATTERY_MFG
#define BATTERY_MODEL
#define BATTERY_WEIGHT
#define BATTERY_MODULES 2         //Number of batteries
#define BATTERY_CHEMISTRY SLA     //Type of battery
#define BATTERY_VOLTAGE 12        //Rated voltage
#define BATTERY_AMPHR 35          //Rated or calibrated Amp Hours
#define BATTERY_MIN_VOLTAGE 10000 //mVoltage to declare 0% or empty (10) x 1000
#define BATTERY_MAX_VOLTAGE 13100 //mVoltage to declare 100% or full (13.1) x 1000

//IMU

//Global Variables
bool logging_enabled = true;      //Track state of logging
unsigned long coulomb_counter;    //Track coulombs in/out
unsigned long last_debounce_time; //Button debouncing
