import os
import re
import time
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')

    try:
        driver = webdriver.Chrome(service=service, options=options)
    finally:
        sys.stderr.close()
        sys.stderr = old_stderr

    try:
        driver.set_page_load_timeout(20)
        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tr"))
            )
        except:
            driver.quit()
            print(f"⚠️  Skipped (no table found on page): {url}")
            return None, "no_data"

        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
        if len(rows) <= 1:
            driver.quit()
            print(f"⚠️  Skipped (table had only headers or was empty): {url}")
            return None, "no_data"

        data = []
        capture_date, capture_time = extract_capture_date(url)
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
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
            print(f"⚠️  Skipped (rows found but no valid data): {url}")
            return None, "no_data"

        df = pd.DataFrame(data)
        return df, "success"
    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        print(f"❌ Exception for URL {url}: {e}")
        return None, "exception"

def scrape_and_save_with_retry(url, retries=3, base_delay=60):
    for attempt in range(1, retries + 1):
        df, status = scrape_and_save(url)
        if status in ("success", "no_data"):
            return df, status
        delay = base_delay * (2 ** (attempt - 1))
        print(f"🔁 Retry {attempt}/{retries} for {url} in {delay}s...")
        time.sleep(delay)
    return None, "exception"

def print_summary(success_log, nodata_log, exception_log, duration_seconds):
    duration_minutes = duration_seconds / 60
    print("\n" + "=" * 60)
    print("📋 Scrape Summary")
    print("=" * 60)
    for msg in nodata_log:
        print(msg)
    for msg in exception_log:
        print(msg)
    for msg in success_log:
        print(msg)

    print(f"\n✅   Success Count: {len(success_log)}")
    print(f"⚠️    No Data Count: {len(nodata_log)}")
    print(f"❌   Exception Count: {len(exception_log)}")
    print(f"\n⏱️  Total scraping duration: {duration_seconds:.2f} seconds | {duration_minutes:.2f} mins\n")

def save_all_with_threads(url_list, max_threads=2, retries=3, append_df=None):
    all_dfs = [] if append_df is None else [append_df]
    exception_urls = []
    nodata_urls = []

    success_log = []
    exception_log = []
    nodata_log = []

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(scrape_and_save_with_retry, url, retries=retries): url for url in url_list}
        for future in as_completed(futures):
            url = futures[future]
            df, status = future.result()

            if status == "success":
                all_dfs.append(df)
                success_log.append(f"✅ Success: {url}")
            elif status == "no_data":
                nodata_urls.append(url)
                nodata_log.append(f"⚠️  No valid data found for: {url}")
            elif status == "exception":
                exception_urls.append(url)
                exception_log.append(f"❌ Exception occurred while scraping: {url}")

    if all_dfs:
        merged = pd.concat(all_dfs, ignore_index=True)
    else:
        merged = None

    return merged, exception_urls, nodata_urls, success_log, exception_log, nodata_log

def clear_log_files():
    open("nodata_urls.txt", "w").close()
    open("exception_urls.txt", "w").close()

if __name__ == "__main__":
    clear_log_files()

    with open("input_urls.txt", "r") as file:
        eci_urls = [line.strip() for line in file if line.strip()]

    print("➡️  Starting initial scrape pass...")
    start_time = time.time()
    master_df, exceptions, nodata, success_log, exception_log, nodata_log = save_all_with_threads(
        eci_urls, max_threads=4, retries=3
    )
    duration = time.time() - start_time

    print_summary(success_log, nodata_log, exception_log, duration)

    if master_df is not None:
        master_df.to_csv("eci_master.csv", index=False)
        print(f"📦 Initial scrape data saved to eci_master.csv")

    with open("exception_urls.txt", "w") as f:
        for url in exceptions:
            f.write(url + "\n")

    with open("nodata_urls.txt", "w") as f:
        for url in nodata:
            f.write(url + "\n")

    if exceptions:
        print("\n➡️  Retrying exception URLs up to 3 times each (no delays)...")
        def retry_scrape(url, max_attempts=3):
            for attempt in range(max_attempts):
                df, status = scrape_and_save(url)
                if status == "success" or status == "no_data":
                    return df, status
            return None, "exception"

        retry_dfs = []
        still_exceptions = []
        still_nodata = []

        retry_success_log = []
        retry_exception_log = []
        retry_nodata_log = []

        start_retry = time.time()
        for url in exceptions:
            df, status = retry_scrape(url)
            if status == "success":
                retry_dfs.append(df)
                retry_success_log.append(f"✅ Retry success: {url}")
            elif status == "no_data":
                still_nodata.append(url)
                retry_nodata_log.append(f"⚠️ Retry no data: {url}")
            else:
                still_exceptions.append(url)
                retry_exception_log.append(f"❌ Retry exception: {url}")
        retry_duration = time.time() - start_retry

        if retry_dfs:
            retry_merged = pd.concat(retry_dfs, ignore_index=True)
            if master_df is not None:
                master_df = pd.concat([master_df, retry_merged], ignore_index=True)
            else:
                master_df = retry_merged
            master_df.to_csv("eci_master.csv", index=False)
            print(f"📦 Updated eci_master.csv with retry successes")

        print_summary(retry_success_log, retry_nodata_log, retry_exception_log, retry_duration)

        with open("exception_urls.txt", "w") as f:
            for url in still_exceptions:
                f.write(url + "\n")

        with open("nodata_urls.txt", "w") as f:
            for url in nodata + still_nodata:
                f.write(url + "\n")

    print("\n🎉 Scraping complete.")
