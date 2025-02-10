import json
import os
import random
import time
import requests
import sys
from datetime import datetime, timedelta, timezone
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# === KONFIGURASI PROXY (PROXIFLY) ===
PROXIFLY_API_KEY = "3fvRFNgH35EPugpAXZszBroPAjjZL6cKn9cc5spGZo4r"
PROXIFLY_URL = "https://api.proxifly.dev/get-proxy"
PROXIES = []  # Daftar proxy yang akan diisi

def fetch_proxies():
    """
    Mengambil daftar proxy dari Proxifly.
    """
    global PROXIES
    payload = {
        "apiKey": PROXIFLY_API_KEY,
        "country": ["US", "RU"],
        "https": True,
        "quantity": 20
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(PROXIFLY_URL, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "proxies" in data:
            PROXIES = [f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}" for proxy in data["proxies"]]
            print(Fore.GREEN + f"✅ Berhasil mengambil {len(PROXIES)} proxy dari Proxifly!")
        else:
            print(Fore.RED + "⚠️ Tidak ada data proxy yang diterima dari Proxifly.")
            PROXIES = []
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal mengambil proxy: {e}")
        PROXIES = []

def get_random_proxy():
    """
    Mengembalikan salah satu proxy secara acak. Jika daftar proxy kosong, maka akan mencoba mengambil proxy.
    """
    if not PROXIES:
        fetch_proxies()
    return random.choice(PROXIES) if PROXIES else None

# === KONFIGURASI AGENT & FILE ===
agents = {
    "deployment_p5J9lz1Zxe7CYEoo0TZpRVay": {"name": "Professor 🧠", "topic": "ai"},
    "deployment_7sZJSiCqCNDy9bBHTEh7dwd9": {"name": "Crypto Buddy 💰", "topic": "crypto"},
    "deployment_SoFftlsf9z4fyA3QCHYkaANq": {"name": "Sherlock 🔎", "topic": "fraud_detection"}
}

wallet_file = "akun.txt"
interaction_log_file = "interaction_log.json"
random_questions_file = "random_questions.json"

# === FUNGSI PENDUKUNG ===
def read_wallets():
    """
    Membaca daftar wallet dari file akun.txt.
    """
    try:
        with open(wallet_file, "r") as f:
            wallets = [line.strip() for line in f if line.strip()]
        return wallets
    except FileNotFoundError:
        print(Fore.RED + f"⚠️ File {wallet_file} tidak ditemukan! Harap buat dan isi dengan wallet address.")
        sys.exit(1)

def read_interaction_log():
    """
    Membaca file log interaksi harian.
    """
    try:
        with open(interaction_log_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_interaction_log(log_data):
    """
    Menyimpan log interaksi ke file.
    """
    with open(interaction_log_file, "w") as f:
        json.dump(log_data, f, indent=2)

def get_today_date_utc():
    """
    Mengembalikan tanggal hari ini (UTC) dalam format YYYY-MM-DD.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def check_and_reset_daily_interactions(log_data, daily_limit, wallet):
    """
    Jika tanggal di log berbeda dengan hari ini, reset interaksi harian dan perbarui wallet.
    """
    today_utc = get_today_date_utc()
    if log_data.get("date") != today_utc:
        print(Fore.YELLOW + "⚠️ Hari baru dimulai! Mereset interaksi harian untuk semua agent.")
        log_data["date"] = today_utc
        log_data["wallet"] = wallet
        log_data["dailyLimit"] = daily_limit
        log_data["interactions"] = {agent_id: 0 for agent_id in agents}
    return log_data

def get_random_questions_by_topic(file_path, topic, count):
    """
    Mengambil sejumlah pertanyaan acak dari file berdasarkan topik.
    Jika jumlah pertanyaan tidak mencukupi, akan memilih secara acak (dengan pengulangan).
    """
    try:
        with open(file_path, "r") as f:
            questions = json.load(f)
        if topic not in questions:
            raise ValueError(f"Topik '{topic}' tidak ditemukan dalam file pertanyaan.")
        if len(questions[topic]) < count:
            return random.choices(questions[topic], k=count)
        return random.sample(questions[topic], count)
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal membaca pertanyaan acak untuk topik {topic}: {e}")
        sys.exit(1)

def send_question_to_agent(agent_id, question):
    """
    Mengirim pertanyaan ke agent dengan percobaan maksimal 3 kali dan menggunakan proxy acak.
    """
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):  # 3 kali percobaan
        proxy = get_random_proxy()
        proxies = {"http": proxy, "https": proxy} if proxy else None
        try:
            response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=5)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]
        except Exception as e:
            print(Fore.RED + f"⚠️ (Percobaan {attempt+1}/3) Gagal mengirim ke {agent_id} melalui proxy {proxy}: {e}")
            time.sleep(2)
    return None

def report_usage(wallet, options):
    """
    Melaporkan penggunaan ke endpoint yang ditentukan.
    """
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

# === FUNGSI UTAMA ===
def main():
    # Tampilan judul dan informasi
    print(Fore.CYAN + Style.BRIGHT + "🚀 Kite AI - Daily Interaction 🚀")
    print(Fore.CYAN + "----------------------------------------")
    print(Fore.MAGENTA + "Channel: https://t.me/ugdairdrop")
    print(Fore.MAGENTA + "Author: https://t.me/jodohsaya")
    print(Fore.CYAN + "----------------------------------------\n")
    
    # Cek apakah file random_questions.json ada, jika tidak maka coba buat dengan menjalankan rand.py
    if not os.path.exists(random_questions_file):
        print(Fore.YELLOW + f"⚠️ File {random_questions_file} tidak ditemukan. Membuat file baru...")
        try:
            os.system(f"{sys.executable} rand.py")
            print(Fore.GREEN + f"✅ File {random_questions_file} berhasil dibuat.")
        except Exception as e:
            print(Fore.RED + f"⚠️ Gagal menjalankan rand.py: {e}")
            sys.exit(1)
    
    # Baca daftar wallet dari akun.txt
    wallets = read_wallets()
    
    # Baca log interaksi atau inisialisasi jika belum ada
    interaction_log = read_interaction_log()
    daily_limit = interaction_log.get("dailyLimit", 20)
    print(Fore.BLUE + f"📊 Batas interaksi harian per agent: {daily_limit}\n")
    
    # Proses tiap wallet satu per satu
    for wallet_index, wallet in enumerate(wallets, start=1):
        print(Fore.YELLOW + f"\n🔄 Menggunakan Wallet ke-{wallet_index}: {wallet}")
        
        # Perbarui log interaksi (reset jika hari baru)
        interaction_log = check_and_reset_daily_interactions(interaction_log, daily_limit, wallet)
        save_interaction_log(interaction_log)
        
        # Ambil pertanyaan acak per agent berdasarkan topik
        random_questions_by_topic = {}
        for agent_id, agent_info in agents.items():
            topic = agent_info["topic"]
            random_questions_by_topic[agent_id] = get_random_questions_by_topic(random_questions_file, topic, daily_limit)
        
        # Proses interaksi untuk tiap agent
        for agent_id, agent_info in agents.items():
            agent_name = agent_info["name"]
            print(Fore.MAGENTA + f"\n🤖 Menggunakan Agent: {agent_name}")
            print(Fore.CYAN + "----------------------------------------")
            
            # Cek apakah batas harian untuk agent sudah tercapai
            interactions_count = interaction_log["interactions"].get(agent_id, 0)
            if interactions_count >= daily_limit:
                print(Fore.YELLOW + f"⚠️ Batas interaksi harian untuk agent {agent_name} sudah tercapai ({daily_limit}x).")
                continue
            
            remaining_interactions = daily_limit - interactions_count
            
            for i in range(remaining_interactions):
                question = random_questions_by_topic[agent_id].pop()
                print(Fore.YELLOW + f"🔄 Interaksi ke-{interaction_log['interactions'][agent_id] + 1} untuk agent {agent_name}")
                print(Fore.CYAN + f"❓ Pertanyaan: {question}")
                
                response = send_question_to_agent(agent_id, question)
                answer_text = response.get("content", "Tidak ada jawaban") if response else "Tidak ada jawaban"
                print(Fore.GREEN + f"💡 Jawaban: {answer_text}")
                
                # Laporkan penggunaan
                report_usage(wallet, {
                    "agent_id": agent_id,
                    "question": question,
                    "response": answer_text
                })
                
                # Update log interaksi
                interaction_log["interactions"][agent_id] += 1
                save_interaction_log(interaction_log)
                
                delay = random.randint(2, 5)
                print(Fore.BLUE + f"⏳ Menunggu {delay} detik sebelum interaksi berikutnya...\n")
                time.sleep(delay)
            
            print(Fore.CYAN + "----------------------------------------")
        
        print(Fore.GREEN + "\n🎉 Sesi selesai untuk wallet ini!")
    
    print(Fore.GREEN + "\nSemua wallet telah diproses. Program selesai.")

if __name__ == "__main__":
    main()
