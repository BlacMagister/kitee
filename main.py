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

# Konfigurasi
DEFAULT_DAILY_LIMIT = 20  # Batas interaksi harian untuk semua akun
interaction_log_file = "interaction_log.json"
random_questions_file = "random_questions.json"
akun_file = "akun.txt"

# Fungsi untuk membaca daftar wallet dari file
def read_wallets():
    try:
        with open(akun_file, "r") as f:
            wallets = [line.strip() for line in f.readlines() if line.strip()]
        return wallets
    except FileNotFoundError:
        print(Fore.RED + f"⚠️ File {akun_file} tidak ditemukan! Harap buat file tersebut dengan daftar wallet.")
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
    now = datetime.utcnow()
    return now.strftime("%Y-%m-%d")

# Fungsi untuk mereset interaksi harian jika hari berganti (UTC)
def check_and_reset_daily_interactions(log_data, wallet, wallet_index):
    today_utc = get_today_date_utc()
    if log_data.get(wallet, {}).get("date") != today_utc:
        print(Fore.YELLOW + f"⚠️ Hari baru dimulai! Mereset interaksi harian untuk {wallet}.")
        log_data[wallet] = {
            "index": wallet_index,  # Menyimpan nomor urut wallet
            "date": today_utc,
            "dailyLimit": DEFAULT_DAILY_LIMIT,
            "interactions": {agent_id: 0 for agent_id in agents}
        }
    return log_data

# Fungsi untuk membaca pertanyaan acak berdasarkan topik
def get_random_questions_by_topic(file_path, topic, count):
    try:
        with open(file_path, "r") as f:
            questions = json.load(f)
        return random.sample(questions.get(topic, []), count)
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal membaca pertanyaan acak untuk topik {topic}: {e}")
        exit(1)

# Fungsi untuk mengirim pertanyaan ke agent AI
def send_question_to_agent(agent_id, question):
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]
    except Exception as e:
        print(Fore.RED + f"⚠️ Error saat mengirim pertanyaan ke agent {agent_id}: {e}")
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
        print(Fore.YELLOW + f"✅ Data penggunaan untuk {wallet} berhasil dilaporkan!\n")
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal melaporkan penggunaan untuk {wallet}: {e}\n")

# Fungsi utama
def main():
    print(Fore.CYAN + Style.BRIGHT + "🚀 Kite AI - Multi Account Daily Interaction 🚀")
    print(Fore.CYAN + "----------------------------------------")

    # Baca daftar wallet dari file
    wallets = read_wallets()
    print(Fore.BLUE + f"📌 Ditemukan {len(wallets)} akun dalam {akun_file}\n")

    # Periksa apakah file random_questions.json ada
    if not os.path.exists(random_questions_file):
        print(Fore.YELLOW + "⚠️ File random_questions.json tidak ditemukan. Membuat file baru...")
        try:
            os.system(f"{sys.executable} rand.py")
            print(Fore.GREEN + "✅ File random_questions.json berhasil dibuat.")
        except Exception as e:
            print(Fore.RED + f"⚠️ Gagal menjalankan rand.py: {e}")
            exit(1)

    # Baca data interaksi harian
    interaction_log = read_interaction_log()

    # Loop untuk setiap akun berdasarkan urutan dalam `akun.txt`
    for index, wallet in enumerate(wallets, start=1):
        print(Fore.MAGENTA + f"\n🔑 Memproses akun ke-{index}: {wallet}")

        # Perbarui log interaksi dengan batas harian (UTC)
        interaction_log = check_and_reset_daily_interactions(interaction_log, wallet, index)
        save_interaction_log(interaction_log)

        # Ambil pertanyaan acak dari file random_questions.json berdasarkan topik
        random_questions_by_topic = {}
        for agent_id, agent_info in agents.items():
            topic = agent_info["topic"]
            random_questions_by_topic[agent_id] = get_random_questions_by_topic(
                random_questions_file, topic, DEFAULT_DAILY_LIMIT
            )

        # Loop untuk setiap agent
        for agent_id, agent_info in agents.items():
            agent_name = agent_info["name"]
            print(Fore.CYAN + f"\n🤖 Menggunakan Agent: {agent_name}")

            # Periksa apakah batas harian sudah tercapai
            if interaction_log[wallet]["interactions"][agent_id] >= DEFAULT_DAILY_LIMIT:
                print(Fore.YELLOW + f"⚠️ Batas interaksi harian untuk {agent_name} sudah tercapai ({DEFAULT_DAILY_LIMIT}x).")
                continue

            # Hitung sisa interaksi yang diizinkan
            remaining_interactions = DEFAULT_DAILY_LIMIT - interaction_log[wallet]["interactions"][agent_id]

            for _ in range(remaining_interactions):
                question = random_questions_by_topic[agent_id].pop()
                print(Fore.YELLOW + f"❓ Pertanyaan: {question}")

                response = send_question_to_agent(agent_id, question)
                response_text = response.get("content", "Tidak ada jawaban") if response else "Tidak ada jawaban"
                print(Fore.GREEN + f"💡 Jawaban: {response_text}")

                # Laporkan penggunaan
                report_usage(wallet.lower(), {
                    "agent_id": agent_id,
                    "question": question,
                    "response": response_text
                })

                # Update jumlah interaksi
                interaction_log[wallet]["interactions"][agent_id] += 1
                save_interaction_log(interaction_log)

                # Tambahkan delay acak
                time.sleep(random.randint(5, 10))

    print(Fore.GREEN + "\n🎉 Semua akun telah selesai diproses!")

if __name__ == "__main__":
    main()
