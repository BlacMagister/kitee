import json
import os
import random
import time
import requests
from datetime import datetime, timedelta, timezone
from colorama import Fore, Style, init

# Inisialisasi colorama
init(autoreset=True)

# Definisi warna untuk log
ORANGE = Fore.LIGHTYELLOW_EX
GREEN  = Fore.LIGHTGREEN_EX
RED    = Fore.LIGHTRED_EX
BLUE   = Fore.LIGHTCYAN_EX
WHITE  = Fore.RESET

# Konfigurasi agents
agents = {
    "deployment_p5J9lz1Zxe7CYEoo0TZpRVay": {"name": "Professor 🧠", "topic": "ai"},
    "deployment_7sZJSiCqCNDy9bBHTEh7dwd9": {"name": "Crypto Buddy 💰", "topic": "crypto"},
    "deployment_SoFftlsf9z4fyA3QCHYkaANq": {"name": "Sherlock 🔎", "topic": "fraud_detection"}
}

# Nama file yang digunakan
interaction_log_file = "interaction_log.json"
wallet_file = "akun.txt"
random_questions_file = "random_questions.json"

# Fungsi untuk membaca daftar wallet dari file akun.txt
def read_wallets():
    try:
        with open(wallet_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{RED}⚠️ File {wallet_file} tidak ditemukan!")
        exit(1)

# Mendapatkan tanggal hari ini dalam format UTC (timezone-aware)
def get_today_date_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Reset log interaksi harian (membuat log baru)
def reset_daily_interactions():
    return {
        "date": get_today_date_utc(),
        "interactions": {}  # nanti setiap wallet akan ditambahkan
    }

# Memuat log interaksi harian dari file, dan memastikan semua wallet ada di dalamnya
def load_interaction_log():
    try:
        with open(interaction_log_file, "r") as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = reset_daily_interactions()

    if log_data.get("date") != get_today_date_utc():
        log_data = reset_daily_interactions()

    # Pastikan semua wallet yang ada di akun.txt terdaftar dalam log
    wallets = read_wallets()
    for wallet in wallets:
        if wallet not in log_data["interactions"]:
            log_data["interactions"][wallet] = {agent_id: 0 for agent_id in agents}
    save_interaction_log(log_data)
    return log_data

# Menyimpan log interaksi ke file
def save_interaction_log(log_data):
    with open(interaction_log_file, "w") as f:
        json.dump(log_data, f, indent=2)

# Mengambil pertanyaan acak berdasarkan topik dari file random_questions.json
def get_random_questions_by_topic(topic, count):
    try:
        with open(random_questions_file, "r") as f:
            questions = json.load(f)
        available = questions.get(topic, [])
        if len(available) < count:
            # Jika pertanyaan kurang, gunakan random.choices dengan pengulangan
            return random.choices(available, k=count)
        return random.sample(available, count)
    except Exception as e:
        print(f"{RED}⚠️ Gagal membaca pertanyaan untuk topik {topic}: {e}")
        exit(1)

# Mengirim pertanyaan ke agent AI
def send_question_to_agent(agent_id, question):
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):  # Coba hingga 3 kali
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                # Ambil jawaban dari response
                answer_data = response.json().get("choices", [{}])[0].get("message", "Jawaban tidak tersedia.")
                if isinstance(answer_data, dict):
                    # Jika formatnya dictionary, ambil nilai 'content'
                    return answer_data.get("content", "Jawaban tidak tersedia.")
                else:
                    return answer_data
            elif response.status_code == 429:
                print(f"{RED}⚠️ 429 Too Many Requests untuk {agent_id}! Skip pertanyaan ini...")
                return None  # Skip pertanyaan jika 429
            else:
                print(f"{RED}⚠️ Gagal (status code {response.status_code}) untuk {agent_id}")
        except requests.RequestException as e:
            print(f"{RED}⚠️ Error pada request ke {agent_id}: {e}")
        time.sleep(2)
    return None

# Melaporkan penggunaan ke server
def report_usage(wallet, agent_id, question, response_text):
    url = "https://quests-usage-dev.prod.zettablock.com/api/report_usage"
    # Jika response_text berupa dictionary, ambil 'content'
    if isinstance(response_text, dict):
        response_text = response_text.get("content", "Jawaban tidak tersedia.")
    payload = {
        "wallet_address": wallet,
        "agent_id": agent_id,
        "request_text": question,
        "response_text": response_text or "Jawaban tidak tersedia",
        "request_metadata": {}
    }
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        r.raise_for_status()
        print(f"{GREEN}✅ Data penggunaan berhasil dilaporkan!")
    except Exception as e:
        print(f"{RED}⚠️ Gagal melaporkan penggunaan: {e}")

# Fungsi utama untuk menjalankan interaksi
def main():
    print(f"{BLUE}🚀 Menjalankan Kite AI - Daily Interaction 🚀")
    
    wallets = read_wallets()
    interaction_log = load_interaction_log()
    daily_limit = 20  # Batas interaksi per agent per hari

    # Proses tiap wallet secara berurutan
    for wallet_index, wallet in enumerate(wallets, start=1):
        print(f"{ORANGE}🔄 Wallet ke-{wallet_index}: {wallet}")
        
        # Proses setiap agent untuk wallet tersebut
        for agent_id, agent_info in agents.items():
            agent_name = agent_info["name"]
            topic = agent_info["topic"]
            current_interactions = interaction_log["interactions"][wallet].get(agent_id, 0)
            
            if current_interactions >= daily_limit:
                print(f"{RED}⚠️ Batas interaksi harian untuk {agent_name} pada wallet {wallet} sudah tercapai ({daily_limit}x).")
                continue

            sisa = daily_limit - current_interactions
            questions = get_random_questions_by_topic(topic, sisa)
            
            for i in range(sisa):
                if not questions:
                    print(f"{RED}⚠️ Tidak ada pertanyaan tersisa untuk topik {topic}.")
                    break
                question = questions.pop()
                interaksi_ke = current_interactions + 1
                print(f"{BLUE}🤖 Menggunakan Agent: {agent_name} | Wallet: {wallet}")
                print(f"{WHITE}❓ Interaksi ke-{interaksi_ke} | Pertanyaan: {question}")
                
                answer = send_question_to_agent(agent_id, question)
                if answer:
                    print(f"{GREEN}💡 Jawaban: {answer}")
                else:
                    print(f"{RED}⚠️ Tidak ada jawaban diterima untuk pertanyaan ini.")
                
                report_usage(wallet, agent_id, question, answer)
                
                current_interactions += 1
                interaction_log["interactions"][wallet][agent_id] = current_interactions
                save_interaction_log(interaction_log)
                
                time.sleep(5)  # Delay 5 detik antar pertanyaan

    print(f"{GREEN}✅ Semua wallet selesai diproses!")
    
    # Menunggu hingga jam 08:00 WIB (01:00 UTC) untuk menjalankan ulang
    now_utc = datetime.now(timezone.utc)
    next_run = now_utc.replace(hour=1, minute=0, second=0, microsecond=0)
    if now_utc >= next_run:
        next_run += timedelta(days=1)
    wait_seconds = (next_run - now_utc).total_seconds()
    print(f"{BLUE}⏳ Menunggu {int(wait_seconds)} detik hingga jam 08:00 WIB untuk menjalankan ulang...")
    time.sleep(wait_seconds)

if __name__ == "__main__":
    while True:
        main()
