from flask import Flask, request
import json
##พวกนี้คือโค้ดรับ uid เวลาคนทักมา จะเพิ่ม uid
app = Flask(__name__)
user_ids_file = "user_ids.txt"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 ได้รับ webhook:", json.dumps(data, indent=2))

    if "events" in data:
        for event in data["events"]:
            uid = event.get("source", {}).get("userId")
            if uid:
                with open(user_ids_file, "a+") as f:
                    f.seek(0)
                    existing = f.read().splitlines()
                    if uid not in existing:
                        f.write(uid + "\n")
                        print("✅ บันทึก userId ใหม่:", uid)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

