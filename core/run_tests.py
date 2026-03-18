import pytest
import sys

if __name__ == "__main__":
    # 运行所有测试，包括子目录
    sys.exit(pytest.main(["-v", "tests/", "--tb=short"]))
