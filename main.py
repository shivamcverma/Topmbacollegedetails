from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
# from selenium.common.exceptions.TimeoutException

import json, time
from webdriver_manager.chrome import ChromeDriverManager
import re

COLLEGE_INFO_URL ="https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307"
COURSES_URL = "https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/courses"
FEES_URL = "https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/fees"
REVIEWS_URL = "https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/reviews"
ADMISSION_URL = "https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/admission"
PLACEMENT_URL = "https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/placement"
CUTOFF_URL = "https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/cutoff"
RANKING_URL="https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/ranking"
GALLARY_URL="https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/gallery"
HOTEL_CAMPUS_URL="https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/infrastructure"




# ---------------- DRIVER ----------------
def create_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )



def scrape_college_info(driver):
    driver.get(COLLEGE_INFO_URL)
    wait = WebDriverWait(driver, 30)
    data = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
        "highlights": {
            "summary": None,
            "table": [],
            
        }
    }

    # ================= COVER IMAGE =================
    section = wait.until(
        EC.presence_of_element_located((By.ID, "topHeaderCard-top-section"))
    )

    img = section.find_element(By.ID, "topHeaderCard-gallery-image")
    data["college_name"] = img.get_attribute("alt")
    data["cover_image"] = img.get_attribute("src")

    badges = section.find_elements(By.CLASS_NAME, "b8cb")
    for badge in badges:
        text = badge.text.lower()
        if "video" in text:
            data["videos_count"] = int(re.search(r"\d+", text).group())
        elif "photo" in text:
            data["photos_count"] = int(re.search(r"\d+", text).group())

    # ================= HEADER CARD =================
    header = wait.until(
        EC.presence_of_element_located((By.ID, "top-header-card-heading"))
    )

    try:
        data["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
    except:
        pass

    try:
        data["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        pass

    try:
        loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
        if "," in loc:
            data["location"], data["city"] = [x.strip() for x in loc.split(",", 1)]
        else:
            data["location"] = loc
    except:
        pass

    try:
        rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
        match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
        if match:
            data["rating"] = match.group(1)
    except:
        pass

    try:
        reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
        data["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
    except:
        pass

    try:
        qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
        num = re.search(r"[\d.]+", qa_text).group()
        data["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
    except:
        pass

    try:
        items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
        for item in items:
            txt = item.text.lower()
            if "institute" in txt:
                data["institute_type"] = item.text.strip()
            elif "estd" in txt:
                year = re.search(r"\d{4}", item.text)
                if year:
                    data["established_year"] = year.group()
    except:
        pass


        # 🔹 Highlights Table
# ================= HIGHLIGHTS SECTION (JS SAFE) =================
    try:
        highlights = wait.until(
            EC.presence_of_element_located((By.ID, "ovp_section_highlights"))
        )
    
        # 🔹 SUMMARY (already OK, JS se bhi safe)
        summary = driver.execute_script("""
            let el = document.querySelector('#EdContent__ovp_section_highlights');
            if (!el) return null;
            let ps = el.querySelectorAll('p');
            let out = [];
            ps.forEach(p => {
                let t = p.innerText.trim();
                if (t.length > 30) out.push(t);
            });
            return out.join("\\n");
        """)
        data["highlights"]["summary"] = summary
    
    
        # 🔹 TABLE (MAIN FIX)
        table_data = driver.execute_script("""
            let table = document.querySelector('#EdContent__ovp_section_highlights table');
            if (!table) return [];
    
            let rows = table.querySelectorAll('tr');
            let result = [];
    
            rows.forEach((row, idx) => {
                if (idx === 0) return; // skip header
                let cols = row.querySelectorAll('td');
                if (cols.length >= 2) {
                    let key = cols[0].innerText.trim();
                    let val = cols[1].innerText.trim();
                    if (key || val) {
                        result.push({
                            particular: key,
                            details: val
                        });
                    }
                }
            });
            return result;
        """)
        data["highlights"]["table"] = table_data
    
    except Exception as e:
        print("Highlights error:", e)
    
    

    return data

def scrape_college_infopro(driver):
    driver.get(COLLEGE_INFO_URL)
    wait = WebDriverWait(driver, 30)

    popular = {
        "intro": None,
        "courses": [],
        "faqs": []
    }

    # ================= SECTION WAIT =================
    wait.until(
        EC.presence_of_element_located(
            (By.ID, "ovp_section_popular_courses")
        )
    )

    # ================= INTRO / SUMMARY =================
    popular["intro"] = driver.execute_script("""
       let el = document.querySelector('#EdContent__ovp_section_popular_courses');
       if (!el) return null;
   
       let ps = el.querySelectorAll('p');
       let out = [];
   
       ps.forEach(p => {
           let t = p.textContent.replace(/\\s+/g, ' ').trim();
           if (t.length > 20) out.push(t);
       });
   
       return out.join("\\n");
       """)

    # ================= COURSES (FIXED) =================
    courses = driver.execute_script("""
        let result = [];

        document.querySelectorAll('div.base_course_tuple > div[id^="tuple_"]').forEach(tuple => {

            let course = {};

            // name + url
            let h3 = tuple.querySelector('h3');
            course.course_name = h3 ? h3.innerText.trim() : null;
            course.course_url = h3 ? h3.closest('a')?.href : null;

            // duration
            let spans = tuple.querySelectorAll('.edfa span');
            course.duration = spans.length > 1 ? spans[1].innerText.trim() : null;

            // rating + reviews
            let ratingBlock = tuple.querySelector('a[href*="reviews"]');
            if (ratingBlock) {
                course.rating = ratingBlock.querySelector('span')?.innerText.trim() || null;
                let r = ratingBlock.querySelector('.e040');
                course.reviews = r ? r.innerText.replace(/[()]/g, '') : null;
            }

            // ranking
            course.ranking =
                tuple.querySelector('.ba04')?.innerText.trim() || null;

            // ===== EXAMS ACCEPTED (SAFE) =====
            course.exams = [];
            tuple.querySelectorAll('label').forEach(label => {
                if (label.innerText.includes('Exams Accepted')) {
                    let ul = label.parentElement.querySelector('ul');
                    if (ul) {
                        ul.querySelectorAll('a').forEach(a => {
                            course.exams.push(a.innerText.trim());
                        });
                    }
                }
            });

            // ===== FEES =====
            course.fees = null;
            tuple.querySelectorAll('label').forEach(label => {
                if (label.innerText.includes('Total Tuition Fees')) {
                    let div = label.parentElement.querySelector('div');
                    if (div) {
                        course.fees = div.innerText.replace('Get Fee Details', '').trim();
                    }
                }
            });

            // ===== SALARY / PLACEMENT =====
            course.median_salary = null;
            tuple.querySelectorAll('label').forEach(label => {
                if (
                    label.innerText.includes('Median Salary') ||
                    label.innerText.includes('Placement Rating')
                ) {
                    let span = label.parentElement.querySelector('span');
                    if (span) {
                        course.median_salary = span.innerText.trim();
                    }
                }
            });

            result.push(course);
        });

        return result;
    """)
    popular["courses"] = courses

    # ================= FAQs =================
    faqs = driver.execute_script("""
        let faqs = [];
        document.querySelectorAll('#sectional-faqs-0 strong').forEach(q => {
            let question = q.innerText.replace('Q:', '').trim();
            let ansBox = q.parentElement.nextElementSibling;
            let answer = ansBox ? ansBox.innerText.replace('A:', '').trim() : "";
            if (question) {
                faqs.push({ question, answer });
            }
        });
        return faqs;
    """)
    popular["faqs"] = faqs

    return popular







def scrape_courses(driver):
    # ---------- COLLEGE INFO ----------
    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(COURSES_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COVER IMAGE ----------
    section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
    img = section.find_element(By.ID, "topHeaderCard-gallery-image")
    college_info["college_name"] = img.get_attribute("alt")
    college_info["cover_image"] = img.get_attribute("src")

    badges = section.find_elements(By.CLASS_NAME, "b8cb")
    for badge in badges:
        text = badge.text.lower()
        if "video" in text:
            college_info["videos_count"] = int(re.search(r"\d+", text).group())
        elif "photo" in text:
            college_info["photos_count"] = int(re.search(r"\d+", text).group())

    # ---------- HEADER CARD ----------
    header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

    try:
        college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
    except:
        pass

    try:
        college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        pass

    try:
        loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
        if "," in loc:
            college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
        else:
            college_info["location"] = loc
    except:
        pass

    try:
        rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
        match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
        if match:
            college_info["rating"] = match.group(1)
    except:
        pass

    try:
        reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
        college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
    except:
        pass

    try:
        qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
        num = re.search(r"[\d.]+", qa_text).group()
        college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
    except:
        pass

    try:
        items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
        for item in items:
            txt = item.text.lower()
            if "institute" in txt:
                college_info["institute_type"] = item.text.strip()
            elif "estd" in txt:
                year = re.search(r"\d{4}", item.text)
                if year:
                    college_info["established_year"] = year.group()
    except:
        pass

    # ---------- SCROLL FUNCTION ----------
    def scroll_to_bottom(driver, scroll_times=3, pause=1.5):
        for _ in range(scroll_times):
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(pause)

    scroll_to_bottom(driver, scroll_times=3, pause=2)

    # ---------- COURSES ----------
    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select("table._1708 tbody tr")
    courses = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        course_name = cols[0].get_text(" ", strip=True)
        fees = cols[1].get_text(" ", strip=True).replace("Get Fee Details", "").strip()

        eligibility = {}
        exams = []

        if len(cols) > 2:
            grad = cols[2].find("span", string=lambda x: x and "Graduation" in x)
            if grad:
                next_span = grad.find_next("span")
                if next_span:
                    eligibility["graduation"] = next_span.get_text(strip=True)

            exams = [a.get_text(strip=True) for a in cols[2].select("a")]
            if exams:
                eligibility["exams"] = exams

        courses.append({
            "course_name": course_name,
            "fees": fees,
            "eligibility": eligibility
        })

    return {"college_info": college_info, "courses": courses}


# # ---------------- FEES ----------------

def scrape_fees(driver):
    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(FEES_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COLLEGE HEADER ----------
    try:
        section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
        img = section.find_element(By.ID, "topHeaderCard-gallery-image")
        college_info["college_name"] = img.get_attribute("alt")
        college_info["cover_image"] = img.get_attribute("src")

        badges = section.find_elements(By.CLASS_NAME, "b8cb")
        for badge in badges:
            text = badge.text.lower()
            if "video" in text:
                college_info["videos_count"] = int(re.search(r"\d+", text).group())
            elif "photo" in text:
                college_info["photos_count"] = int(re.search(r"\d+", text).group())
    except:
        print("⚠️ Top header section not found")

    # ---------- HEADER CARD DETAILS ----------
    try:
        header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

        try:
            college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
        except:
            pass

        try:
            college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            pass

        try:
            loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
            if "," in loc:
                college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
            else:
                college_info["location"] = loc
        except:
            pass

        try:
            rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
            match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
            if match:
                college_info["rating"] = match.group(1)
        except:
            pass

        try:
            reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
            college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
        except:
            pass

        try:
            qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
            num = re.search(r"[\d.]+", qa_text).group()
            college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
        except:
            pass

        try:
            items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
            for item in items:
                txt = item.text.lower()
                if "institute" in txt:
                    college_info["institute_type"] = item.text.strip()
                elif "estd" in txt:
                    year = re.search(r"\d{4}", item.text)
                    if year:
                        college_info["established_year"] = year.group()
        except:
            pass

    except:
        print("⚠️ Header card not found")

    # ---------- FEES TABLE ----------
    fees_data = []

    try:
        # Scroll to bottom to load table
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Wait for table if it exists
        try:
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table._26d3")))
        except:
            print("⚠️ Fees table not found")
            return {"college_info": college_info, "fees_data": []}

        # Parse table with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("table._26d3 tbody tr")

        for row in rows:
            course_a = row.select_one("td:nth-child(1) a")
            fee_div = row.select_one("td:nth-child(2) div.getFeeDetailsCTA__text")

            if not course_a or not fee_div:
                continue

            fees = fee_div.get_text(" ", strip=True).replace("Get Fee Details", "").strip()
            fees_data.append({
                "course": course_a.get_text(strip=True),
                "total_tuition_fees": fees
            })

    except Exception as e:
        print(f"⚠️ Error scraping fees table: {e}")

    return {"college_info": college_info, "fees_data": fees_data}
# # ---------------- REVIEW SUMMARY ----------------
def scrape_review_summary(driver):

    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(REVIEWS_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COVER IMAGE ----------
    section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
    img = section.find_element(By.ID, "topHeaderCard-gallery-image")
    college_info["college_name"] = img.get_attribute("alt")
    college_info["cover_image"] = img.get_attribute("src")

    badges = section.find_elements(By.CLASS_NAME, "b8cb")
    for badge in badges:
        text = badge.text.lower()
        if "video" in text:
            college_info["videos_count"] = int(re.search(r"\d+", text).group())
        elif "photo" in text:
            college_info["photos_count"] = int(re.search(r"\d+", text).group())

    # ---------- HEADER CARD ----------
    header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

    try:
        college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
    except:
        pass

    try:
        college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        pass

    try:
        loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
        if "," in loc:
            college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
        else:
            college_info["location"] = loc
    except:
        pass

    try:
        rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
        match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
        if match:
            college_info["rating"] = match.group(1)
    except:
        pass

    try:
        reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
        college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
    except:
        pass

    try:
        qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
        num = re.search(r"[\d.]+", qa_text).group()
        college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
    except:
        pass

    try:
        items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
        for item in items:
            txt = item.text.lower()
            if "institute" in txt:
                college_info["institute_type"] = item.text.strip()
            elif "estd" in txt:
                year = re.search(r"\d{4}", item.text)
                if year:
                    college_info["established_year"] = year.group()
    except:
        pass
    summary = {
        "college_name": "",
        "overall_rating": "",
        "total_verified_reviews": "",
        "rating_distribution": {},
        "category_ratings": {}
    }

    # Page thoda scroll karo taki summary load ho jaye
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 🔥 MAIN SUMMARY CARD (paper-card bfe9)
    main_card = soup.select_one("div.paper-card.bfe9")
    if not main_card:
        print("❌ Review summary main card not found")
        return summary

    # -------- COLLEGE NAME --------
    college = main_card.select_one("div.fe79")
    if college:
        summary["college_name"] = college.get_text(strip=True)

    # -------- OVERALL RATING --------
    overall = main_card.select_one("span._6ac2")
    if overall:
        summary["overall_rating"] = overall.get_text(strip=True).replace("/5", "")

    # -------- TOTAL VERIFIED REVIEWS --------
    total = main_card.select_one("span._03a5")
    if total:
        summary["total_verified_reviews"] = total.get_text(strip=True)\
            .replace("Verified Reviews", "").strip()

    # -------- RATING DISTRIBUTION (4-5, 3-4, 2-3) --------
    for li in main_card.select("ul._8c4d li"):
        label = li.select_one("span._4826")
        count = li.select_one("span.c230")
        if label and count:
            summary["rating_distribution"][label.get_text(strip=True)] = count.get_text(strip=True)

    # -------- CATEGORY RATINGS (Placements, Infra, Faculty...) --------
    for card in main_card.select("div.paper-card.boxShadow._4b5c"):
        category = card.select_one("span._7542")
        rating = card.select_one("span._1b94 span")
        if category and rating:
            summary["category_ratings"][category.get_text(strip=True)] = rating.get_text(strip=True)

    return {"college_info":college_info,"summary":summary,}



# # ---------------- REVIEWS ----------------
def scrape_reviews(driver):
    
    reviews = []

    driver.get(REVIEWS_URL)
    wait = WebDriverWait(driver, 20)

    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.paper-card"))
    )

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("div.paper-card")

    for card in cards:
        title = card.select_one("div._1298")
        detail_block = card.select_one("div.cf9e.false")

        if not title or not detail_block:
            continue

        review = {
            "reviewer_name": (card.select_one("span._1bfc") or "").get_text(strip=True) if card.select_one("span._1bfc") else "",
            "course": (card.select_one("div._4efe a") or "").get_text(strip=True) if card.select_one("div._4efe a") else "",
            "overall_rating": (card.select_one("div._304d span") or "").get_text(strip=True) if card.select_one("div._304d span") else "",
            "review_title": title.get_text(strip=True),
            "review_date": (card.select_one("span._4dae") or "").get_text(strip=True) if card.select_one("span._4dae") else "",
            "detailed_review": {}
        }

        for sec in detail_block.find_all("div", recursive=False):
            key = sec.find("strong")
            val = sec.find("span")
            if key and val:
                review["detailed_review"][key.get_text(strip=True).replace(":", "")] = val.get_text(strip=True)

        reviews.append(review)

    return reviews

def scrape_admission_overview(driver):
    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(ADMISSION_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COVER IMAGE ----------
    section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
    img = section.find_element(By.ID, "topHeaderCard-gallery-image")
    college_info["college_name"] = img.get_attribute("alt")
    college_info["cover_image"] = img.get_attribute("src")

    badges = section.find_elements(By.CLASS_NAME, "b8cb")
    for badge in badges:
        text = badge.text.lower()
        if "video" in text:
            college_info["videos_count"] = int(re.search(r"\d+", text).group())
        elif "photo" in text:
            college_info["photos_count"] = int(re.search(r"\d+", text).group())

    # ---------- HEADER CARD ----------
    header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

    try:
        college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
    except:
        pass

    try:
        college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        pass

    try:
        loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
        if "," in loc:
            college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
        else:
            college_info["location"] = loc
    except:
        pass

    try:
        rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
        match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
        if match:
            college_info["rating"] = match.group(1)
    except:
        pass

    try:
        reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
        college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
    except:
        pass

    try:
        qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
        num = re.search(r"[\d.]+", qa_text).group()
        college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
    except:
        pass

    try:
        items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
        for item in items:
            txt = item.text.lower()
            if "institute" in txt:
                college_info["institute_type"] = item.text.strip()
            elif "estd" in txt:
                year = re.search(r"\d{4}", item.text)
                if year:
                    college_info["established_year"] = year.group()
    except:
        pass
    admission = {
        "title": "",
        "overview_text": "",
        "faqs": []
    }

    driver.get(ADMISSION_URL)
    wait = WebDriverWait(driver, 20)

    # Page ko thoda scroll karao (accordion + wiki load ke liye)
    for _ in range(4):
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # -------- TITLE --------
    title = soup.select_one("div#admission_section_admission_overview h2 div._6a22")
    if title:
        admission["title"] = title.get_text(strip=True)

    # -------- OVERVIEW TEXT --------
    overview_block = soup.select_one(
        "div#EdContent__admission_section_admission_overview"
    )

    if overview_block:
        paragraphs = overview_block.find_all("p")
        admission["overview_text"] = "\n\n".join(
            p.get_text(" ", strip=True) for p in paragraphs
        )

    # -------- FAQs (Questions & Answers) --------
    faq_blocks = soup.select("div.sectional-faqs > div.listener")

    for q_block in faq_blocks:
        question = q_block.get_text(" ", strip=True).replace("Q:", "").strip()

        answer_block = q_block.find_next("div", class_="_16f53f")
        answer = ""

        if answer_block:
            p_tags = answer_block.select("div._843b17 p")
            answer = " ".join(p.get_text(" ", strip=True) for p in p_tags)

        if question and answer:
            admission["faqs"].append({
                "question": question,
                "answer": answer
            })

    return {"college_info":college_info,"admission":admission}

def scrape_admission_eligibility_selection(driver):
    data = {
        "title": "",
        "intro_text": "",
        "eligibility_table": [],
        "faqs": []
    }

    driver.get(ADMISSION_URL)
    wait = WebDriverWait(driver, 25)

    # Scroll so accordion content loads
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 900);")
        time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ================= TITLE =================
    title = soup.select_one(
        "#admission_section_eligibility_selection h2 div._6a22"
    )
    if title:
        data["title"] = title.get_text(strip=True)

    # ================= INTRO PARAGRAPH =================
    intro = soup.select_one(
        "#EdContent__admission_section_eligibility_selection p"
    )
    if intro:
        data["intro_text"] = intro.get_text(" ", strip=True)

    # ================= TABLE =================
    table = soup.select_one(
        "#EdContent__admission_section_eligibility_selection table._895c"
    )

    if table:
        rows = table.select("tbody tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            course = cols[0].get_text(" ", strip=True)
            eligibility = cols[1].get_text(" ", strip=True)
            selection = cols[2].get_text(" ", strip=True)

            data["eligibility_table"].append({
                "course": course,
                "eligibility": eligibility,
                "selection_criteria": selection
            })

    # ================= FAQs =================
    faq_blocks = soup.select("div.sectional-faqs > div.listener")

    for q in faq_blocks:
        question = q.get_text(" ", strip=True)
        question = question.replace("Q:", "").strip()

        ans_block = q.find_next("div", class_="_16f53f")
        answer = ""

        if ans_block:
            answer = ans_block.get_text(" ", strip=True)
            answer = answer.replace("A:", "").strip()

        if question and answer:
            data["faqs"].append({
                "question": question,
                "answer": answer
            })

    return data

def scrape_placement_report(driver):
    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(PLACEMENT_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COLLEGE HEADER ----------
    try:
        section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
        img = section.find_element(By.ID, "topHeaderCard-gallery-image")
        college_info["college_name"] = img.get_attribute("alt")
        college_info["cover_image"] = img.get_attribute("src")

        badges = section.find_elements(By.CLASS_NAME, "b8cb")
        for badge in badges:
            text = badge.text.lower()
            if "video" in text:
                college_info["videos_count"] = int(re.search(r"\d+", text).group())
            elif "photo" in text:
                college_info["photos_count"] = int(re.search(r"\d+", text).group())
    except:
        print("⚠️ Top header section not found")

    # ---------- HEADER CARD DETAILS ----------
    try:
        header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

        try:
            college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
        except:
            pass

        try:
            college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            pass

        try:
            loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
            if "," in loc:
                college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
            else:
                college_info["location"] = loc
        except:
            pass

        try:
            rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
            match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
            if match:
                college_info["rating"] = match.group(1)
        except:
            pass

        try:
            reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
            college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
        except:
            pass

        try:
            qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
            num = re.search(r"[\d.]+", qa_text).group()
            college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
        except:
            pass

        try:
            items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
            for item in items:
                txt = item.text.lower()
                if "institute" in txt:
                    college_info["institute_type"] = item.text.strip()
                elif "estd" in txt:
                    year = re.search(r"\d{4}", item.text)
                    if year:
                        college_info["established_year"] = year.group()
        except:
            pass

    except:
        print("⚠️ Header card not found")
    data = {
        "title": "",
        "summary": [],
        "faqs": []
    }

    driver.get(PLACEMENT_URL)
    wait = WebDriverWait(driver, 25)

    # Scroll to load placement section
    for _ in range(6):
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    section = soup.select_one("section#placement_section_report")
    if not section:
        return data

    # ================= TITLE =================
    title = section.select_one("h2 div._6a22")
    if title:
        data["title"] = title.get_text(strip=True)

    # ================= SUMMARY PARAGRAPHS =================
    paragraphs = section.select(
        "#EdContent__placement_section_report p"
    )
    for p in paragraphs:
        text = p.get_text(" ", strip=True)
        if text:
            data["summary"].append(text)

    # ================= FAQs =================
    faq_questions = section.select("div.sectional-faqs > div.listener")

    for q in faq_questions:
        question = q.get_text(" ", strip=True)
        question = question.replace("Q:", "").strip()

        ans_block = q.find_next("div", class_="_16f53f")
        answer_text = ""
        tables = []

        if ans_block:
            # Answer text
            answer_text = ans_block.get_text(" ", strip=True)
            answer_text = answer_text.replace("A:", "").strip()

            # Tables inside answer
            for table in ans_block.select("table"):
                headers = [th.get_text(strip=True) for th in table.select("tr th")]
                rows = []

                for tr in table.select("tr")[1:]:
                    cols = [td.get_text(" ", strip=True) for td in tr.select("td")]
                    if cols:
                        rows.append(cols)

                tables.append({
                    "headers": headers,
                    "rows": rows
                })

        if question:
            data["faqs"].append({
                "question": question,
                "answer": answer_text,
                "tables": tables
            })

    return {"college_info":college_info,"data":data}

def scrape_average_package_section(driver):
    data = {
        "title": "",
        "intro": "",
        "average_package_table": [],
        "top_recruiters": [],
        "insights": [],
        "faqs": []
    }

    driver.get("https://www.shiksha.com/college/iim-ahmedabad-indian-institute-of-management-vastrapur-307/placement")
    wait = WebDriverWait(driver, 25)

    # Scroll to load section
    for _ in range(6):
        driver.execute_script("window.scrollBy(0, 900);")
        time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    section = soup.select_one("section#placement_section_average_package")
    if not section:
        return data

    # ---------------- TITLE ----------------
    title = section.select_one("h2 div._6a22")
    if title:
        data["title"] = title.get_text(strip=True)

    # ---------------- INTRO TEXT ----------------
    intro = section.select_one("#EdContent__placement_section_average_package p")
    if intro:
        data["intro"] = intro.get_text(" ", strip=True)

    # ---------------- MAIN TABLE ----------------
    table = section.select_one("#EdContent__placement_section_average_package table")
    if table:
        headers = [th.get_text(strip=True) for th in table.select("tr th")]
        for row in table.select("tr")[1:]:
            cols = [td.get_text(" ", strip=True) for td in row.select("td")]
            if cols:
                data["average_package_table"].append(dict(zip(headers, cols)))

    # ---------------- TOP RECRUITERS ----------------
    recruiters = section.select("div._140ef9 span._58be47")
    data["top_recruiters"] = [r.get_text(strip=True) for r in recruiters]

    # ---------------- INSIGHTS ----------------
    insight_cards = section.select("div._58c8")
    for card in insight_cards:
        heading = card.select_one("h6")
        text = card.select_one("p")

        if heading and text:
            data["insights"].append({
                "title": heading.get_text(strip=True),
                "description": text.get_text(strip=True)
            })

    # ---------------- FAQs ----------------
    faq_questions = section.select("div.sectional-faqs > div.listener")

    for q in faq_questions:
        question = q.get_text(" ", strip=True).replace("Q:", "").strip()
        ans_block = q.find_next("div", class_="_16f53f")

        answer_text = ""
        tables = []

        if ans_block:
            answer_text = ans_block.get_text(" ", strip=True).replace("A:", "").strip()

            for t in ans_block.select("table"):
                headers = [th.get_text(strip=True) for th in t.select("tr th")]
                rows = []

                for tr in t.select("tr")[1:]:
                    cols = [td.get_text(" ", strip=True) for td in tr.select("td")]
                    if cols:
                        rows.append(cols)

                tables.append({
                    "headers": headers,
                    "rows": rows
                })

        data["faqs"].append({
            "question": question,
            "answer": answer_text,
            "tables": tables
        })

    return data

def scrape_placement_faqs(driver):
    faqs = []

    

    driver.get(PLACEMENT_URL)
    time.sleep(5)

    # lazy load ke liye scroll
    for _ in range(8):
        driver.execute_script("window.scrollBy(0, 1200)")
        time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 👉 Question blocks
    questions = soup.select("div.html-0.c5db62.listener")

    for q in questions:
        question_text = q.get_text(" ", strip=True)
        question_text = question_text.replace("Q:", "").strip()

        answer_div = q.find_next_sibling("div", class_="_16f53f")
        if not answer_div:
            continue

        answer_paragraphs = []
        tables = []

        # ---- text ----
        for p in answer_div.select("p"):
            txt = p.get_text(" ", strip=True)
            if txt and "Ask Shiksha GPT" not in txt:
                answer_paragraphs.append(txt)

        # ---- tables ----
        for table in answer_div.select("table"):
            headers = [th.get_text(" ", strip=True) for th in table.select("tr th")]
            rows = []

            for tr in table.select("tr")[1:]:
                cols = [td.get_text(" ", strip=True) for td in tr.select("td")]
                if cols:
                    rows.append(cols)

            tables.append({
                "headers": headers,
                "rows": rows
            })

        faqs.append({
            "question": question_text,
            "answer": " ".join(answer_paragraphs),
            "tables": tables
        })

    return faqs

# ---------------- CUTOFF ----------------

def scrape_cutoff(driver):
    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(CUTOFF_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COLLEGE HEADER ----------
    try:
        section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
        img = section.find_element(By.ID, "topHeaderCard-gallery-image")
        college_info["college_name"] = img.get_attribute("alt")
        college_info["cover_image"] = img.get_attribute("src")

        badges = section.find_elements(By.CLASS_NAME, "b8cb")
        for badge in badges:
            text = badge.text.lower()
            if "video" in text:
                college_info["videos_count"] = int(re.search(r"\d+", text).group())
            elif "photo" in text:
                college_info["photos_count"] = int(re.search(r"\d+", text).group())
    except:
        print("⚠️ Top header section not found")

    # ---------- HEADER CARD DETAILS ----------
    try:
        header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

        try:
            college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
        except:
            pass

        try:
            college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            pass

        try:
            loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
            if "," in loc:
                college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
            else:
                college_info["location"] = loc
        except:
            pass

        try:
            rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
            match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
            if match:
                college_info["rating"] = match.group(1)
        except:
            pass

        try:
            reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
            college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
        except:
            pass

        try:
            qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
            num = re.search(r"[\d.]+", qa_text).group()
            college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
        except:
            pass

        try:
            items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
            for item in items:
                txt = item.text.lower()
                if "institute" in txt:
                    college_info["institute_type"] = item.text.strip()
                elif "estd" in txt:
                    year = re.search(r"\d{4}", item.text)
                    if year:
                        college_info["established_year"] = year.group()
        except:
            pass

    except:
        print("⚠️ Header card not found")
    result = []

    driver.get(CUTOFF_URL)
    wait = WebDriverWait(driver, 20)
    cutoff_section = wait.until(
        EC.presence_of_element_located((By.ID, "icop_section_latest_round_cutoff_327"))
    )

    # --- Expand qualifying cutoff accordion using JS click ---
    try:
        accordion_icon = cutoff_section.find_element(By.CSS_SELECTOR, "img._377d._7ef0")
        driver.execute_script("arguments[0].scrollIntoView(true);", accordion_icon)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", accordion_icon)  # JS click avoids interception
        time.sleep(2)  # wait for table to render
    except Exception as e:
        print("Accordion click error:", e)

    # --- Extract qualifying cutoff table using JS + BeautifulSoup ---
    qualifying_cutoff = []
    try:
        # Wait until table rows are present
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#icop_section_latest_round_cutoff_327 div.wikiContents table tbody tr")
            )
        )
    
        # Get table HTML directly within the cutoff section
        table_html = driver.execute_script(
            "return document.querySelector('#icop_section_latest_round_cutoff_327 div.wikiContents table').outerHTML;"
        )
        soup = BeautifulSoup(table_html, "html.parser")
    
        headers = [th.get_text(strip=True) for th in soup.select("thead th")]
        rows = soup.select("tbody tr")
        for row in rows:
            cols = row.find_all("td")
            row_dict = {headers[i]: cols[i].get_text(strip=True) if i < len(cols) else "" for i in range(len(headers))}
            qualifying_cutoff.append(row_dict)
    except Exception as e:
        print("Qualifying table parse error:", e)
    
    result.append({"type": "qualifying_cutoff", "table": qualifying_cutoff})

    # --- Extract course-wise cutoffs ---
    try:
        course_divs = cutoff_section.find_elements(By.CSS_SELECTOR, "div.multipleTableContainer > div")
        for div in course_divs:
            try:
                course_name = div.find_element(By.CSS_SELECTOR, "h5 span").text.strip()
                
                # Get course table HTML via JS within this div
                table_html = driver.execute_script(
                    "return arguments[0].querySelector('table').outerHTML;", div
                )
                soup = BeautifulSoup(table_html, "html.parser")
                headers = [th.get_text(strip=True) for th in soup.select("thead th")]
                rows = soup.select("tbody tr")
                rows_data = []
                for row in rows:
                    cols = row.find_all("td")
                    row_dict = {headers[i]: cols[i].get_text(strip=True) if i < len(cols) else "" for i in range(len(headers))}
                    rows_data.append(row_dict)

                result.append({
                    "type": "course_cutoff",
                    "course_name": course_name,
                    "cutoff_table": rows_data
                })
            except Exception as e:
                print("Course parse error:", e)
                continue
    except Exception as e:
        print("Course container error:", e)

    return {"college_info":college_info,"result":result}

def scrape_ranking(driver):
    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(RANKING_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COLLEGE HEADER ----------
    try:
        section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
        img = section.find_element(By.ID, "topHeaderCard-gallery-image")
        college_info["college_name"] = img.get_attribute("alt")
        college_info["cover_image"] = img.get_attribute("src")

        badges = section.find_elements(By.CLASS_NAME, "b8cb")
        for badge in badges:
            text = badge.text.lower()
            if "video" in text:
                college_info["videos_count"] = int(re.search(r"\d+", text).group())
            elif "photo" in text:
                college_info["photos_count"] = int(re.search(r"\d+", text).group())
    except:
        print("⚠️ Top header section not found")

    # ---------- HEADER CARD DETAILS ----------
    try:
        header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

        try:
            college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
        except:
            pass

        try:
            college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            pass

        try:
            loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
            if "," in loc:
                college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
            else:
                college_info["location"] = loc
        except:
            pass

        try:
            rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
            match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
            if match:
                college_info["rating"] = match.group(1)
        except:
            pass

        try:
            reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
            college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
        except:
            pass

        try:
            qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
            num = re.search(r"[\d.]+", qa_text).group()
            college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
        except:
            pass

        try:
            items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
            for item in items:
                txt = item.text.lower()
                if "institute" in txt:
                    college_info["institute_type"] = item.text.strip()
                elif "estd" in txt:
                    year = re.search(r"\d{4}", item.text)
                    if year:
                        college_info["established_year"] = year.group()
        except:
            pass

    except:
        print("⚠️ Header card not found")
    result = []

    driver.get(RANKING_URL)
    wait = WebDriverWait(driver, 30)

    # --- wait for ranking section ---
    ranking_section = wait.until(
        EC.presence_of_element_located((By.ID, "rp_section_international_ranking"))
    )

    # --- expand accordion ---
    try:
        icon = ranking_section.find_element(By.CSS_SELECTOR, "img._377d._7ef0")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", icon)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", icon)
        time.sleep(2)
    except:
        pass

    # --- wait for content block ---
    content_div = wait.until(
        EC.presence_of_element_located(
            (By.ID, "EdContent__rp_section_international_ranking")
        )
    )

    # --- get FULL HTML of content ---
    html = driver.execute_script(
        "return arguments[0].innerHTML;", content_div
    )

    soup = BeautifulSoup(html, "html.parser")

    # ================= HEADING =================
    try:
        title = ranking_section.find_element(By.CSS_SELECTOR, "h2 div").text.strip()
    except:
        title = ""

    # ================= PARAGRAPHS =================
    description = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            description.append(text)

    # ================= TABLE =================
    tables = []
    for table in soup.find_all("table"):
        table_rows = []
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            if cells:
                table_rows.append(cells)
        if table_rows:
            tables.append(table_rows)

    result.append({
        "type": "international_ranking",
        "title": title,
        "description": description,
        "tables": tables
    })

    return {"college_info":college_info,"result":result}

def scrape_ranking_section(driver):
    driver.get(RANKING_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    section = soup.find("section", id="rp_section_publishers_8")
    if not section:
        return {}

    result = {
        "title": "",
        "description": "",
        "tables": []
    }

    # ---- TITLE ----
    h2 = section.find("h2")
    if h2:
        result["title"] = h2.get_text(strip=True)

    # ---- DESCRIPTION (paragraph text) ----
    paragraphs = section.find_all("p")
    result["description"] = " ".join(p.get_text(" ", strip=True) for p in paragraphs)

    # ---- ALL TABLES ----
    for table in section.find_all("table"):
        table_data = []

        # headers
        headers = [th.get_text(strip=True) for th in table.find_all("th")]

        for row in table.find_all("tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]

            if not cols:
                continue

            if headers and len(headers) == len(cols):
                table_data.append(dict(zip(headers, cols)))
            else:
                table_data.append(cols)

        if table_data:
            result["tables"].append(table_data)

    return result



def parse_ranking_criteria_html(driver):
    driver.get(RANKING_URL)
    wait = WebDriverWait(driver, 30)

    section = wait.until(
        EC.presence_of_element_located(
            (By.ID, "EdContent__rp_section_publisher_ranking_criteria")
        )
    )

    # 🔥 scroll so lazy images load
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", section)
    time.sleep(2)

    html = driver.execute_script(
        "return arguments[0].innerHTML;", section
    )

    soup = BeautifulSoup(html, "html.parser")

    data = {
        "description": "",
        "table": [],
        "images": []
    }

    # ✅ description
    p = soup.find("p")
    if p:
        data["description"] = p.get_text(strip=True)

    # ✅ table
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")
        headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

        for row in rows[1:]:
            values = [td.get_text(strip=True) for td in row.find_all("td")]
            if values:
                data["table"].append(dict(zip(headers, values)))

    # ✅ images (lazy-load safe)
    images = set()
    for img in soup.find_all("img"):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
        )
        if src and src.startswith("http"):
            images.add(src)

    data["images"] = list(images)

    return data

def scrape_mini_clips(driver):
    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(GALLARY_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COLLEGE HEADER ----------
    try:
        section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
        img = section.find_element(By.ID, "topHeaderCard-gallery-image")
        college_info["college_name"] = img.get_attribute("alt")
        college_info["cover_image"] = img.get_attribute("src")

        badges = section.find_elements(By.CLASS_NAME, "b8cb")
        for badge in badges:
            text = badge.text.lower()
            if "video" in text:
                college_info["videos_count"] = int(re.search(r"\d+", text).group())
            elif "photo" in text:
                college_info["photos_count"] = int(re.search(r"\d+", text).group())
    except:
        print("⚠️ Top header section not found")

    # ---------- HEADER CARD DETAILS ----------
    try:
        header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

        try:
            college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
        except:
            pass

        try:
            college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            pass

        try:
            loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
            if "," in loc:
                college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
            else:
                college_info["location"] = loc
        except:
            pass

        try:
            rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
            match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
            if match:
                college_info["rating"] = match.group(1)
        except:
            pass

        try:
            reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
            college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
        except:
            pass

        try:
            qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
            num = re.search(r"[\d.]+", qa_text).group()
            college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
        except:
            pass

        try:
            items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
            for item in items:
                txt = item.text.lower()
                if "institute" in txt:
                    college_info["institute_type"] = item.text.strip()
                elif "estd" in txt:
                    year = re.search(r"\d{4}", item.text)
                    if year:
                        college_info["established_year"] = year.group()
        except:
            pass

    except:
        print("⚠️ Header card not found")
    driver.get(GALLARY_URL)
    wait = WebDriverWait(driver, 40)

    data = {
        "section_title": "Mini Clips",
        "clips": []
    }

    # ✅ wait for widget
    widget = wait.until(
        EC.presence_of_element_located((By.ID, "reelsWidget"))
    )

    # ✅ force scroll (VERY IMPORTANT)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", widget)
    time.sleep(3)

    # ✅ wait until clips appear
    wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#reelsWidget li._7c2b")
        )
    )

    clips = driver.find_elements(By.CSS_SELECTOR, "#reelsWidget li._7c2b")

    for clip in clips:
        clip_data = {
            "title": "",
            "thumbnail": "",
            
        }

        # 🎥 iframe video
       

        # 🖼️ thumbnail
        try:
            img = clip.find_element(By.TAG_NAME, "img")
            clip_data["thumbnail"] = img.get_attribute("src")
        except:
            pass

        # 📝 title
        try:
            title = clip.find_element(By.CSS_SELECTOR, "._4a7330")
            clip_data["title"] = title.text.strip()
        except:
            pass

        if any(clip_data.values()):
            data["clips"].append(clip_data)

    return {"college_info":college_info,"data":data}

def scrape_hostel_campus_structured(driver):
    college_info = {
        "college_name": None,
        "logo": None,
        "cover_image": None,
        "videos_count": 0,
        "photos_count": 0,
        "rating": None,
        "reviews_count": None,
        "qa_count": None,
        "location": None,
        "city": None,
        "institute_type": None,
        "established_year": None,
    }

    driver.get(HOTEL_CAMPUS_URL)
    wait = WebDriverWait(driver, 20)

    # ---------- COLLEGE HEADER ----------
    try:
        section = wait.until(EC.presence_of_element_located((By.ID, "topHeaderCard-top-section")))
        img = section.find_element(By.ID, "topHeaderCard-gallery-image")
        college_info["college_name"] = img.get_attribute("alt")
        college_info["cover_image"] = img.get_attribute("src")

        badges = section.find_elements(By.CLASS_NAME, "b8cb")
        for badge in badges:
            text = badge.text.lower()
            if "video" in text:
                college_info["videos_count"] = int(re.search(r"\d+", text).group())
            elif "photo" in text:
                college_info["photos_count"] = int(re.search(r"\d+", text).group())
    except:
        print("⚠️ Top header section not found")

    # ---------- HEADER CARD DETAILS ----------
    try:
        header = wait.until(EC.presence_of_element_located((By.ID, "top-header-card-heading")))

        try:
            college_info["logo"] = header.find_element(By.CSS_SELECTOR, "div.c55b78 img").get_attribute("src")
        except:
            pass

        try:
            college_info["college_name"] = header.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            pass

        try:
            loc = header.find_element(By.CLASS_NAME, "_94eae8").text.strip()
            if "," in loc:
                college_info["location"], college_info["city"] = [x.strip() for x in loc.split(",", 1)]
            else:
                college_info["location"] = loc
        except:
            pass

        try:
            rating_text = header.find_element(By.CLASS_NAME, "f05f57").text
            match = re.search(r"([\d.]+)\s*/\s*5", rating_text)
            if match:
                college_info["rating"] = match.group(1)
        except:
            pass

        try:
            reviews_text = header.find_element(By.XPATH, ".//a[contains(text(),'Reviews')]").text
            college_info["reviews_count"] = int(re.search(r"\d+", reviews_text).group())
        except:
            pass

        try:
            qa_text = header.find_element(By.XPATH, ".//a[contains(text(),'Student Q')]").text.lower()
            num = re.search(r"[\d.]+", qa_text).group()
            college_info["qa_count"] = int(float(num) * 1000) if "k" in qa_text else int(num)
        except:
            pass

        try:
            items = header.find_elements(By.CSS_SELECTOR, "ul.e1a898 li")
            for item in items:
                txt = item.text.lower()
                if "institute" in txt:
                    college_info["institute_type"] = item.text.strip()
                elif "estd" in txt:
                    year = re.search(r"\d{4}", item.text)
                    if year:
                        college_info["established_year"] = year.group()
        except:
            pass

    except:
        print("⚠️ Header card not found")
    driver.get(HOTEL_CAMPUS_URL)
    wait = WebDriverWait(driver, 30)

    section = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.wikkiContents"))
    )

    html = driver.execute_script("return arguments[0].innerHTML;", section)
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "author": "",
        "updated_on": "",
        "sections": []
    }

    # ✅ Author
    author = soup.select_one(".adp_usr_dtls a")
    if author:
        result["author"] = author.get_text(strip=True)

    # ✅ Updated date
    updated = soup.select_one(".post-date")
    if updated:
        result["updated_on"] = updated.get_text(strip=True)

    content_root = soup.select_one(".abtSection")
    if not content_root:
        return result

    current_section = {
        "heading": "Introduction",
        "text": [],
        "list": [],
        "images": [],
        "videos": [],
        "tables": []
    }

    def push_section():
        if (
            current_section["text"]
            or current_section["list"]
            or current_section["images"]
            or current_section["videos"]
            or current_section["tables"]
        ):
            result["sections"].append(current_section.copy())

    # ✅ Traverse content in order
    for tag in content_root.find_all(
        ["h2", "h3", "p", "ul", "img", "iframe", "table"],
        recursive=True
    ):

        # 🔹 New section starts
        if tag.name in ["h2", "h3"]:
            push_section()
            current_section = {
                "heading": tag.get_text(strip=True),
                "text": [],
                "list": [],
                "images": [],
                "videos": [],
                "tables": []
            }

        elif tag.name == "p":
            # Skip paragraphs inside table
            if tag.find_parent("table"):
                continue
            text = tag.get_text(" ", strip=True)
            if text:
                current_section["text"].append(text)

        elif tag.name == "ul":
            for li in tag.find_all("li"):
                li_text = li.get_text(strip=True)
                if li_text:
                    current_section["list"].append(li_text)

        elif tag.name == "img":
            src = (
                tag.get("data-src")
                or tag.get("data-original")
                or tag.get("src")
            )
            if src and src.startswith("http"):
                current_section["images"].append(src)

        elif tag.name == "iframe":
            src = tag.get("src")
            if not src:
                continue
            video = {
                "video_url": src,
                "video_id": "",
                "title": tag.get("title", "")
            }
            if "embed/" in src:
                video["video_id"] = src.split("embed/")[1].split("?")[0]
            current_section["videos"].append(video)

        elif tag.name == "table":
            table_data = []
            rows = tag.find_all("tr")
            if rows:
                headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
                for row in rows[1:]:
                    values = [td.get_text(strip=True) for td in row.find_all("td")]
                    if values:
                        if headers and len(headers) == len(values):
                            table_data.append(dict(zip(headers, values)))
                        else:
                            table_data.append(values)
            if table_data:
                current_section["tables"].append(table_data)

    push_section()
    return {"college_info":college_info,"result":result}

def scrape_infrastructure_structured(driver):
  
    driver.get(HOTEL_CAMPUS_URL)
    wait = WebDriverWait(driver, 30)

    section = wait.until(
        EC.presence_of_element_located((By.ID, "infrastructureSection"))
    )
    
    html = driver.execute_script("return arguments[0].innerHTML;", section)
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "section": "",
        "facilities": [],
        "other_facilities": []
    }

    # Section title
    title_tag = soup.find("h2", class_="tbSec2")
    if title_tag:
        result["section"] = title_tag.get_text(strip=True)

    # Main facilities
    for li in soup.select("ul.infraDataList > li"):
        # Handle other major facilities without dtl
        if li.find_all("div", class_="icn") and not li.find("div", class_="dtl"):
            other_list = [i.get_text(strip=True) for i in li.find_all("strong")]
            result["facilities"].append({
                "name": "Other Major Facilities",
                "list": other_list
            })
            continue

        name_tag = li.find("strong")
        name = name_tag.get_text(strip=True) if name_tag else None
        description_tag = li.find("div", class_="dtl")
        description = ""
        available_facilities = []

        if description_tag:
            p_tag = description_tag.find("p")
            if p_tag:
                description = p_tag.get_text(" ", strip=True)

            child_facility = description_tag.find("div", class_="childFaciltyBox")
            if child_facility:
                spans = [s.get_text(strip=True) for s in child_facility.find_all("span") if s.get_text(strip=True)]
                # Sports / Labs style
                if "|" in child_facility.text:
                    available_facilities = [s for s in spans if s not in ["|", ","]]
                else:
                    # Hostel details with Boys/Girls
                    details = {}
                    current_category = None
                    temp_list = []
                    for s in spans:
                        if "Hostel" in s or "Boys" in s or "Girls" in s:
                            if current_category and temp_list:
                                details[current_category] = temp_list
                            current_category = s
                            temp_list = []
                        elif s not in ["|", ","]:
                            temp_list.append(s)
                    if current_category and temp_list:
                        details[current_category] = temp_list
                    result["facilities"].append({
                        "name": name,
                        "description": description,
                        "details": details
                    })
                    continue

        facility_data = {"name": name}
        if description:
            facility_data["description"] = description
        if available_facilities:
            facility_data["available_facilities"] = available_facilities

        result["facilities"].append(facility_data)

    # Other facilities at the bottom
    other_facilities = [span.get_text(strip=True) for span in soup.select("div.otherFacilityBox .OFLabels .itm")]
    result["other_facilities"] = other_facilities

    return result




# ---------------- RUN ----------------
def scrape_mba_colleges():
    driver = create_driver()
    time.sleep(3)

    try:
        data = {
            "college_info":{
             "college_info":scrape_college_info(driver),
             "college_info_program":scrape_college_infopro(driver),
            },
            "courses":scrape_courses(driver),
            "fees":scrape_fees(driver),
            "reviews":{
            "review_summary":scrape_review_summary(driver),
            "reviews":scrape_reviews(driver),
            },
            "admission":{
            "admission":scrape_admission_overview(driver),
            "eligibility_selection":scrape_admission_eligibility_selection(driver),
            },
            "placement":{
            "placement_report":scrape_placement_report(driver),
            "average_package":scrape_average_package_section(driver),
            "placements_faqs":scrape_placement_faqs(driver),
            },
            "cut_off":{
            "cut_off":scrape_cutoff(driver),
            },
            "ranking":{
            "ranking":scrape_ranking(driver),
            "ranking_section":scrape_ranking_section(driver),
            "ranking_criteria":parse_ranking_criteria_html(driver),
            },
            "gallery":{
            "gallery_page":scrape_mini_clips(driver),
            },
           "hotel_campus":{
            "hostel_campus":scrape_hostel_campus_structured(driver),
            "infrastructure":scrape_infrastructure_structured(driver)
           }
           
        }
        return data

    finally:
        driver.quit()

import time
import os

DATA_FILE =  "iim_ahmedabad_full_data.json"
UPDATE_INTERVAL = 6 * 60 * 60  # 6 hours

def auto_update_scraper():
    # Check last modified time
    # if os.path.exists(DATA_FILE):
    #     last_mod = os.path.getmtime(DATA_FILE)
    #     if time.time() - last_mod < UPDATE_INTERVAL:
    #         print("⏱️ Data is recent, no need to scrape")
    #         return

    print("🔄 Scraping started")
    data = scrape_mba_colleges()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✅ Data scraped & saved successfully")

if __name__ == "__main__":
    while True:
        auto_update_scraper()
        time.sleep(UPDATE_INTERVAL)
