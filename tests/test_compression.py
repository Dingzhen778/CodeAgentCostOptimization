"""Context Compression 单元测试"""
import pytest
from src.compression.context_compressor import (
    ContextCompressor, CompressionConfig,
    TopKFileSelector, FunctionLevelTrimmer, TokenBudgetTrimmer,
    count_tokens,
)


@pytest.fixture
def sample_files():
    return {
        "auth/views.py": "import os\n\ndef login(request):\n    pass\n\ndef logout():\n    pass\n" * 20,
        "utils/helpers.py": "import sys\n\ndef format_date(d):\n    return str(d)\n" * 10,
        "models/user.py": "class User:\n    def __init__(self):\n        self.name = ''\n" * 15,
        "settings.py": "DEBUG = True\nDATABASES = {}\n" * 5,
        "urls.py": "from django.urls import path\nurlpatterns = []\n" * 5,
        "irrelevant/deep.py": "x = 1\n" * 30,
    }


def test_topk_selector(sample_files):
    selector = TopKFileSelector(top_k=3)
    result = selector.select("fix login bug in auth views", sample_files)
    assert len(result) == 3
    assert "auth/views.py" in result  # 最相关的文件应被选中


def test_function_trimmer():
    code = """
import os
import sys

class MyClass:
    def unrelated_method(self):
        x = 1 + 2
        return x

def login_user(request):
    user = authenticate(request)
    return user

def process_data(data):
    for item in data:
        pass
""".strip()
    trimmer = FunctionLevelTrimmer(keep_imports=True)
    result = trimmer.trim(code, "login authentication bug")
    assert "login_user" in result   # 相关函数保留
    assert "import os" in result    # import 保留


def test_token_budget_trimmer(sample_files):
    trimmer = TokenBudgetTrimmer(token_budget=500)
    result = trimmer.trim(sample_files, "login bug")
    total_tokens = sum(count_tokens(c) for c in result.values())
    assert total_tokens <= 600  # 允许小幅超出（截断不精确）


def test_context_compressor_none(sample_files):
    compressor = ContextCompressor(CompressionConfig(strategy="none"))
    result = compressor.compress("any query", sample_files)
    assert result == sample_files  # none 策略不压缩


def test_context_compressor_hybrid(sample_files):
    compressor = ContextCompressor(CompressionConfig(
        strategy="hybrid", top_k_files=3, token_budget=2000
    ))
    result = compressor.compress("fix login bug", sample_files)
    assert len(result) <= 3
    ratio = compressor.compression_ratio(sample_files, result)
    assert ratio < 1.0  # 压缩后 token 更少
    print(f"Compression ratio: {ratio:.2f}")
