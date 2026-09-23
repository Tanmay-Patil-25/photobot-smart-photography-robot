#!/usr/bin/env python3
"""
Photo Bot - LAPTOP TEST VERSION
No Raspberry Pi needed
Uses Laptop Webcam or Phone Camera
"""

import cv2
import time
import os
import numpy as np
from datetime import datetime

# ============================================
# FAKE GPIO (Simulates Raspberry Pi GPIO)
# ============================================
class FakeGPIO:
    """
    Simulates RPi.GPIO for laptop testing
    No real hardware needed!
    """
    BCM = "BCM"
    OUT = "OUT"
    
    @staticmethod
    def setmode(mode):
        print(f"[SIMULATOR] GPIO Mode set: {mode}")
    
    @staticmethod
    def setup(pin, mode):
        print(f"[SIMULATOR] GPIO Pin {pin} setup as {mode}")
    
    @staticmethod
    def cleanup():
        print("[SIMULATOR] GPIO Cleanup done")

    class PWM:
        def __init__(self, pin, frequency):
            self.pin = pin
            self.frequency = frequency
            self.current_duty = 0
            print(f"[SIMULATOR] PWM created on Pin {pin}")
        
        def start(self, duty_cycle):
            self.current_duty = duty_cycle
            print(f"[SIMULATOR] PWM Pin {self.pin} started "
                  f"at {duty_cycle}% duty cycle")
        
        def ChangeDutyCycle(self, duty):
            self.current_duty = duty
            angle = (duty - 2) * 18
            print(f"[SIMULATOR] Pin {self.pin} → "
                  f"Duty: {duty:.1f}% → Angle: {angle:.1f}°")
        
        def stop(self):
            print(f"[SIMULATOR] PWM Pin {self.pin}stopped")

# Use Fake GPIO instead of real one
GPIO = FakeGPIO()

# ============================================
# CONFIGURATION
# ============================================

# Camera Options:
# 0 = Laptop Webcam (Default)
# 1 = External USB Camera
# "http://IP:8080/video" = Phone Camera

CAMERA_SOURCE = 0           # Use laptop webcam
SAVE_FOLDER = "PhotoBot_Test_Photos"
PHOTO_COUNT = 5             # Photos to capture
MAX_ZOOM = 3.0              # Maximum zoom level

# Simulate Servo Pins
PAN_PIN = 17
TILT_PIN = 18

# ============================================
# SETUP SIMULATED GPIO
# ============================================
GPIO.setmode(GPIO.BCM)
GPIO.setup(PAN_PIN, GPIO.OUT)
GPIO.setup(TILT_PIN, GPIO.OUT)

pan_servo = GPIO.PWM(PAN_PIN, 50)
tilt_servo = GPIO.PWM(TILT_PIN, 50)

pan_servo.start(7.5)
tilt_servo.start(7.5)

# Track servo positions
servo_positions = {
    "pan": 90,
    "tilt": 90
}

# ============================================
# SERVO CONTROL (Simulated)
# ============================================
def set_servo_angle(servo, angle, name="servo"):
    """Simulate servo movement"""
    angle = max(0, min(180, angle))
    duty = 2 + (angle / 18)
    servo.ChangeDutyCycle(duty)
    servo_positions[name] = angle
    time.sleep(0.1)  # Faster for testing

# ============================================
# FACE DETECTION
# ============================================
def detect_faces(frame):
    """Detect faces in frame"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 
        'haarcascade_frontalface_default.xml'
    )
    
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    return faces

# ============================================
# AUTO ADJUST FRAME
# ============================================
def auto_adjust_frame(frame):
    """Auto adjust camera to center face"""
    faces = detect_faces(frame)
    height, width = frame.shape[:2]
    
    center_x = width // 2
    center_y = height // 2
    
    if len(faces) > 0:
        # Get largest face
        largest_face = max(faces, 
                          key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face
        
        face_cx = x + w // 2
        face_cy = y + h // 2
        
        offset_x = face_cx - center_x
        offset_y = face_cy - center_y
        
        # Simulate pan servo
        if abs(offset_x) > 30:
            pan_angle = 90 + (offset_x / width) * 60
            set_servo_angle(pan_servo, 
                          pan_angle, "pan")
        
        # Simulate tilt servo
        if abs(offset_y) > 30:
            tilt_angle = 90 - (offset_y / height) * 60
            set_servo_angle(tilt_servo, 
                          tilt_angle, "tilt")
        
        return True, largest_face
    
    return False, None

# ============================================
# DIGITAL ZOOM
# ============================================
def digital_zoom(frame, zoom_level):
    """Apply digital zoom"""
    if zoom_level <= 1.0:
        return frame
    
    h, w = frame.shape[:2]
    new_h = int(h / zoom_level)
    new_w = int(w / zoom_level)
    
    start_y = (h - new_h) // 2
    start_x = (w - new_w) // 2
    
    cropped = frame[start_y:start_y+new_h,
                    start_x:start_x+new_w]
    
    return cv2.resize(cropped, (w, h))

# ============================================
# SAVE PHOTO
# ============================================
def save_photo(frame, number, zoom):
    """Save photo to folder"""
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    filename = (f"photobot_{timestamp}"
                f"_zoom{zoom}x_#{number}.jpg")
    filepath = os.path.join(SAVE_FOLDER, filename)
    
    cv2.imwrite(filepath, frame,
                [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    print(f"✅ Saved: {filename}")
    return filepath

# ============================================
# DRAW UI ON SCREEN
# ============================================
def draw_ui(frame, status, photo_count, 
            zoom, face_detected):
    """Draw info overlay"""
    h, w = frame.shape[:2]
    
    # Top bar
    cv2.rectangle(frame, (0, 0), 
                  (w, 70), (0, 0, 0), -1)
    
    # Title
    cv2.putText(frame, "PHOTO BOT - TEST MODE",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 255), 2)
    
    # Status
    cv2.putText(frame,
                f"Status: {status} | "
                f"Photos: {photo_count}/{PHOTO_COUNT} | "
                f"Zoom: {zoom:.1f}x",
                (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (255, 255, 255), 1)
    
    # Servo positions
    pan_pos = servo_positions["pan"]
    tilt_pos = servo_positions["tilt"]
    
    cv2.putText(frame,
                f"Pan: {pan_pos:.0f}° | "
                f"Tilt: {tilt_pos:.0f}°",
                (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 255, 0), 1)
    
    # Face indicator
    color = (0, 255, 0) if face_detected else (0, 0, 255)
    label = "FACE LOCKED" if face_detected else "SEARCHING..."
    cv2.putText(frame, label,
                (w - 180, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, color, 2)
    
    # Center crosshair
    cx, cy = w // 2, h // 2
    cv2.line(frame, (cx-30, cy), 
             (cx+30, cy), (0, 255, 0), 1)
    cv2.line(frame, (cx, cy-30), 
             (cx, cy+30), (0, 255, 0), 1)
    cv2.circle(frame, (cx, cy), 
               30, (0, 255, 0), 1)
    
    return frame

# ============================================
# MAIN TEST LOOP
# ============================================
def run_laptop_test():
    """Run Photo Bot in laptop test mode"""
    
    print("=" * 50)
    print("🤖 PHOTO BOT - LAPTOP TEST MODE")
    print("=" * 50)
    print(f"📷 Camera Source: {CAMERA_SOURCE}")
    print(f"📁 Save Folder: {SAVE_FOLDER}")
    print(f"📸 Photos to take: {PHOTO_COUNT}")
    print("=" * 50)
    print("Controls:")
    print("  SPACE = Manual capture photo")
    print("  Q     = Quit")
    print("  Z     = Zoom In")
    print("  X     = Zoom Out")
    print("=" * 50)
    
    # Connect camera
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    
    if not cap.isOpened():
        print("❌ Cannot open camera!")
        print("Try changing CAMERA_SOURCE to 1")
        return
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("✅ Camera opened successfully!")
    
    photo_count = 0
    current_zoom = 1.0
    zoom_direction = 0.1
    status = "Ready"
    auto_capture = False
    last_capture_time = time.time()
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Frame capture failed")
            break
        
        # Mirror frame
        frame = cv2.flip(frame, 1)
        
        # Auto adjust frame
        face_detected, face_bbox = auto_adjust_frame(frame)
        
        if face_detected:
            status = "Face Locked!"
            x, y, w_f, h_f = face_bbox
            
            # Draw face box
            cv2.rectangle(frame,
                         (x, y),
                         (x+w_f, y+h_f),
                         (0, 255, 0), 2)
            
            # Draw center of face
            fx, fy = x+w_f//2, y+h_f//2
            cv2.circle(frame, (fx, fy), 
                      5, (0, 255, 0), -1)
            
            # Auto zoom
            current_zoom += zoom_direction
            if current_zoom >= MAX_ZOOM:
                zoom_direction = -0.1
            elif current_zoom <= 1.0:
                zoom_direction = 0.1
            
            # Auto capture every 2 seconds
            if (auto_capture and 
                time.time() - last_capture_time > 2 and
                photo_count < PHOTO_COUNT):
                
                zoomed = digital_zoom(frame, current_zoom)
                save_photo(zoomed, photo_count, 
                          round(current_zoom, 1))
                photo_count += 1
                last_capture_time = time.time()
                
        else:
            status = "Searching for face..."
        
        # Apply zoom to display
        display = digital_zoom(frame, current_zoom)
        
        # Draw UI
        display = draw_ui(display, status,
                         photo_count, current_zoom,
                         face_detected)
        
        # Show frame
        cv2.imshow("Photo Bot - Test Mode", display)
        
        # Keyboard controls
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("👋 Quitting...")
            break
            
        elif key == ord(' '):
            # Manual capture
            zoomed = digital_zoom(frame, current_zoom)
            save_photo(zoomed, photo_count,
                      round(current_zoom, 1))
            photo_count += 1
            print(f"📸 Manual capture #{photo_count}")
            
        elif key == ord('z'):
            # Zoom in
            current_zoom = min(MAX_ZOOM, 
                             current_zoom + 0.5)
            print(f"🔍 Zoom: {current_zoom}x")
            
        elif key == ord('x'):
            # Zoom out
            current_zoom = max(1.0, 
                             current_zoom - 0.5)
            print(f"🔍 Zoom: {current_zoom}x")
            
        elif key == ord('a'):
            # Toggle auto capture
            auto_capture = not auto_capture
            state = "ON" if auto_capture else "OFF"
            print(f"🤖 Auto Capture: {state}")
        
        # Done
        if photo_count >= PHOTO_COUNT:
            print(f"\n🎉 Done! {photo_count} photos saved")
            print(f"📁 Check folder: {SAVE_FOLDER}")
            time.sleep(2)
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    pan_servo.stop()
    tilt_servo.stop()
    GPIO.cleanup()
    print("✅ Test Complete!")

# ============================================
# RUN TEST
# ============================================
if __name__ == "__main__":
    run_laptop_test()
