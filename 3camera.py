import cv2
import numpy as np
import requests

# 🔐 LINE OA Access Token
LINE_TOKEN = "X8o7GTODP7P4+EjzJMoEDi8lYaNAcc/MilJaPaWrZNI54jHB0O/Qn0Mjq2OaRDoB9gm+0N7DLMN6gpKoyQc9Cr6HOZyXnUqcHes0pXboS9TigM573aJVJZKlhgSHXfXp2NGLDnA7b+mGDdBwgVjMrAdB04t89/1O/w1cDnyilFU="

# โหลด user ID ที่ต้องส่งแจ้งเตือน
def load_user_ids(file_path="user_ids.txt"):
    try:
        with open(file_path, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

# ฟังก์ชันส่งข้อความ LINE
def send_line_alert(message, user_id):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        print(f"📨 แจ้งเตือนไปยัง {user_id}: {r.status_code}")
    except Exception as e:
        print("❌ ส่งแจ้งเตือนล้มเหลว:", e)

# คำนวณ sharpness และ stddev
def detect_dust_intensity(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    stddev = np.std(gray)
    return sharpness, stddev

# ประเมินระดับฝุ่น
def estimate_dust_level(sharpness, stddev):
    if sharpness > 200 and stddev > 40:
        return "< 0.05 mg/m³", "GOOD"
    elif sharpness > 100 and stddev > 30:
        return "0.05–0.15 mg/m³", "MODERATE"
    elif sharpness > 50 and stddev > 20:
        return "0.15–0.30 mg/m³", "POOR"
    elif sharpness > 30 and stddev > 15:
        return "0.30–1.0 mg/m³", "VERY POOR"
    else:
        return "> 1 mg/m³", "VERY VERY POOR"

# แสดงผลบนจอ
def annotate_zone(frame, x, y, w, h, sharpness, stddev, dust_level, status, label):
    color = (0, 255, 0) if status == "GOOD" else (0, 165, 255) if "POOR" in status else (0, 0, 255)
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.putText(frame, f"{label} | S:{sharpness:.1f} | SD:{stddev:.1f} | {status}",
                (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

# 🎯 กำหนดโซน
zones = [
    (100, 100, 100, 100, "Zone 1"),
    (250, 100, 100, 100, "Zone 2"),
    (400, 100, 100, 100, "Zone 3"),
]
alert_sent = [False, False, False]

# 📷 กล้องจาก OBS หรืออื่น ๆ
CAM_INDEX = 2
cap = cv2.VideoCapture(CAM_INDEX)

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ กล้องไม่ทำงาน")
        break

    for i, (x, y, w, h, label) in enumerate(zones):
        roi = frame[y:y+h, x:x+w]
        sharpness, stddev = detect_dust_intensity(roi)
        dust_level, status = estimate_dust_level(sharpness, stddev)
        annotate_zone(frame, x, y, w, h, sharpness, stddev, dust_level, status, label)

        if status == "VERY VERY POOR" and not alert_sent[i]:
            message = (
                f"🚨 แจ้งเตือน {label} ฝุ่นสูงมาก!\n"
                f"🔹 Sharpness: {sharpness:.2f}\n"
                f"🔹 StdDev: {stddev:.2f}\n"
                f"🔹 ระดับ: {dust_level}\n"
                f"โปรดสวมหน้ากาก N95 ก่อนเข้าพื้นที่นี้"
            )
            for uid in load_user_ids():
                send_line_alert(message, uid)
            alert_sent[i] = True

        if status != "VERY VERY POOR":
            alert_sent[i] = False

    cv2.imshow("Dust Detection - Enhanced", frame)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
