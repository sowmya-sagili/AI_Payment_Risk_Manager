import pytest
import requests
from unittest.mock import patch
from frontend.app import check_backend_health, fetch_history, fetch_analytics

@patch("requests.get")
def test_backend_online(mock_get):
    mock_get.return_value.status_code = 200
    backend_online, model_ready = check_backend_health()
    assert backend_online == True
    assert model_ready == True

@patch("requests.get")
def test_backend_model_unavailable(mock_get):
    mock_get.return_value.status_code = 503
    backend_online, model_ready = check_backend_health()
    assert backend_online == True
    assert model_ready == False

@patch("requests.get")
def test_backend_offline(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError()
    backend_online, model_ready = check_backend_health()
    assert backend_online == False
    assert model_ready == False

@patch("requests.get")
def test_fetch_history_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [{"tx": "1"}]
    data = fetch_history()
    assert len(data) == 1

@patch("requests.get")
def test_fetch_history_fail(mock_get):
    mock_get.return_value.status_code = 500
    data = fetch_history()
    assert data == []
