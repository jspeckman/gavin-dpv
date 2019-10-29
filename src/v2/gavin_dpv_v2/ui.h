/*
 * Functions related to the user interface
 */

#include "SSD1306Ascii.h"
#include "SSD1306AsciiWire.h"

SSD1306AsciiWire oled;

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
