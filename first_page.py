import csv
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

class BiharElectionScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.output_file = "bihar_election_data.csv"
        self.ensure_csv_exists()

    def ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist."""
        if not Path(self.output_file).exists():
            with open(self.output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["District", "Post", "Name", "Party", "Ward", "PDF_URL"])

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
        """Get dropdown option values and texts"""
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

    def extract_table_data(self, district, post):
        table = self.page.locator("table.table-bordered")
        if not table.is_visible():
            print("⛔ Table not visible, skipping...")
            return

        rows = table.locator("tbody tr")
        for i in range(rows.count()):
            cols = rows.nth(i).locator("td")
            if cols.count() < 4:
                continue
            name = cols.nth(0).inner_text()
            party = cols.nth(1).inner_text()
            ward = cols.nth(2).inner_text()
            pdf_link_tag = cols.nth(3).locator("a")
            pdf_url = pdf_link_tag.get_attribute("href") if pdf_link_tag.count() > 0 else ""

            # Save to CSV
            with open(self.output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([district, post, name, party, ward, pdf_url])

            # Download PDF
            if pdf_url:
                self.download_pdf(pdf_url, name)

    def download_pdf(self, url, name):
        try:
            download = self.page.wait_for_event("download", timeout=10000)
            self.page.locator(f'a[href="{url}"]').click()
            dl = download.value
            dl.save_as(f"downloads/{name.replace('/', '_')}.pdf")
        except Exception as e:
            print(f"⚠️ PDF download failed for {name}: {e}")

    def run_all_combinations(self):
        try:
            self.navigate()
            os.makedirs("downloads", exist_ok=True)

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
