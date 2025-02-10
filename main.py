import json
import os
import random
import time
import requests
import sys
from datetime import datetime, timedelta

# Konfigurasi Agents
agents = {
    "deployment_p5J9lz1Zxe7CYEoo0TZpRVay": {"name": "Professor 🧠", "topic": "ai"},
    "deployment_7sZJSiCqCNDy9bBHTEh7dwd9": {"name": "Crypto Buddy 💰", "topic": "crypto"},
    "deployment_SoFftlsf9z4fyA3QCHYkaANq": {"name": "Sherlock 🔎", "topic": "fraud_detection"}
}

# File untuk menyimpan data
interaction_log_file = "interaction_log.json"
wallet_file = "akun.txt"
random_questions_file = "random_questions.json"

# Membaca daftar wallet dari file
def read_wallets():
    try:
        with open(wallet_file, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("⚠️ File akun.txt tidak ditemukan!")
        exit(1)

# Mendapatkan tanggal hari ini dalam format UTC
def get_today_date_utc():
    return datetime.utcnow().strftime("%Y-%m-%d")

# Reset log interaksi harian
def reset_daily_interactions():
    return {
        "date": get_today_date_utc(),
        "interactions": {}
    }

# Memuat log interaksi harian
def load_interaction_log():
    try:
        with open(interaction_log_file, "r") as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = reset_daily_interactions()

    if log_data.get("date") != get_today_date_utc():
        log_data = reset_daily_interactions()

    # Tambahkan wallet yang belum ada dalam log
    wallets = read_wallets()
    for wallet in wallets:
        if wallet not in log_data["interactions"]:
            log_data["interactions"][wallet] = {agent_id: 0 for agent_id in agents}

    save_interaction_log(log_data)
    return log_data

# Menyimpan log interaksi harian
def save_interaction_log(log_data):
    with open(interaction_log_file, "w") as f:
        json.dump(log_data, f, indent=2)

# Mengambil pertanyaan acak berdasarkan topik
def get_random_questions_by_topic(topic, count):
    try:
        with open(random_questions_file, "r") as f:
            questions = json.load(f)
        return random.sample(questions.get(topic, []), count)
    except Exception as e:
        print(f"⚠️ Gagal membaca pertanyaan untuk topik {topic}: {e}")
        exit(1)

# Mengirim pertanyaan ke agent AI
def send_question_to_agent(agent_id, question):
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):  # Coba 3 kali dengan timeout 5 detik
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {})
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Percobaan {attempt + 1}: Gagal menghubungi agent {agent_id}. Error: {e}")
            time.sleep(5)  # Tunggu 5 detik sebelum mencoba lagi
    
    return None

# Melaporkan penggunaan ke server
def report_usage(wallet, agent_id, question, response):
    url = "https://quests-usage-dev.prod.zettablock.com/api/report_usage"
    payload = {
        "wallet_address": wallet,
        "agent_id": agent_id,
        "request_text": question,
        "response_text": response or "Tidak ada jawaban",
        "request_metadata": {}
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        print("✅ Data penggunaan berhasil dilaporkan!\n")
    except Exception as e:
        print(f"⚠️ Gagal melaporkan penggunaan: {e}\n")

# Fungsi utama
def main():
    print("\n🚀 Menjalankan Kite AI - Daily Interaction 🚀\n")

    interaction_log = load_interaction_log()
    wallets = read_wallets()
    daily_limit = 20  # Batas interaksi per agent per hari

    for idx, wallet in enumerate(wallets, start=1):
        print(f"🔄 Wallet ke-{idx}: {wallet}")

        for agent_id, agent_info in agents.items():
            agent_name = agent_info["name"]
            topic = agent_info["topic"]

            print(f"🤖 Menggunakan Agent: {agent_name} | Wallet: {wallet}")
            
            # Cek apakah batas interaksi harian sudah tercapai
            interaksi_ke = interaction_log["interactions"][wallet].get(agent_id, 0)
            if interaksi_ke >= daily_limit:
                print(f"⚠️ Batas interaksi harian untuk {agent_name} sudah tercapai ({daily_limit}x).")
                continue

            questions = get_random_questions_by_topic(topic, daily_limit)
            for _ in range(daily_limit - interaksi_ke):
                if not questions:
                    print(f"⚠️ Tidak ada pertanyaan tersisa untuk {agent_name}.")
                    break

                question = questions.pop()
                print(f"❓ Interaksi ke-{interaksi_ke + 1} | Pertanyaan: {question}")

                response = send_question_to_agent(agent_id, question)
                response_text = response.get("content", "Tidak ada jawaban") if response else "Tidak ada jawaban"

                print(f"💡 Jawaban: {response_text}")

                # Laporkan penggunaan
                report_usage(wallet, agent_id, question, response_text)

                # Update log
                interaction_log["interactions"][wallet][agent_id] = interaksi_ke + 1
                save_interaction_log(interaction_log)

                # Delay acak antara 3-7 detik
                delay = random.randint(3, 7)
                print(f"⏳ Menunggu {delay} detik sebelum pertanyaan berikutnya...\n")
                time.sleep(delay)

        print("✅ Wallet selesai diproses!\n")

    print("✅ Semua wallet selesai diproses! Menunggu hingga jam 08:00 WIB untuk menjalankan ulang...")

    # Hitung waktu hingga 08:00 WIB
    now = datetime.utcnow()
    next_run = now.replace(hour=1, minute=0, second=0, microsecond=0)  # 08:00 WIB = 01:00 UTC
    if now >= next_run:
        next_run += timedelta(days=1)  # Jika sudah lewat jam 08:00, tunggu hingga besok

    time_until_next_run = (next_run - now).total_seconds()
    print(f"⏰ Waktu hingga restart: {int(time_until_next_run)} detik")
    time.sleep(time_until_next_run)

# Jalankan script
if __name__ == "__main__":
    while True:
        main()
