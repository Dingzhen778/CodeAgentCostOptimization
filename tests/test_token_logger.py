"""Token Logger 单元测试"""
import json
import pytest
from pathlib import Path
from src.gateway.token_logger import TokenLogger, UsageRecord


@pytest.fixture
def tmp_logger(tmp_path):
    return TokenLogger(tmp_path / "logs", "test_instance_001")


def test_log_creates_record(tmp_logger):
    record = tmp_logger.log(
        step=1, tool="read_file", model="deepseek-chat",
        input_tokens=1000, output_tokens=200, latency=1.5
    )
    assert isinstance(record, UsageRecord)
    assert record.total_tokens == 1200
    assert record.step == 1


def test_log_writes_jsonl(tmp_logger, tmp_path):
    tmp_logger.log(step=1, tool="search", model="test", input_tokens=500, output_tokens=100, latency=0.5)
    log_file = tmp_path / "logs" / "request_log.jsonl"
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["tool"] == "search"


def test_summary(tmp_logger):
    for i in range(3):
        tmp_logger.log(step=i+1, tool="read_file", model="test",
                       input_tokens=1000, output_tokens=200, latency=1.0)
    summary = tmp_logger.summary()
    assert summary["total_calls"] == 3
    assert summary["total_tokens"] == 3600
    assert summary["input_tokens"] == 3000


def test_save_summary(tmp_logger, tmp_path):
    tmp_logger.log(step=1, tool="edit", model="test",
                   input_tokens=2000, output_tokens=500, latency=2.0)
    out = tmp_logger.save_summary(success=True)
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["success"] is True
    assert data["total_tokens"] == 2500
