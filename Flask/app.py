from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from discordwebhook import Discord
import time
import sys
import schedule
import threading

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def start():
    course_code = request.form.get("course_code")
    course_number = request.form.get("course_number")
    discord_webhook = request.form.get("discord_webhook")
    Term = request.form.get("term")

    schedule.every(30).seconds.do(
        run_script, course_code, course_number, discord_webhook, Term
    )

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    t = threading.Thread(target=run_schedule)
    t.start()

    return render_template("submit.html")


def run_script(course_code, course_number, discord_webhook, Term):
    discord = Discord(url=discord_webhook)

    driver_service = Service("./chromedriver.exe")

    options = Options()

    options.add_argument("--headless")
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=driver_service, options=options)

    printcount = 0

    url = (
        "https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-course&dept="
        + course_code
        + "&course="
        + course_number
    )

    driver.get(url)

    table_locator = (By.CLASS_NAME, "section-summary")
    wait = WebDriverWait(driver, 10)
    table = wait.until(EC.visibility_of_element_located(table_locator))

    rows = table.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        columns = row.find_elements(By.TAG_NAME, "td")

        if len(columns) >= 5:
            status = columns[0].text.strip()
            section = columns[1].text.strip()
            type = columns[2].text.strip()
            term = columns[3].text.strip()
            days = columns[6].text.strip()
            time = columns[7].text.strip() + " - " + columns[8].text.strip()

            if term == Term and type == "Lecture" and status == "":
                printcount += 1

                discord.post(content="Section: " + section)
                discord.post(content="Type: " + type)
                discord.post(content="Term: " + term)
                discord.post(content="Days: " + days)
                discord.post(content="Time: " + time)
                discord.post(content="-----------------------------------")

    if printcount > 0:
        discord.post(
            content="\n\nSEAT AVAILABLE FOR " + course_code + " " + course_number
        )
        discord.post(content="-----------------------------------")

        exit_program()


def exit_program():
    sys.exit(0)


if __name__ == "__main__":
    app.run(debug=True)
