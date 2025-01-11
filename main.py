import argparse
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

"""
To install and run:

python3 virtualenv env
source ./env/bin/activate
pip install -r requirements.txt
python main.py
"""

# Initialize the ChromeDriver with webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

driver.implicitly_wait(30)

def fetch_library_data(start_page=0):

    file_path = 'midcolumbialibraries.txt'

    base_url = "https://catalog.midcolumbialibraries.org/polaris/search/searchresults.aspx?ctx=1.1033.0.0.6&type=Keyword&term=*&by=ISBN&sort=MP&limit=TOM=bks&query=&page="
    total_pages = 3050  # Approximate total pages based on 100 results per page

    # Set up Selenium WebDriver (using Chrome)
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode

    # Change results per page to 100
    driver.get(base_url + "0")  # Load the first page

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "dropdownResultsPerPageTop"))
        )
        results_per_page_dropdown = driver.find_element(By.ID, "dropdownResultsPerPageTop")
        results_per_page_dropdown.click()  # Open the dropdown menu
        option_100 = results_per_page_dropdown.find_element(By.XPATH, "//option[@value='100']")
        option_100.click()  # Select the 100 results per page option
        # Wait for the page to reload with the new setting
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "searchResultsDIV"))
        )
    except Exception as e:
        print("Failed to set results per page to 100:", e)
        driver.quit()
        return
    
    for page in range(start_page, total_pages):
        print(f"Processing page {page + 1}/{total_pages}...")

        url = base_url + str(page)
        try:
            driver.get(url)
            WebDriverWait(driver, 45).until(
                EC.presence_of_element_located((By.ID, "searchResultsDIV"))
            ) # Allow time for the page to load
            search_results_div = driver.find_element(By.ID, "searchResultsDIV")
            if search_results_div:
                with open(file_path, 'a', encoding='utf-8') as file:
                    file.write(search_results_div.get_attribute('outerHTML'))
                    file.write("\n\n")
                print(f"Page {page + 1} saved.")
        except (selenium.common.exceptions.NoSuchElementException, TimeoutException) as e:
            print(f"ERROR fetching page {page + 1}: {e}")

    print("Fetching complete. File saved at:", file_path)
    driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch library data starting from a specific page.")
    parser.add_argument("--start_page", type=int, default=0, help="Page number to start fetching from (default: 0)")
    args = parser.parse_args()
    fetch_library_data(start_page=args.start_page)
