import json
import os
import random
import time
import requests
import sys
import schedule
from datetime import datetime, timezone, timedelta
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# === KONFIGURASI PROXY (GEONODE) ===
GEONODE_API_URL = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
PROXIES = []

def fetch_proxies():
    """Mengambil daftar proxy dari Geonode."""
    global PROXIES
    try:
        response = requests.get(GEONODE_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            PROXIES = [f"http://{proxy['ip']}:{proxy['port']}" for proxy in data["data"] if 'http' in proxy['protocols']]
            print(Fore.GREEN + f"✅ Berhasil mengambil {len(PROXIES)} proxy dari Geonode!")
        else:
            PROXIES = []
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal mengambil proxy: {e}")
        PROXIES = []

def get_random_proxy():
    """Mengembalikan proxy acak."""
    if not PROXIES:
        fetch_proxies()
    return random.choice(PROXIES) if PROXIES else None

# === KONFIGURASI AGENT & WALLET ===
agents = {
    "deployment_p5J9lz1Zxe7CYEoo0TZpRVay": {"name": "Professor 🧠", "topic": "ai"},
    "deployment_7sZJSiCqCNDy9bBHTEh7dwd9": {"name": "Crypto Buddy 💰", "topic": "crypto"},
    "deployment_SoFftlsf9z4fyA3QCHYkaANq": {"name": "Sherlock 🔎", "topic": "fraud_detection"}
}

wallet_file = "akun.txt"
interaction_log_file = "interaction_log.json"
random_questions_file = "random_questions.json"

def read_wallets():
    """Membaca daftar wallet dari file."""
    try:
        with open(wallet_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + f"⚠️ File {wallet_file} tidak ditemukan!")
        return []

def get_today_date_utc():
    """Mengembalikan tanggal hari ini (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def reset_daily_interactions():
    """Reset interaksi jika sudah ganti hari."""
    today_utc = get_today_date_utc()
    return {
        "date": today_utc,
        "interactions": {wallet: {agent_id: 0 for agent_id in agents} for wallet in read_wallets()}
    }

def save_interaction_log(log_data):
    """Menyimpan log ke file."""
    with open(interaction_log_file, "w") as f:
        json.dump(log_data, f, indent=2)

def load_interaction_log():
    """Memuat log interaksi."""
    try:
        with open(interaction_log_file, "r") as f:
            log_data = json.load(f)
            if log_data.get("date") != get_today_date_utc():
                return reset_daily_interactions()
            return log_data
    except FileNotFoundError:
        return reset_daily_interactions()

def get_random_questions(topic, count):
    """Mengambil pertanyaan acak."""
    try:
        with open(random_questions_file, "r") as f:
            questions = json.load(f)
        return random.sample(questions.get(topic, []), min(count, len(questions.get(topic, []))))
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal membaca pertanyaan: {e}")
        return []

def send_question(agent_id, question):
    """Mengirim pertanyaan ke agent."""
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}

    for _ in range(3):
        proxy = get_random_proxy()
        proxies = {"http": proxy, "https": proxy} if proxy else None
        try:
            response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=5)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", "Tidak ada jawaban")
        except Exception as e:
            print(Fore.RED + f"⚠️ Gagal mengirim ke {agent_id} (proxy: {proxy}): {e}")
            time.sleep(2)
    return "Tidak ada jawaban"

def main():
    print(Fore.CYAN + "🚀 Menjalankan Kite AI - Daily Interaction 🚀")
    
    wallets = read_wallets()
    interaction_log = load_interaction_log()
    save_interaction_log(interaction_log)

    for wallet_index, wallet in enumerate(wallets, start=1):
        print(Fore.YELLOW + f"\n🔄 Wallet ke-{wallet_index}: {wallet}")

        for agent_id, agent_info in agents.items():
            agent_name = agent_info['name']
            interaksi_ke = interaction_log["interactions"][wallet].get(agent_id, 0) + 1

            if interaksi_ke > 20:
                continue  # Jika interaksi sudah mencapai batas, skip
            
            print(Fore.MAGENTA + f"\n🤖 Menggunakan Agent: {agent_name}")
            questions = get_random_questions(agent_info["topic"], 1)  # Ambil 1 pertanyaan

            for question in questions:
                print(Fore.YELLOW + f"🔄 Interaksi ke-{interaksi_ke} dengan {agent_name}")
                print(Fore.CYAN + f"❓ Pertanyaan: {question}")

                response = send_question(agent_id, question)
                print(Fore.GREEN + f"💡 Jawaban: {response}")

                interaction_log["interactions"][wallet][agent_id] = interaksi_ke
                save_interaction_log(interaction_log)

                time.sleep(random.randint(2, 5))  # Delay sebelum interaksi berikutnya

    print(Fore.GREEN + "\n✅ Semua wallet selesai diproses!")

# === JADWAL ULANG OTOMATIS SETIAP HARI JAM 08:00 WIB ===
def start_scheduler():
    schedule.clear()
    
    def run_script():
        print(Fore.YELLOW + "\n🔄 Menjalankan ulang script pada jam 08:00 WIB\n")
        main()
    
    # Jadwal ulang setiap jam 08:00 WIB
    wib_now = datetime.now() + timedelta(hours=7)
    next_run = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    if wib_now > next_run:
        next_run += timedelta(days=1)
    
    schedule.every().day.at("08:00").do(run_script)
    
    print(Fore.GREEN + f"⏳ Script akan dijalankan ulang setiap jam 08:00 WIB")
    
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    main()
    start_scheduler()
