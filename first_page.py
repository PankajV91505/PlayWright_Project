import csv
import os
import requests
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

class BiharElectionScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        self.output_file = f"bihar_election_data_{timestamp}.csv"
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        self.ensure_csv_exists()

    def ensure_csv_exists(self):
        if not Path(self.output_file).exists():
            with open(self.output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "District", "Post", "NagarNikay", "WardNo", "ReservationStatus",
                    "CandidateName", "GuardianName", "Gender", "Age", "Category",
                    "Address", "MobileNo", "CandidatePhotoFile", "AffidavitFile"
                ])

    def start_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch(headless=self.headless)
        self.context = self.browser.new_context(accept_downloads=True)
        self.page = self.context.new_page()

    def navigate(self):
        self.page.goto("https://sec.bihar.gov.in/")
        self.page.wait_for_timeout(3000)
        self.page.locator("//button[span[contains(@class, 'fa fa-bars')]]").click()
        self.page.wait_for_timeout(3000)
        self.page.goto("http://sec2021.bihar.gov.in/SEC_NP_P4_01/Admin/winningCandidatesPost_wise.aspx")
        self.page.wait_for_timeout(3000)

    def get_select_options(self, selector):
        options = self.page.locator(selector).locator("option")
        count = options.count()
        values = []
        for i in range(1, count):  # skip the first one ("Select")
            value = options.nth(i).get_attribute("value")
            text = options.nth(i).inner_text()
            values.append((value, text))
        return values

    def select_combination_and_submit(self, district_val, post_val):
        self.page.select_option('select#ddlDistrict', value=district_val)
        self.page.wait_for_timeout(2000)
        self.page.select_option('select#ddlPosts', value=post_val)
        self.page.wait_for_timeout(1000)
        self.page.click("button.btnshow")
        self.page.wait_for_timeout(3000)

    def download_file(self, url, filename):
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded: {filename}")
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")

    def extract_table_data(self, district, post):
        self.page.wait_for_selector("table.table-bordered", timeout=5000)
        table = self.page.locator("table.table-bordered")

        if not table.is_visible():
            print("⛔ Table not visible, skipping...")
            return

        rows = table.locator("tbody tr")
        for i in range(rows.count()):
            cols = rows.nth(i).locator("td")
            if cols.count() < 15:
                continue

            post_name = cols.nth(1).inner_text().strip()
            district_name = cols.nth(2).inner_text().strip()
            nagarnikay = cols.nth(3).inner_text().strip()
            wardno = cols.nth(4).inner_text().strip()
            reservation_status = cols.nth(5).inner_text().strip()
            candidate_name = cols.nth(6).inner_text().strip()
            guardian_name = cols.nth(7).inner_text().strip()
            gender = cols.nth(8).inner_text().strip()
            age = cols.nth(9).inner_text().strip()
            category = cols.nth(10).inner_text().strip()
            address = cols.nth(11).inner_text().strip()
            mobile_no = cols.nth(12).inner_text().strip()

            # Extract Photo and Affidavit
            photo_url = cols.nth(13).locator("img").get_attribute("src") if cols.nth(13).locator("img").count() > 0 else ""
            affidavit_url = cols.nth(14).locator("a").get_attribute("href") if cols.nth(14).locator("a").count() > 0 else ""

            photo_filename = ""
            affidavit_filename = ""

            # Download Photo
            if photo_url:
                photo_filename = os.path.join(self.download_dir, f"{candidate_name.replace('/', '_')}_photo.jpg")
                self.download_file(photo_url, photo_filename)

            # Download Affidavit PDF
            if affidavit_url:
                affidavit_filename = os.path.join(self.download_dir, f"{candidate_name.replace('/', '_')}_affidavit.pdf")
                self.download_file(affidavit_url, affidavit_filename)

            # Save to CSV
            with open(self.output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    district_name, post_name, nagarnikay, wardno, reservation_status,
                    candidate_name, guardian_name, gender, age, category,
                    address, mobile_no, photo_filename, affidavit_filename
                ])

    def run_all_combinations(self):
        try:
            self.navigate()

            districts = self.get_select_options('select#ddlDistrict')
            posts = self.get_select_options('select#ddlPosts')

            for d_val, d_text in districts:
                self.page.select_option('select#ddlDistrict', value=d_val)
                self.page.wait_for_timeout(1500)

                for p_val, p_text in posts:
                    print(f"\n▶️ Scraping for District: {d_text}, Post: {p_text}")
                    self.select_combination_and_submit(d_val, p_val)
                    try:
                        self.extract_table_data(d_text, p_text)
                    except Exception as e:
                        print(f"❌ Error while extracting table: {e}")

        except Exception as e:
            print(f"❌ Fatal Error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

# Usage
if __name__ == "__main__":
    scraper = BiharElectionScraper(headless=False)
    scraper.start_browser()
    scraper.run_all_combinations()
