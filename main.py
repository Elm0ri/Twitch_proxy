import random
import streamlink
import threading
import time
import requests
from selenium import webdriver
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from threading import Lock


proxy_list = [
    ("104.250.204.146", 6237, "nekosbot", "5tapegalob53"),
    
]


selenium_initialized = False
fake_viewer_count = 0
viewer_count_lock = Lock()
active_threads = []

def get_stream_url(channel_name):
    try:
        streams = streamlink.streams(f'twitch.tv/{channel_name}')
        if streams:
            return streams['worst'].url
        else:
            return None
    except Exception as e:
        print(f"Errore durante l'ottenimento dell'URL dello stream: {e}")
        return None

def check_streamer_status(channel_name):
    try:
        url = f"https://www.twitch.tv/{channel_name}"

        response = requests.get(url)

        if response.status_code == 200:
            if "channel offline" in response.text.lower():
                return False
            else:
                return True
        else:
            print(f"Errore nella verifica dello stato dello streamer: {response.status_code}")
            return False

    except Exception as e:
        print(f"Errore nella verifica dello stato dello streamer: {e}")
        return False

def real_viewer_function(channel_name):
    global selenium_initialized

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        stream_url = get_stream_url(channel_name)
        if stream_url:
            driver.get(stream_url)
            print(f"Spettatore reale inizializzato per {channel_name}")

            start_time = time.time()
            duration = random.randint(900, 1500)  # Durata casuale tra 15 e 25 minuti
            elapsed_time = 0

            while elapsed_time < duration:
                if not check_streamer_status(channel_name):
                    print("Lo streamer ha interrotto lo streaming.")
                    break

                time.sleep(30)  # Controllo ogni 30 secondi

                elapsed_time = time.time() - start_time

            driver.quit()
            print(f"Spettatore reale terminato per {channel_name}. Durata: {elapsed_time} secondi")

        else:
            print("Impossibile ottenere l'URL dello stream.")

    except Exception as e:
        print(f"Errore durante l'esecuzione dello spettatore reale: {e}")

    finally:
        selenium_initialized = True

def change_proxy():
    global proxy_list

    while True:
        time.sleep(300)  # Cambia il proxy ogni 5 minuti
        proxy = random.choice(proxy_list)
        print(f"Cambiato il proxy a {proxy[0]}:{proxy[1]}")


def safe_request(url, proxies=None, headers=None):
    retries = 3
    for i in range(retries):
        try:
            response = requests.get(url, proxies=proxies, headers=headers, timeout=60)
            return response
        except requests.RequestException:
            time.sleep(2**i)  # Backoff esponenziale
    return None

def increase_viewers(channel_name, proxy, duration):
    global fake_viewer_count, active_threads

    ua = UserAgent()
    headers = {'User-Agent': ua.random}

    try:
        while True:
            if not check_streamer_status(channel_name):
                print("Lo streamer ha interrotto lo streaming.")
                return

            stream_url = get_stream_url(channel_name)
            if not stream_url:
                print("Impossibile ottenere l'URL dello stream.")
                return

            proxies = {
                "http": f"http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}",
                "https": f"http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
            }

            response = safe_request(stream_url, proxies=proxies, headers=headers)
            if response and response.status_code == 200:
                with viewer_count_lock:
                    fake_viewer_count += 1
                print(f"Spettatore fittizio utilizzando il proxy {proxy[0]}:{proxy[1]}")
                time.sleep(60)
            else:
                print(f"Impossibile inviare la visualizzazione al flusso video tramite il proxy {proxy[0]}:{proxy[1]}.")
                break

    except Exception as e:
        print(f"Errore durante l'aumento degli spettatori: {e}")
    finally:
        with viewer_count_lock:
            if threading.current_thread() in active_threads:
                    active_threads.remove(threading.current_thread())
            

def increase_viewers_with_proxies_and_real(channel_name, num_fake_viewers, num_threads):
    global fake_viewer_count

    if check_streamer_status(channel_name):
        duration = random.randint(600, 900)  # Durata casuale tra 10 e 15 minuti

        proxy_thread = threading.Thread(target=change_proxy)
        proxy_thread.start()

        for _ in range(num_threads):
            proxy = random.choice(proxy_list)

            for _ in range(num_fake_viewers // num_threads):
                viewer_thread = threading.Thread(target=increase_viewers, args=(channel_name, proxy, duration))
                viewer_thread.start()

        while fake_viewer_count < num_fake_viewers:
            time.sleep(1)

        for _ in range(num_fake_viewers):
            while not selenium_initialized:
                time.sleep(1)

            real_viewer_thread = threading.Thread(target=real_viewer_function, args=(channel_name,))
            real_viewer_thread.start()

    else:
        print("Lo streamer non è online.")


def monitor_and_adjust_viewers(target_viewers, channel_name):
    global fake_viewer_count, active_threads
    while True:
        with viewer_count_lock:
            current_viewers = fake_viewer_count
            additional_viewers = target_viewers - current_viewers

        for _ in range(additional_viewers):
            if len(active_threads) < target_viewers:
                proxy = random.choice(proxy_list)
                viewer_thread = threading.Thread(target=increase_viewers, args=(channel_name, proxy, 600))
                viewer_thread.start()
                with viewer_count_lock:
                    active_threads.append(viewer_thread)

        time.sleep(60)  # Controlla ogni minuto

if __name__ == '__main__':
    channel_name = "justallyson_"
    try:
        num_fake_viewers = int(input("Inserisci il numero di spettatori fittizi da inviare: "))
        num_threads = int(input("Inserisci il numero di thread da utilizzare: "))

        if check_streamer_status(channel_name):
            monitor_thread = threading.Thread(target=monitor_and_adjust_viewers, args=(num_fake_viewers, channel_name))
            monitor_thread.start()
            increase_viewers_with_proxies_and_real(channel_name, num_fake_viewers, num_threads)
        else:
            print("Lo streamer non è online.")

    except ValueError:
        print("Inserisci un numero valido.")
