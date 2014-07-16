"""
Single page performance tests for Studio.
"""
from bok_choy.performance import WebAppPerfReport, performance_report
from ..pages.studio.login import LoginPage
# from ..pages.studio.signup import SignupPage


class PagePerformanceTest(WebAppPerfReport):
    """
    Smoke test for pages in Studio that are visible when logged out.
    """
    @performance_report(cached_only=True)
    def test_login_page_perf(self):
        """
        Produce a report for the login page performance.
        """
        login_page = LoginPage(self.browser)
        login_page.visit()

        # signup_page = SignupPage(self.browser)
        # signup_page.visit()
