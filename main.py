import json
import os
import random
import time
import requests
import sys
from datetime import datetime, timedelta
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# Konfigurasi agents dengan topik spesifik
agents = {
    "deployment_p5J9lz1Zxe7CYEoo0TZpRVay": {"name": "Professor 🧠", "topic": "ai"},
    "deployment_7sZJSiCqCNDy9bBHTEh7dwd9": {"name": "Crypto Buddy 💰", "topic": "crypto"},
    "deployment_SoFftlsf9z4fyA3QCHYkaANq": {"name": "Sherlock 🔎", "topic": "fraud_detection"}
}

# File untuk menyimpan data interaksi harian
interaction_log_file = "interaction_log.json"
random_questions_file = "random_questions.json"
wallet_file = "akun.txt"  # File daftar wallet

# Fungsi untuk membaca daftar wallet dari file
def read_wallets():
    try:
        with open(wallet_file, "r") as f:
            wallets = [line.strip() for line in f if line.strip()]
        return wallets
    except FileNotFoundError:
        print(Fore.RED + f"⚠️ File {wallet_file} tidak ditemukan! Harap buat dan isi dengan wallet address.")
        exit(1)

# Fungsi untuk membaca data interaksi harian
def read_interaction_log():
    try:
        with open(interaction_log_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Fungsi untuk menyimpan data interaksi harian
def save_interaction_log(log_data):
    with open(interaction_log_file, "w") as f:
        json.dump(log_data, f, indent=2)

# Fungsi untuk mendapatkan tanggal hari ini dalam format YYYY-MM-DD (UTC)
def get_today_date_utc():
    return datetime.utcnow().strftime("%Y-%m-%d")

# Fungsi untuk mereset interaksi jika hari baru dimulai (UTC)
def check_and_reset_daily_interactions(log_data, daily_limit, wallet):
    today_utc = get_today_date_utc()
    if log_data.get("date") != today_utc:
        print(Fore.YELLOW + "⚠️ Hari baru dimulai! Mereset interaksi harian.")
        log_data["date"] = today_utc
        log_data["wallet"] = wallet
        log_data["dailyLimit"] = daily_limit
        log_data["interactions"] = {agent_id: 0 for agent_id in agents}
    return log_data

# Fungsi untuk membaca pertanyaan acak berdasarkan topik
def get_random_questions_by_topic(file_path, topic, count):
    try:
        with open(file_path, "r") as f:
            questions = json.load(f)
        return random.sample(questions[topic], count)
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal membaca pertanyaan acak untuk topik {topic}: {e}")
        exit(1)

# Fungsi untuk mengirim pertanyaan ke agent AI dengan timeout & retry
def send_question_to_agent(agent_id, question):
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}

    for attempt in range(3):  # 3 percobaan
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]
        except Exception as e:
            print(Fore.RED + f"⚠️ (Percobaan {attempt+1}/3) Gagal mengirim ke {agent_id}: {e}")
            time.sleep(2)  # Tunggu sebelum mencoba ulang

    return None

# Fungsi untuk melaporkan penggunaan
def report_usage(wallet, options):
    url = "https://quests-usage-dev.prod.zettablock.com/api/report_usage"
    payload = {
        "wallet_address": wallet,
        "agent_id": options["agent_id"],
        "request_text": options["question"],
        "response_text": options["response"],
        "request_metadata": {}
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(Fore.YELLOW + "✅ Data penggunaan berhasil dilaporkan!\n")
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal melaporkan penggunaan: {e}\n")

# Fungsi utama
def main():
    # Judul aplikasi
    print(Fore.CYAN + Style.BRIGHT + "🚀 Kite AI - Daily Interaction 🚀")
    print(Fore.CYAN + "----------------------------------------")
    print(Fore.MAGENTA + "Channel: https://t.me/ugdairdrop")
    print(Fore.MAGENTA + "Author: https://t.me/jodohsaya")
    print(Fore.CYAN + "----------------------------------------\n")

    # Baca daftar wallet dari akun.txt
    wallets = read_wallets()

    # Input batas harian jika belum tersimpan di log
    interaction_log = read_interaction_log()
    daily_limit = interaction_log.get("dailyLimit", 20)

    print(Fore.BLUE + f"📊 Batas interaksi harian per agent: {daily_limit}\n")

    # Loop untuk setiap wallet dalam daftar
    for wallet_index, wallet in enumerate(wallets, start=1):
        print(Fore.YELLOW + f"\n🔄 Menggunakan Wallet ke-{wallet_index}: {wallet}")

        # Perbarui log interaksi dengan batas harian (UTC)
        interaction_log = check_and_reset_daily_interactions(interaction_log, daily_limit, wallet)
        save_interaction_log(interaction_log)

        # Ambil pertanyaan acak dari file random_questions.json
        random_questions_by_topic = {}
        for agent_id, agent_info in agents.items():
            topic = agent_info["topic"]
            random_questions_by_topic[agent_id] = get_random_questions_by_topic(random_questions_file, topic, daily_limit)

        # Loop untuk setiap agent
        for agent_id, agent_info in agents.items():
            agent_name = agent_info["name"]
            print(Fore.MAGENTA + f"\n🤖 Menggunakan Agent: {agent_name}")
            print(Fore.CYAN + "----------------------------------------")

            remaining_interactions = daily_limit - interaction_log["interactions"].get(agent_id, 0)
            if remaining_interactions <= 0:
                print(Fore.YELLOW + f"⚠️ Batas interaksi untuk {agent_name} sudah tercapai.")
                continue

            for _ in range(remaining_interactions):
                question = random_questions_by_topic[agent_id].pop()
                print(Fore.YELLOW + f"❓ Pertanyaan: {question}")

                response = send_question_to_agent(agent_id, question)
                print(Fore.GREEN + f"💡 Jawaban: {response.get('content', 'Tidak ada jawaban') if response else 'Tidak ada jawaban'}")

                report_usage(wallet, {
                    "agent_id": agent_id,
                    "question": question,
                    "response": response.get("content", "Tidak ada jawaban") if response else "Tidak ada jawaban"
                })

                interaction_log["interactions"][agent_id] += 1
                save_interaction_log(interaction_log)

                time.sleep(random.randint(2, 5))  # Kurangi delay agar lebih cepat

        print(Fore.GREEN + "\n🎉 Sesi selesai untuk wallet ini!")

if __name__ == "__main__":
    main()
