import os
import re
import time
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sys

def extract_capture_date(url):
    match = re.search(r'/web/(\d{14})/', url)
    if match:
        timestamp = match.group(1)
        dt = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H-%M-%S")
    return "unknown_date", "unknown_time"

def scrape_and_save(url):
    os.environ['GOOGLE_API_CPP_LOG_LEVEL'] = '3'
    os.environ['CHROME_LOG_FILE'] = os.devnull

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-logging')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-features=VoiceAudioCapture,VoiceDetection,AudioServiceAudioStreams")
    options.add_argument("--enable-unsafe-swiftshader")

    service = Service(log_path=os.devnull)

    # Silence native ChromeDriver stderr messages
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')

    try:
        driver = webdriver.Chrome(service=service, options=options)
    finally:
        sys.stderr.close()
        sys.stderr = old_stderr

    try:
        driver.get(url)
        time.sleep(5)
        rows = driver.find_elements("css selector", "table tr")

        data = []
        capture_date, capture_time = extract_capture_date(url)
        for row in rows[1:]:
            cols = row.find_elements("tag name", "td")
            if len(cols) != 4:
                continue
            data.append({
                "capture_date": capture_date,
                "GMT_capture_time": capture_time,
                "Country": cols[0].text.strip(),
                "Statements of Support": cols[1].text.strip().replace(',', ''),
                "Threshold": cols[2].text.strip().replace(',', ''),
                "Percentage": cols[3].text.strip().replace('%', ''),
            })

        driver.quit()
        if not data:
            return None, "no_data"

        df = pd.DataFrame(data)
        return df, "success"
    except Exception:
        driver.quit()
        return None, "exception"

def save_all_with_threads(url_list, max_threads=3):
    all_dfs = []
    failed_urls = []

    success_log = []
    fail_log = []
    nodata_log = []

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(scrape_and_save, url): url for url in url_list}
        for future in as_completed(futures):
            original_url = futures[future]
            df, status = future.result()

            if status == "success":
                all_dfs.append(df)
                success_log.append(f"✅ Success: {original_url}")
            elif status == "no_data":
                failed_urls.append(original_url)
                nodata_log.append(f"⚠️  No valid data found for: {original_url}")
            elif status == "exception":
                failed_urls.append(original_url)
                fail_log.append(f"❌ Exception occurred while scraping: {original_url}")

    # Print organized logs
    print("\n" + "=" * 60)
    print("📋 Scrape Summary")
    print("=" * 60)
    for msg in nodata_log:
        print(msg)
    for msg in fail_log:
        print(msg)
    for msg in success_log:
        print(msg)

    # Save master dataset only if we got any data
    if all_dfs:
        merged = pd.concat(all_dfs, ignore_index=True)
        merged_path = "eci_master.csv"
        merged.to_csv(merged_path, index=False)
        print(f"\n📦 Master dataset successfully saved to {merged_path}")

    # Save failed URLs if any
    if failed_urls:
        fail_path = "failed_urls.txt"
        with open(fail_path, "w") as f:
            for url in failed_urls:
                f.write(url + "\n")
        print(f"⚠️  Failed URLs written to {fail_path}\n")

# Example URLs
eci_urls = [
    "https://web.archive.org/web/20250627115346/https://citizens-initiative.europa.eu/initiatives/details/2024/000007_en",
    "https://web.archive.org/web/20250627163823/https://citizens-initiative.europa.eu/initiatives/details/2024/000007_en",
    "https://youtube.com"
]

save_all_with_threads(eci_urls, max_threads=3)
