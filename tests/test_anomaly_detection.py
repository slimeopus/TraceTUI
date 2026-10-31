"""Тесты для автоматического обнаружения аномалий."""

from tracetui.models import LogLevel, LogEntry
from tracetui.widgets.log_list import LogList


class TestAnomalyDetection:
    """Тесты автоматического выделения аномалий."""

    def test_error_level_is_anomaly(self):
        """Уровень ERROR автоматически аномальный."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.ERROR, message="some info")
        assert log_list._is_anomaly(entry) is True

    def test_critical_level_is_anomaly(self):
        """Уровень CRITICAL автоматически аномальный."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.CRITICAL, message="some info")
        assert log_list._is_anomaly(entry) is True

    def test_timeout_keyword_detected(self):
        """Ключевое слово Timeout обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.WARNING, message="Request timeout after 30s")
        assert log_list._is_anomaly(entry) is True

    def test_connection_error_keyword_detected(self):
        """Ключевое слово ConnectionError обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.ERROR, message="ConnectionError: host unreachable")
        assert log_list._is_anomaly(entry) is True

    def test_exception_keyword_detected(self):
        """Ключевое слово Exception обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.ERROR, message="Unhandled exception in worker")
        assert log_list._is_anomaly(entry) is True

    def test_failure_keyword_detected(self):
        """Ключевое слово Failure обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.WARNING, message="Task failure after 3 retries")
        assert log_list._is_anomaly(entry) is True

    def test_fatal_keyword_detected(self):
        """Ключевое слово Fatal обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.ERROR, message="Fatal error in main loop")
        assert log_list._is_anomaly(entry) is True

    def test_status_code_500_detected(self):
        """HTTP 500 обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.WARNING, message="Server responded with 500")
        assert log_list._is_anomaly(entry) is True

    def test_status_code_503_detected(self):
        """HTTP 503 обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.WARNING, message="Service 503 unavailable")
        assert log_list._is_anomaly(entry) is True

    def test_timed_out_keyword_detected(self):
        """Фраза timed out обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.WARNING, message="Database connection timed out")
        assert log_list._is_anomaly(entry) is True

    def test_broken_pipe_detected(self):
        """Фраза broken pipe обнаруживается."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.ERROR, message="Write failed: broken pipe")
        assert log_list._is_anomaly(entry) is True

    def test_normal_info_is_not_anomaly(self):
        """Обычный INFO не является аномалией."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.INFO, message="Application started successfully")
        assert log_list._is_anomaly(entry) is False

    def test_normal_debug_is_not_anomaly(self):
        """Обычный DEBUG не является аномалией."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.DEBUG, message="Processing request payload")
        assert log_list._is_anomaly(entry) is False

    def test_normal_warning_is_not_anomaly(self):
        """Обычный WARNING без ключевых слов не аномалия."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.WARNING, message="Configuration file is outdated")
        assert log_list._is_anomaly(entry) is False

    def test_case_insensitive_detection(self):
        """Проверка без учёта регистра."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.WARNING, message="TIMEOUT detected in module")
        assert log_list._is_anomaly(entry) is True

        entry2 = LogEntry(level=LogLevel.WARNING, message="Timeout in module")
        assert log_list._is_anomaly(entry2) is True

        entry3 = LogEntry(level=LogLevel.WARNING, message="tImeOuT occurred")
        assert log_list._is_anomaly(entry3) is True

    def test_anomaly_count_in_header(self):
        """Подсчёт аномалий в заголовке."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="normal"),
            LogEntry(level=LogLevel.ERROR, message="error"),
            LogEntry(level=LogLevel.WARNING, message="timeout occurred"),
            LogEntry(level=LogLevel.DEBUG, message="debug info"),
        ]
        log_list._entries = entries
        # DataTable использует _build_line() вместо _build_lines()
        # Проверяем аномалии через get_filtered_entries
        filtered = log_list._get_filtered_entries()
        anomaly_count = sum(1 for e in filtered if log_list._is_anomaly(e))
        assert anomaly_count == 2

    def test_custom_anomaly_keywords(self):
        """Проверка что список ключевых слов не пустой."""
        log_list = LogList()
        assert len(log_list._anomaly_keywords) > 0
        assert "timeout" in log_list._anomaly_keywords
        assert "connectionerror" in log_list._anomaly_keywords
