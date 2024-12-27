from pymongo import MongoClient
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с других доменов, включая GitHub Pages

# Подключение к MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Убедитесь, что MongoDB запущена
db = client["telegram_webapp"]
users_collection = db["users"]


# Функция обновления пользователя
def update_user_activity(user_data, session_time):
    user_id = user_data["id"]
    user_record = users_collection.find_one({"id": user_id})

    if not user_record:
        # Создаем нового пользователя, если он не существует
        user_record = {
            "id": user_id,
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "username": user_data.get("username", ""),
            "language_code": user_data.get("language_code", ""),
            "Mini App is active for session time": session_time,
            "Mini App is active for all time": session_time,
        }
        users_collection.insert_one(user_record)
    else:
        # Обновляем время активности
        new_session_time = user_record.get("Mini App is active for all time", 0) + session_time
        users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "Mini App is active for session time": session_time,
                    "Mini App is active for all time": new_session_time,
                }
            }
        )


# Маршрут для обновления активности
@app.route("/update_activity", methods=["GET", "POST"])
def update_activity():
    if request.method == "GET":
        # Получение общего времени для конкретного пользователя
        user_id = request.args.get("id")
        if not user_id:
            return jsonify({"error": "User ID not provided"}), 400

        user = users_collection.find_one({"id": int(user_id)}, {"_id": 0})
        if user:
            return jsonify({"total_time": user.get("Mini App is active for all time", 0)})
        return jsonify({"total_time": 0})

    elif request.method == "POST":
        # Обновление активности
        data = request.json
        print("Received data:", data)  # Отладка: проверяем, какие данные поступают
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_data = data.get("user")
        session_time = data.get("session_time", 0)

        if not user_data or "id" not in user_data:
            return jsonify({"error": "Invalid user data"}), 400

        print("Updating user activity:", user_data)  # Отладка: смотрим, что передаётся
        update_user_activity(user_data, session_time)
        return jsonify({"status": "success"}), 200


# Маршрут для получения всех пользователей (для проверки)
@app.route("/get_users", methods=["GET"])
def get_users():
    users = list(users_collection.find({}, {"_id": 0}))  # Исключаем _id из вывода
    return jsonify(users)


# Маршрут для получения логов
@app.route("/logs", methods=["POST"])
def logs():
    data = request.json
    if not data or "log" not in data:
        return jsonify({"error": "No log provided"}), 400
    print(f"LOG: {data['log']}")
    return jsonify({"status": "log received"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
