#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

float zeroPitch = 0.0;
float zeroRoll = 0.0;
bool calibrated = false;

// THRESHOLDS

const float threshold = 20.0;  // degrees of tilt to trigger action

const unsigned long commandCooldown = 150;  // ms between commands

unsigned long lastCommandTime = 0;

// Calibration Sequence

void calibrateSensor() {
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  float axf = (float)ax;
  float ayf = (float)ay;
  float azf = (float)az;

  float denomPitch = sqrt(ayf * ayf + azf * azf);
  float denomRoll = sqrt(axf * axf + azf * azf);

  if (denomPitch != 0 && denomRoll != 0) {
    zeroPitch = atan2(axf, denomPitch) * 180.0 / PI;
    zeroRoll = atan2(ayf, denomRoll) * 180.0 / PI;
    calibrated = true;
    Serial.println("Calibration complete.");
  } else {
    Serial.println("Calibration failed (invalid orientation).");
  }
}

void setup() {
  Serial.begin(9600);
  Wire.begin();
  mpu.initialize();

  if (!mpu.testConnection()) {
    Serial.println("MPU6050 connection failed");
    while (1); // halt if not connected
  }

  Serial.println("MPU6050 connected. Send 'CALIBRATE' to set zero position.");
}

void loop() {
  if (Serial.available()) {
    String incoming = Serial.readStringUntil('\n');
    incoming.trim();

    if (incoming == "CALIBRATE") {
      calibrateSensor();
    }
  }

  if (!calibrated) return;

  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  float axf = (float)ax;
  float ayf = (float)ay;
  float azf = (float)az;

  float pitch = 0.0, roll = 0.0;
  float denomPitch = sqrt(ayf * ayf + azf * azf);
  float denomRoll = sqrt(axf * axf + azf * azf);

  if (denomPitch != 0) {
    pitch = atan2(axf, denomPitch) * 180.0 / PI;
  }

  if (denomRoll != 0) {
    roll = atan2(ayf, denomRoll) * 180.0 / PI;
  }

  float relativePitch = pitch - zeroPitch;
  float relativeRoll = roll - zeroRoll;

  unsigned long now = millis();
  if (now - lastCommandTime >= commandCooldown) {
    if (relativeRoll > threshold) {
      Serial.println("RIGHT");
    } else if (relativeRoll < -threshold) {
      Serial.println("LEFT");
    } else if (relativePitch > threshold) {
      Serial.println("BACKWARD");
    } else if (relativePitch < -threshold) {
      Serial.println("FORWARD");
    } else {
      Serial.println("NEUTRAL");
    }

    lastCommandTime = now;
  }
}
