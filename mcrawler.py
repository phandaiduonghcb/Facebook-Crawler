import browser
from page import *
from helium import *
from selenium.common import exceptions
from selenium.webdriver.common.by import By
import json
import time

HEADLESS = True # if False the browser will run in background.
PRIVATE = True # Running in incognito mode

PAGE_URL = 'https://m.facebook.com/pageABC/posts'
SCROLL_DOWN = 1 # Number of times to scroll so that more posts are loaded.
VIEW_MORE_CMTS = 5 # Number of times to click view more comments in a post.
VIEW_MORE_REPLIES = 10 # Number of times to click to see replies in a post.

# If username or password is None, facebook will not be logged in.
LOGIN_USERNAME = None # ex: 'user'
LOGIN_PASSWORD = None # ex: '123456'

PRINT_DETAILS = False # Print post and comment content.

SAVED_FILE_NAME = 'posts.json'
def print_(*args, **kargs):
    if PRINT_DETAILS:
        print(*args, **kargs)


def scroll_to_element(driver, e):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", e)
def crawl_posts():
    # For more settings when setting up the driver, see "https://github.com/18520339/facebook-data-extraction/tree/master/2%20-%20Automation%20tools%20with%20IP%20hiding%20techniques"
    driver = browser.setup_driver(PAGE_URL, browser.TOR_PATH.LINUX, private=PRIVATE, browser_options= browser.BROWSER_OPTIONS.FIREFOX, headless=HEADLESS, use_proxy=False)

    if LOGIN_USERNAME is not None and LOGIN_PASSWORD is not None:
        loginBtn = driver.find_element(by=By.CSS_SELECTOR,value='#msite-pages-header-contents > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > a:nth-child(1)')
        loginBtn.click()

        emailInput = driver.find_element(by=By.CSS_SELECTOR, value='#m_login_email')
        passInput = driver.find_element(by=By.CSS_SELECTOR, value='#m_login_password')

        write(LOGIN_USERNAME, emailInput)
        write(LOGIN_PASSWORD, passInput)
        click(Button('Log In'))

        def login_finished():
            try:
                driver.find_element(by=By.ID, value='pages_msite_body_contents')
                return True
            except:
                return False
        wait_until(login_finished)


    # Scroll for more posts:
    for i in range(SCROLL_DOWN):
        print(f'Load more posts times {i + 1}/{scroll_down}')
        load_more_posts(driver)

    posts = driver.find_elements(by=By.CSS_SELECTOR, value="div[class='story_body_container'] > div > a")
    post_links = [post.get_attribute('href') for post in posts]

    print(f'Number of posts: {len(post_links)}')
    posts = []
    for post_i, link in enumerate(post_links):
        driver.get(link)
        try:
            post = driver.find_element(by=By.ID,value='m_story_permalink_view')
        except exceptions.NoSuchElementException:
            continue

        # Load more comments
        for i in range(VIEW_MORE_CMTS):
            try:
                viewmoreBtn = post.find_element(by=By.CSS_SELECTOR, value = "div[id*='see_next'] > a")
            except exceptions.NoSuchElementException:
                break
            except exceptions.StaleElementReferenceException:
                continue
            scroll_to_element(driver, viewmoreBtn)
            viewmoreBtn.click()
            time.sleep(random.uniform(0.5,1))

        # Load replies
        for i in range(VIEW_MORE_REPLIES):
            try:
                repliesBtn = post.find_element(by=By.CSS_SELECTOR, value = "div[data-sigil='replies-see-more'] > a")
            except exceptions.NoSuchElementException:
                break
            except exceptions.StaleElementReferenceException:
                continue
            scroll_to_element(driver, repliesBtn)
            repliesBtn.click()
            time.sleep(random.uniform(0.5,1))

        # Start to crawl post data:
        print(f'***POST {post_i}***')

        # Post content
        content = post.find_element(by=By.CSS_SELECTOR, value='.story_body_container > div > div').text
        post_data = {}
        post_data['body'] = content
        print_(content)


        comments = post.find_elements(by=By.CSS_SELECTOR, value='div[data-sigil="comment"]')
        print(f'# Number of comments: {len(comments)}')

        comment_arr = []
        for comment in comments:
            aComment = {}
            
            print_('--- ',end='')
            
            try:
                comment_body = comment.find_element(by=By.CSS_SELECTOR, value='div[data-sigil="comment"] > div:nth-child(2) > div:first-child div[data-sigil="comment-body"]')
            except exceptions.NoSuchElementException:
                    continue
            comment_details = comment_body.find_element(by=By.XPATH, value='./..').find_elements(by=By.TAG_NAME,value='div')
            commenter_name = comment_details[0].get_attribute("textContent")
            comment_content = comment_details[1].text

            aComment['name'] = commenter_name
            aComment['body'] = comment_content
            print_(f'{commenter_name}: {comment_content}')

            
            replies_wrapper = comment.find_elements(by=By.CSS_SELECTOR, value='div[data-sigil="comment"] > div:nth-child(2) > div:last-child > div')
            # Check if the comment is replied:
            if len(replies_wrapper) > 1:
                replies = replies_wrapper[0].find_elements(by=By.CSS_SELECTOR, value='div[data-sigil="comment inline-reply"]')
                reply_arr = []
                for reply in replies:
                    aReply = {}
                    print_('++++++ ',end='')
                    try:
                        reply_body= reply.find_element(by=By.CSS_SELECTOR, value='div[data-sigil="comment inline-reply"] > div:nth-child(2) > div:first-child div[data-sigil="comment-body"]')
                    except exceptions.NoSuchElementException:
                        continue
                    reply_details = reply_body.find_element(by=By.XPATH, value='./..').find_elements(by=By.TAG_NAME,value='div')
                    respondent_name = reply_details[0].get_attribute("textContent")
                    reply_content = reply_details[1].text
                    aReply['name'] = respondent_name
                    aReply['body'] = reply_content
                    reply_arr.append(aReply)
                    print_(f'{respondent_name}: {reply_content}')
            else:
                reply_arr = []
            aComment['replies'] = reply_arr
            comment_arr.append(aComment)
            post_data['comments'] = comment_arr
        posts.append(post_data)

    return {'posts': posts}

if __name__ == '__main__':
    data = crawl_posts()
    with open(SAVED_FILE_NAME, 'w') as j:
        print(f'Saved to {SAVED_FILE_NAME}')
        json.dump(data , j)