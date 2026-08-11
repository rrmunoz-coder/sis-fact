from sisfact.execution.service import policy_values


def test_manual_policy_ignores_schedule():
    values = policy_values({
        "execution_mode": "MANUAL",
        "frequency_type": "DAILY",
        "run_time": "06:00",
        "timeout_minutes": "45",
        "max_retries": "2",
    })
    assert values["execution_mode"] == "MANUAL"
    assert values["frequency_type"] is None


def test_scheduled_requires_frequency():
    try:
        policy_values({"execution_mode": "SCHEDULED", "timeout_minutes": "45", "max_retries": "2"})
    except ValueError as exc:
        assert "periodicidad" in str(exc).lower()
    else:
        raise AssertionError("SCHEDULED sin frecuencia debió fallar")


def test_external_requires_executor():
    try:
        policy_values({"execution_mode": "EXTERNAL", "timeout_minutes": "45", "max_retries": "2"})
    except ValueError as exc:
        assert "ejecutor" in str(exc).lower()
    else:
        raise AssertionError("EXTERNAL sin ejecutor debió fallar")


def test_daily_policy_normalizes_time():
    values = policy_values({
        "execution_mode": "SCHEDULED",
        "frequency_type": "DAILY",
        "run_time": "06:05",
        "interval_value": "1",
        "timeout_minutes": "30",
        "max_retries": "1",
    })
    assert values["run_time"] == "06:05"
    assert values["timeout_minutes"] == 30
    assert values["max_retries"] == 1
