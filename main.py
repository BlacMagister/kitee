import json
import os
import random
import time
import requests
import sys
from datetime import datetime, timedelta, timezone
from colorama import init, Fore, Style
import concurrent.futures
import threading

# Inisialisasi Colorama
init(autoreset=True)

# Global lock untuk mengupdate file log dengan aman
log_lock = threading.Lock()

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
MAX_RETRIES = 3  # Jumlah maksimum percobaan ulang untuk permintaan yang gagal
TIMEOUT = 20  # Timeout untuk permintaan HTTP (dalam detik)
SLEEP_RANGE = (5, 10) # Rentang waktu tidur acak antara interaksi (dalam detik)
RATE_LIMIT_DELAY = 2 # Delay awal untuk rate limiting (dalam detik)
MAX_CONCURRENT_WALLETS = 5 # Jumlah wallet yang diproses secara bersamaan
MAX_CONCURRENT_AGENTS = 3 #Jumlah agent yang diproses secara bersamaan per wallet

# Fungsi untuk membaca daftar wallet dari file (1 address per baris)
def read_wallets():
    try:
        with open(akun_file, "r") as f:
            wallets = [line.strip() for line in f.readlines() if line.strip()]
        return wallets
    except FileNotFoundError:
        print(Fore.RED + f"⚠️ File {akun_file} tidak ditemukan! Harap buat file tersebut dengan daftar wallet.")
        sys.exit(1)

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

# Fungsi untuk mendapatkan tanggal hari ini berdasarkan WIB (format YYYY-MM-DD)
def get_today_date_wib():
    now_wib = datetime.now(timezone.utc) + timedelta(hours=7)
    return now_wib.strftime("%Y-%m-%d")

# Fungsi untuk mereset interaksi harian jika hari sudah berganti (WIB)
def check_and_reset_daily_interactions(log_data, wallet, wallet_index):
    today_wib = get_today_date_wib()
    if log_data.get(wallet, {}).get("date") != today_wib:
        print(Fore.YELLOW + f"⚠️ Hari baru dimulai! Mereset interaksi harian untuk akun ke-{wallet_index}: {wallet}.")
        log_data[wallet] = {
            "index": wallet_index,  # Menyimpan nomor urut wallet
            "date": today_wib,
            "dailyLimit": DEFAULT_DAILY_LIMIT,
            "interactions": {agent_id: 0 for agent_id in agents}
        }
    return log_data

# Fungsi untuk membaca pertanyaan acak berdasarkan topik
def get_random_questions_by_topic(file_path, topic, count):
    try:
        with open(file_path, "r") as f:
            questions = json.load(f)
        questions_list = questions.get(topic, [])
        if len(questions_list) < count:
            print(Fore.YELLOW + f"⚠️ Jumlah pertanyaan untuk topik {topic} kurang dari {count}. Menggunakan semua pertanyaan yang tersedia.")
            return questions_list.copy()
        return random.sample(questions_list, count)
    except FileNotFoundError:
        print(Fore.RED + f"⚠️ File {file_path} tidak ditemukan!")
        sys.exit(1)
    except json.JSONDecodeError:
        print(Fore.RED + f"⚠️ File {file_path} rusak. Pastikan ini adalah file JSON yang valid.")
        sys.exit(1)
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal membaca pertanyaan acak untuk topik {topic}: {e}")
        sys.exit(1)

# Fungsi untuk mengirim pertanyaan ke agent AI dengan retry dan rate limit handling
def send_question_to_agent(agent_id, question, retries=MAX_RETRIES):
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}

    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0].get("message", None)
            else:
                print(Fore.RED + f"⚠️ Format respons tidak sesuai dari agent {agent_id}: {data}")
                return None

        except requests.exceptions.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response else None
            if status == 429:  # Rate limit
                delay = RATE_LIMIT_DELAY ** (attempt + 1)
                print(Fore.YELLOW + f"⏳ Rate limit terdeteksi, retrying dalam {delay} detik... ({attempt + 1}/{retries})")
                time.sleep(delay)
            else:
                print(Fore.RED + f"⚠️ HTTP error saat mengirim pertanyaan ke agent {agent_id}: {http_err}")
                return None

        except requests.exceptions.Timeout as te:
            print(Fore.RED + f"⚠️ Timeout saat mengirim pertanyaan ke agent {agent_id}: {te}")
            if attempt < retries - 1:
                print(Fore.YELLOW + f"Retrying... ({attempt + 1}/{retries})")
                time.sleep(5)
            else:
                return None  # Give up after max retries

        except requests.exceptions.RequestException as re: #Catch broad exceptions
            print(Fore.RED + f"⚠️ Request error saat mengirim pertanyaan ke agent {agent_id}: {re}")
            return None

        except json.JSONDecodeError as json_err: #Handle JSON decoding errors
             print(Fore.RED + f"⚠️ JSON Decode error saat memproses response dari agent {agent_id}: {json_err}")
             return None

        except Exception as e:
            print(Fore.RED + f"⚠️ Error tak terduga saat mengirim pertanyaan ke agent {agent_id}: {e}")
            return None

    print(Fore.RED + f"⚠️ Gagal mengirim pertanyaan ke agent {agent_id} setelah {retries} percobaan.")
    return None

# Fungsi untuk melaporkan penggunaan dengan retry dan rate limit handling
def report_usage(wallet, options, retries=MAX_RETRIES):
    url = "https://quests-usage-dev.prod.zettablock.com/api/report_usage"
    payload = {
        "wallet_address": wallet,
        "agent_id": options["agent_id"],
        "request_text": options["question"],
        "response_text": options["response"],
        "request_metadata": {}
    }
    headers = {"Content-Type": "application/json"}

    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            print(Fore.YELLOW + f"✅ Data penggunaan untuk {wallet} berhasil dilaporkan!\n")
            return

        except requests.exceptions.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response else None
            if status == 429:
                delay = RATE_LIMIT_DELAY ** (attempt + 1)
                print(Fore.YELLOW + f"⏳ Rate limit terdeteksi, retrying dalam {delay} detik... ({attempt + 1}/{retries})")
                time.sleep(delay)
            else:
                print(Fore.RED + f"⚠️ Gagal melaporkan penggunaan untuk {wallet}: {http_err}\n")
                return

        except requests.exceptions.RequestException as re:  # catch broad exception
            print(Fore.RED + f"⚠️ Request error saat melaporkan penggunaan untuk {wallet}: {re}")
            return

        except Exception as e:
            print(Fore.RED + f"⚠️ Gagal melaporkan penggunaan untuk {wallet}: {e}\n")
            return

    print(Fore.RED + f"⚠️ Gagal melaporkan penggunaan untuk {wallet} setelah {retries} percobaan.")

# Fungsi yang memproses interaksi untuk satu agent secara concurrent
def process_agent_interactions(agent_id, agent_info, wallet, questions, interaction_log):
    agent_name = agent_info["name"]
    print(Fore.CYAN + f"\n🤖 Memproses Agent: {agent_name} untuk {wallet} (concurrent)")

    # Periksa batas interaksi harian
    if interaction_log[wallet]["interactions"][agent_id] >= DEFAULT_DAILY_LIMIT:
        print(Fore.YELLOW + f"⚠️ Batas interaksi harian untuk {agent_name} sudah tercapai ({DEFAULT_DAILY_LIMIT}x) untuk {wallet}.")
        return

    remaining_interactions = DEFAULT_DAILY_LIMIT - interaction_log[wallet]["interactions"][agent_id]
    
    for _ in range(remaining_interactions):
        if not questions:
            print(Fore.YELLOW + f"⚠️ Tidak ada pertanyaan tersisa untuk topik {agent_info['topic']} untuk {wallet}.")
            break
        
        question = questions.pop()
        print(Fore.YELLOW + f"❓ Pertanyaan untuk {agent_name} untuk {wallet}: {question}")
        
        response = send_question_to_agent(agent_id, question)
        
        if response is None:
            print(Fore.RED + f"⚠️ Tidak menerima respons dari {agent_name} untuk pertanyaan: {question} untuk {wallet}")
            continue  # Skip melaporkan penggunaan jika tidak ada respons
            
        response_text = response if response else "Tidak ada jawaban"
        if isinstance(response_text, dict):
            response_text = response_text.get("content", "Tidak ada jawaban")
        
        print(Fore.GREEN + f"💡 Jawaban dari {agent_name} untuk {wallet}: {response_text}")
        
        report_usage(wallet.lower(), {
            "agent_id": agent_id,
            "question": question,
            "response": response_text
        })
        
        with log_lock:
            interaction_log[wallet]["interactions"][agent_id] += 1
            save_interaction_log(interaction_log)
        
        time.sleep(random.randint(*SLEEP_RANGE)) # Use SLEEP_RANGE tuple

# Fungsi untuk memproses satu wallet
def process_wallet(wallet, index, interaction_log):
    print(Fore.MAGENTA + f"\n🔑 Memproses akun ke-{index}: {wallet}")
    interaction_log = check_and_reset_daily_interactions(interaction_log, wallet, index)
    save_interaction_log(interaction_log)

    # Ambil pertanyaan acak dari file random_questions.json per topik untuk masing-masing agent
    random_questions_by_topic_dict = {}
    for agent_id, agent_info in agents.items():
        topic = agent_info["topic"]
        random_questions_by_topic_dict[agent_id] = get_random_questions_by_topic(random_questions_file, topic, DEFAULT_DAILY_LIMIT)

    # Jalankan interaksi untuk ketiga agent secara concurrent
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_AGENTS) as executor:
        futures = []
        for agent_id, agent_info in agents.items():
            #Create a copy of the question list for each thread to prevent race conditions
            question_list_copy = random_questions_by_topic_dict[agent_id].copy()
            futures.append(
                executor.submit(
                    process_agent_interactions,
                    agent_id,
                    agent_info,
                    wallet,
                    question_list_copy,
                    interaction_log
                )
            )
        # Tunggu hingga semua thread selesai
        for future in concurrent.futures.as_completed(futures):
            future.result()

# Fungsi utama
def main():
    print(Fore.CYAN + "🚀 Kite AI - Multi Account Daily Interaction 🚀")
    print(Fore.CYAN + "----------------------------------------")
    
    # Pastikan file random_questions.json ada, jika tidak buat file tersebut
    if not os.path.exists(random_questions_file):
        print(Fore.YELLOW + "⚠️ File random_questions.json tidak ditemukan. Membuat file baru...")
        try:
            os.system(f"{sys.executable} rand.py")
            print(Fore.GREEN + "✅ File random_questions.json berhasil dibuat.")
        except Exception as e:
            print(Fore.RED + f"⚠️ Gagal menjalankan rand.py: {e}")
            sys.exit(1) #Exit sys instead of exit
    
    while True:
        wallets = read_wallets()
        print(Fore.BLUE + f"📌 Ditemukan {len(wallets)} akun dalam {akun_file}\n")
        
        # Baca data interaksi harian
        interaction_log = read_interaction_log()

        # Proses wallet secara concurrent dengan batasan MAX_CONCURRENT_WALLETS
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WALLETS) as executor:
            futures = []
            for index, wallet in enumerate(wallets, start=1):
                futures.append(
                    executor.submit(
                        process_wallet,
                        wallet,
                        index,
                        interaction_log
                    )
                )

            # Tunggu hingga semua wallet selesai diproses
            for future in concurrent.futures.as_completed(futures):
                future.result()
        
        print(Fore.GREEN + "\n🎉 Sesi selesai! Menunggu hingga ±08:00 WIB untuk interaksi berikutnya...\n")
        
        # Hitung waktu hingga reset harian (08:00 WIB)
        now_wib = datetime.now(timezone.utc) + timedelta(hours=7)
        next_reset_wib = now_wib.replace(hour=8, minute=0, second=0, microsecond=0)
        if next_reset_wib <= now_wib:
            next_reset_wib += timedelta(days=1)
        time_until_reset = (next_reset_wib - now_wib).total_seconds()
        print(Fore.BLUE + f"⏰ Waktu hingga reset harian: {int(time_until_reset)} detik")
        
        time.sleep(time_until_reset)

if __name__ == "__main__":
    main()
