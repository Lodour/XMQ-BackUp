from selenium import webdriver


class AutoClosableChrome(webdriver.Chrome):
    def __enter__(self):
        return self

    def __exit__(self, type, value, trace):
        self.quit()
