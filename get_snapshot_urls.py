import time
from datetime import datetime
import re
import os
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

def get_wayback_links(calendar_url, results, index, all_failed_days, all_mismatch_days):
    label = f"[Thread-{index}]"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-features=VoiceAudioCapture,VoiceDetection,AudioServiceAudioStreams")
    options.add_argument("--enable-unsafe-swiftshader")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-logging')

    service = Service(log_path=os.devnull)
    driver = webdriver.Chrome(options=options, service=service)

    failed_days = []
    mismatch_days = []

    try:
        print(f"\n{label} 🔄 Opening: {calendar_url}")
        driver.get(calendar_url)
        time.sleep(5)

        urls = set()
        actions = ActionChains(driver)

        calendar_days = driver.find_elements(By.CLASS_NAME, "calendar-day")
        total_days = len(calendar_days)
        max_retries = 3

        for i in range(total_days):
            retries = 0
            full_date_str = None  # Reset for each day

            while retries < max_retries:
                try:
                    calendar_days = driver.find_elements(By.CLASS_NAME, "calendar-day")
                    time.sleep(0.5)
                    if len(calendar_days) != total_days:
                        print(f"{label} ⚠️  Warning: day count changed during iteration.")
                    day = calendar_days[i]

                    fallback_date = f"Index {i} (label={day.text})"

                    if total_days > 1 and i < total_days // 2 and i != total_days - 1:
                        try:
                            actions.move_to_element(calendar_days[-1]).perform()
                            time.sleep(2)
                        except Exception:
                            pass
                    elif total_days > 1 and i >= total_days // 2 and i != 0:
                        try:
                            actions.move_to_element(calendar_days[0]).perform()
                            time.sleep(2)
                        except Exception:
                            pass

                    try:
                        actions.move_to_element(day).perform()
                    except StaleElementReferenceException:
                        retries += 1
                        print(f"{label} ⚠️  Stale hover element, retrying {fallback_date} (attempt {retries})")
                        time.sleep(1)
                        continue

                    try:
                        popup = WebDriverWait(driver, 6).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "popup-of-day-content"))
                        )
                    except TimeoutException:
                        print(f"{label} ⚠️  Popup did not appear for {fallback_date}, skipping")
                        full_date_str = fallback_date
                        break

                    time.sleep(2)

                    try:
                        header_text = popup.find_element(By.CLASS_NAME, "day-tooltip-title").text
                        import datetime
                        dt = datetime.datetime.strptime(header_text, "%B %d, %Y")
                        date_str = dt.strftime("%Y-%m-%d")
                        full_date_str = dt.strftime("%b %d, %Y")
                    except Exception:
                        full_date_str = fallback_date
                        date_str = fallback_date

                    print(f"{label} 🖱️  Hovering on {full_date_str}")

                    try:
                        tooltip_subtitle = popup.find_element(By.CLASS_NAME, "day-tooltip-subtitle").text
                        import re
                        m = re.search(r"(\d+)\s+snapshot", tooltip_subtitle)
                        expected_snapshots = int(m.group(1)) if m else 0
                    except Exception:
                        expected_snapshots = 0

                    try:
                        scrollable_div = popup.find_element(By.CSS_SELECTOR, "ul.day-tooltip-shapshot-list > div > div")
                    except Exception:
                        print(f"{label} ⚠️  Scroll container not found for {full_date_str}, skipping")
                        break

                    last_height = -1
                    scroll_pos = 0
                    step = 50
                    while True:
                        scroll_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                        if scroll_height == last_height:
                            break
                        last_height = scroll_height
                        while scroll_pos < scroll_height:
                            driver.execute_script(f"arguments[0].scrollTop = {scroll_pos}", scrollable_div)
                            time.sleep(0.15)
                            scroll_pos += step
                        scroll_pos = 0

                    snapshot_links = scrollable_div.find_elements(By.TAG_NAME, "a")
                    found_count = len(snapshot_links)

                    for link in snapshot_links:
                        href = link.get_attribute("href")
                        if href and "citizens-initiative.europa.eu" in href:
                            if href.startswith("/web/"):
                                href = "https://web.archive.org" + href
                            urls.add(href)

                    if found_count != expected_snapshots:
                        print(f"{label} 🗓️  {full_date_str}: Found {found_count} snapshots (expected {expected_snapshots})")
                        retries += 1
                        if retries >= max_retries:
                            mismatch_days.append(f"{full_date_str} ({found_count} vs {expected_snapshots})")
                        time.sleep(1)
                        continue

                    time.sleep(0.3)
                    break

                except StaleElementReferenceException:
                    retries += 1
                    print(f"{label} ⚠️  Stale element during processing, retrying {fallback_date} (attempt {retries})")
                    time.sleep(1)

                except Exception as e:
                    print(f"{label} ⚠️  Error processing {fallback_date}: {e}")
                    break

            else:
                print(f"{label} ⚠️  Failed to process {full_date_str or fallback_date} after {max_retries} retries")
                failed_days.append(full_date_str or fallback_date)

        results[index] = urls

    finally:
        driver.quit()

    all_failed_days.extend(failed_days)
    all_mismatch_days.extend(mismatch_days)

calendar_urls = [
    "https://web.archive.org/web/20240101000000*/https://citizens-initiative.europa.eu/initiatives/details/2024/000007_en",
    "https://web.archive.org/web/20250101000000*/https://citizens-initiative.europa.eu/initiatives/details/2024/000007_en"
]

results = [set(), set()]
all_failed_days = []
all_mismatch_days = []

start_time = time.time()

threads = []
for i, url in enumerate(calendar_urls):
    thread = threading.Thread(target=get_wayback_links, args=(url, results, i, all_failed_days, all_mismatch_days))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

all_urls = set()
for url_set in results:
    all_urls.update(url_set)

unique_urls = sorted(all_urls)
date_pattern = re.compile(r"/web/(\d{8})")
date_list = []

for url in unique_urls:
    match = date_pattern.search(url)
    if match:
        date_str = match.group(1)
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            date_list.append(dt)
        except ValueError:
            continue

# Default name in case no dates were found
filename = "wayback_snapshot_urls.txt"

# If dates found, create descriptive filename
if date_list:
    start_date = min(date_list).strftime("%Y-%m-%d")
    end_date = max(date_list).strftime("%Y-%m-%d")
    filename = f"snapshotLinks_{start_date}_to_{end_date}.txt"

# Save to descriptive file
with open(filename, "w") as f:
    for url in unique_urls:
        f.write(url + "\n")

end_time = time.time()
duration = end_time - start_time
minutes = int(duration // 60)
seconds = int(duration % 60)

print(f"\n⏱️ Total scraping duration: {minutes} minutes {seconds} seconds")
print(f"\n📦 Total unique snapshots collected: {len(unique_urls)}")
print("📁 Saved to wayback_snapshot_urls.txt")

if all_failed_days or all_mismatch_days:
    print("\n🔍 Dates to double check:")

if all_failed_days:
    print("❌ Failed to process after all retries:")
    for d in all_failed_days:
        print(f"   - {d}")

if all_mismatch_days:
    print("⚠️  Snapshot count mismatches:")
    for d in all_mismatch_days:
        print(f"   - {d}")
