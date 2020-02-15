from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
try:
    opts = Options()
    opts.set_headless()
    assert opts.headless  # Operating in headless mode
    browser = Firefox(options=opts)
    browser.get('https://duckduckgo.com')
    search_form.send_keys('real python')
    search_form.submit()
except Exception as e:
    print(f"An exception has occurred: {e}")
