from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

import shutil

import subprocess

def get_attendance():
    print("--- Browser Environment (Docker) ---")
    
    # In our Docker setup, binaries are always here:
    chrome_path = "/usr/bin/chromium"
    driver_path = "/usr/bin/chromedriver"
    
    print(f"Target Chrome path: {chrome_path} (exists: {os.path.exists(chrome_path)})")
    print(f"Target Driver path: {driver_path} (exists: {os.path.exists(driver_path)})")
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    if os.path.exists(chrome_path):
        chrome_options.binary_location = chrome_path

    print("Initializing WebDriver...")
    try:
        # We explicitly provide the service with the driver path to bypass Selenium Manager
        service = Service(executable_path=driver_path) if os.path.exists(driver_path) else Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"WebDriver initialization failed: {e}")
        
        # Diagnostic: Try to extract path from error and run ldd
        error_str = str(e)
        if "Service" in error_str and "unexpectedly exited" in error_str:
            import re
            path_match = re.search(r'Service (.*) unexpectedly exited', error_str)
            if path_match:
                failing_driver = path_match.group(1)
                print(f"Failing driver: {failing_driver}")
                if os.path.exists(failing_driver):
                    print(f"Running ldd on {failing_driver}:")
                    try:
                        print(subprocess.check_output(["ldd", failing_driver], stderr=subprocess.STDOUT).decode())
                    except Exception as ldd_e:
                        print(ldd_e)
                        
        return f"❌ Error initializing browser: {e}"

    try:
        print("Opening portal...")
        driver.get("https://webprosindia.com/vignanit/")

        print("Entering username...")
        driver.find_element(By.ID, "txtId2").send_keys(os.getenv("PORTAL_USERNAME"))

        print("Entering password...")
        driver.find_element(By.ID, "txtPwd2").send_keys(os.getenv("PASSWORD"))

        print("Clicking login...")
        driver.find_element(By.ID, "imgBtn2").click()

        print("Waiting after login...")
        time.sleep(5)

        wait = WebDriverWait(driver, 15)

        # Click ATTENDANCE
        attendance_link = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "ATTENDANCE"))
        )
        attendance_link.click()

        # Switch to iframe
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "capIframe")))

        # Select radio
        wait.until(
            EC.element_to_be_clickable((By.ID, "radTillNow"))
        ).click()

        # Click show
        wait.until(
            EC.element_to_be_clickable((By.ID, "btnShow"))
        ).click()

        # Wait for attendance table
        wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "table")))

        tables = driver.find_elements(By.TAG_NAME, "table")
        table = tables[-1]  # Attendance table

        rows = table.find_elements(By.TAG_NAME, "tr")

        result = "📊 Attendance Summary\n\n"

        # Extract all rows except header and last row
        for row in rows[1:-1]:
            cols = row.find_elements(By.TAG_NAME, "td")

            if len(cols) >= 5:
                subject = cols[1].text.strip()
                percentage = cols[4].text.strip()   
                result += f"{subject} → {percentage}%\n"

        # Extract last row separately (Overall)
        last_row = rows[-1]
        last_cols = last_row.find_elements(By.TAG_NAME, "td")

        if len(last_cols) >= 1:
            overall_percentage = last_cols[-1].text.strip()
            result += "\n"
            result += f"🎯 Overall Attendance → {overall_percentage}%\n"
        return result

    except Exception as e:
        print("Error occurred:", e)
        return "❌ Error fetching attendance."

    finally:
        print("Closing browser...")
        driver.quit()