#!/usr/bin/env python3
"""
quick_test.py

快速验证框架各模块是否正常工作（不需要任何 API）

用法：
    python scripts/quick_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def test_token_logger():
    logger.info("Testing TokenLogger...")
    from src.gateway.token_logger import TokenLogger
    log = TokenLogger("/tmp/test_log", "test_instance_001", experiment="test", strategy="vanilla")
    for i in range(5):
        log.log(step=i+1, tool="read_file", model="deepseek-chat",
                input_tokens=1000 + i*100, output_tokens=200 + i*20, latency=1.2)
    summary = log.summary()
    assert summary["total_tokens"] > 0
    assert summary["total_calls"] == 5
    logger.info(f"  TokenLogger OK: {summary['total_tokens']} total tokens")


def test_trajectory():
    logger.info("Testing Trajectory...")
    from src.agent.trajectory import Trajectory
    traj = Trajectory("test_001", "/tmp/test_traj")
    traj.add(1, "search", "login bug", input_tokens=500, output_tokens=100)
    traj.add(2, "read_file", "auth/views.py", input_tokens=2000, output_tokens=80)
    traj.add(2, "read_file", "auth/views.py", input_tokens=2000, output_tokens=80)
    assert len(traj.unique_targets("read_file")) == 1
    assert traj.total_tokens() == (500+100 + 2000+80 + 2000+80)
    logger.info(f"  Trajectory OK: {len(traj.steps())} steps")


def test_compression():
    logger.info("Testing ContextCompressor...")
    from src.compression.context_compressor import ContextCompressor, CompressionConfig

    files = {
        f"module_{i}.py": f"import os\n\ndef function_{i}():\n    pass\n\n" * 50
        for i in range(10)
    }
    query = "fix login bug in function_3"
    compressor = ContextCompressor(CompressionConfig(strategy="topk", top_k_files=3))
    compressed = compressor.compress(query, files)
    ratio = compressor.compression_ratio(files, compressed)
    assert len(compressed) <= 3
    logger.info(f"  ContextCompressor OK: {len(files)} → {len(compressed)} files, ratio={ratio:.2f}")


def test_pruning():
    logger.info("Testing TrajectoryPruner...")
    from src.pruning.trajectory_pruner import (
        ActionContext, PruningConfig, PruningDecision, TrajectoryPruner
    )
    pruner = TrajectoryPruner(PruningConfig(
        enable_dedup=True, enable_step_limit=True, max_steps=5,
        enable_search_limit=True, max_search_calls=2,
    ))

    # 正常动作
    d = pruner.before_action(ActionContext(1, "read_file", "utils.py"))
    assert d == PruningDecision.ALLOW

    # 去重
    d = pruner.before_action(ActionContext(2, "read_file", "utils.py"))
    assert d == PruningDecision.SKIP, f"Expected SKIP, got {d}"

    # 超步骤
    d = pruner.before_action(ActionContext(10, "bash", "pytest"))
    assert d == PruningDecision.STOP

    stats = pruner.stats()
    logger.info(f"  TrajectoryPruner OK: {stats['total_pruned']} pruned actions")


def test_mock_runner():
    logger.info("Testing AgentRunner (mock)...")
    from src.agent.runner import AgentRunner
    config = {
        "experiment": "test_mock",
        "strategy": "mock",
        "agent": {"type": "mock"},
        "gateway": {},
        "output_dir": "/tmp/test_experiments",
    }
    runner = AgentRunner(config)
    instance = {"instance_id": "test__repo-99999"}
    result = runner.run(instance)
    assert result.instance_id == "test__repo-99999"
    assert result.token_summary.get("total_tokens", 0) > 0
    logger.info(f"  AgentRunner OK: tokens={result.token_summary['total_tokens']}, success={result.success}")


def main():
    tests = [
        test_token_logger,
        test_trajectory,
        test_compression,
        test_pruning,
        test_mock_runner,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            logger.error(f"  FAILED: {e}")

    logger.info(f"\n{'='*40}")
    logger.info(f"Results: {passed}/{len(tests)} tests passed")
    if passed == len(tests):
        logger.info("All tests passed! Framework is ready.")
    else:
        logger.warning("Some tests failed. Check the errors above.")


if __name__ == "__main__":
    main()
