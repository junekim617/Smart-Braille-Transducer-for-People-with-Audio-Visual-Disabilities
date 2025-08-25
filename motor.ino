#include <Servo.h>

Servo servos[3];
int servoPins[] = {9, 10, 11};
int angles[] = {60, 180, 120, 0};

int mapCommandToAngle(char command) {
  int index = command - 'A';
  if (index >= 0 && index < 4) {
    return angles[index];
  }
  return 0;
}

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 3; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(60);
  }
  delay(500); 
}

void loop() {
  if (Serial.available() >= 3) {
    char commands[3];
    for (int i = 0; i < 3; i++) {
      commands[i] = Serial.read();
    }
    
    for (int i = 0; i < 3; i++) {
      servos[i].write(mapCommandToAngle(commands[i]));
      delay(300); 
    }
  }
}
