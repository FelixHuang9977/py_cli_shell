#!/usr/bin/env python3
import os
import json
import psutil
from testcase.base_test import BaseTest


class TestCPUCore(BaseTest):
    """Test case for CPU core number verification."""

    def setup_method(self):
        """Setup method to initialize test parameters."""
        self.config = self._load_cpu_config()
        self.logger.info("Starting CPU core test")
        self.logger.debug(f"Loaded configuration: {self.config}")

    def _load_cpu_config(self):
        """Load CPU configuration from config file."""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
            "cpu_config.json"
        )
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config.get('expected_cores', {})
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file: {config_path}")
            return {}

    def get_cpu_core_info(self):
        """Get detailed CPU core information."""
        self.logger.debug("Collecting CPU core information")
        cpu_info = {
            'logical_cores': psutil.cpu_count(),
            'physical_cores': psutil.cpu_count(logical=False),
            'sockets': None
        }

        try:
            socket_info = self.run_command("lscpu | grep 'Socket(s):'")
            if socket_info:
                socket_line = socket_info.strip()
                cpu_info['sockets'] = int(socket_line.split(':')[1].strip())
                self.logger.debug(f"Found socket information: {socket_info}")
        except Exception as e:
            self.logger.warning(f"Unable to get socket information: {str(e)}")

        return cpu_info

    def print_cpu_info(self, cpu_info):
        """Print CPU information in a formatted way."""
        self.logger.info("=" * 50)
        self.logger.info("CPU Core Information:")
        self.logger.info("-" * 50)
        # 基本 CPU 資訊
        self.logger.info("Logical CPU cores (包含超執行緒):")
        self.logger.info(f"  - Current: {cpu_info['logical_cores']}")
        self.logger.info(f"  - Expected: {self.config.get('logical_cores', 'Not specified')}")
        
        self.logger.info("\nPhysical CPU cores (實體核心數):")
        self.logger.info(f"  - Current: {cpu_info['physical_cores']}")
        self.logger.info(f"  - Expected: {self.config.get('physical_cores', 'Not specified')}")
        
        if cpu_info['sockets'] is not None:
            self.logger.info("\nCPU Sockets (CPU 插槽數):")
            self.logger.info(f"  - Current: {cpu_info['sockets']}")
            self.logger.info(f"  - Expected: {self.config.get('sockets', 'Not specified')}")
        
        # 計算每核心執行緒數
        if cpu_info['logical_cores'] and cpu_info['physical_cores']:
            threads_per_core = cpu_info['logical_cores'] / cpu_info['physical_cores']
            self.logger.info(f"\nThreads per core (每核心執行緒數): {threads_per_core:.1f}")
        
        self.logger.info("=" * 50)

    def test_cpu_core_count(self):
        """Test if the CPU core count matches the expected number."""
        self.logger.info("Starting CPU core count test")
        cpu_info = self.get_cpu_core_info()
        
        # 顯示詳細的 CPU 資訊
        self.print_cpu_info(cpu_info)

        # 顯示 CPU 型號資訊
        cpu_model = self.run_command("lscpu | grep 'Model name'")
        if cpu_model:
            self.logger.info("\nCPU Model Information:")
            self.logger.info(cpu_model.strip())

        # 執行測試驗證
        self.logger.debug("Verifying CPU core counts")
        assert cpu_info['logical_cores'] > 0, "Failed to detect logical CPU cores"
        assert cpu_info['physical_cores'] > 0, "Failed to detect physical CPU cores"

        if 'logical_cores' in self.config:
            assert cpu_info['logical_cores'] == self.config['logical_cores'], \
                f"Expected {self.config['logical_cores']} logical cores, but found {cpu_info['logical_cores']}"

        if 'physical_cores' in self.config:
            assert cpu_info['physical_cores'] == self.config['physical_cores'], \
                f"Expected {self.config['physical_cores']} physical cores, but found {cpu_info['physical_cores']}"

        if 'sockets' in self.config and cpu_info['sockets']:
            assert cpu_info['sockets'] == self.config['sockets'], \
                f"Expected {self.config['sockets']} CPU sockets, but found {cpu_info['sockets']}"

        self.logger.info("CPU core count test completed successfully")

    def test_cpu_core_status(self):
        """Test if all CPU cores are functioning and online."""
        self.logger.info("Starting CPU core status test")
        
        try:
            # CPU 拓撲資訊
            self.logger.info("\nCPU Core Details:")
            self.logger.info("-" * 50)
            
            cpu_topology = self.run_command("lscpu -e")
            if cpu_topology:
                self.logger.info("CPU topology information:")
                self.logger.info(cpu_topology)

            # CPU 使用率檢查
            self.logger.debug("Collecting CPU utilization data")
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            
            self.logger.info("\nCPU Core Utilization:")
            self.logger.info("-" * 50)
            for core_id, usage in enumerate(cpu_percent):
                self.logger.info(f"Core {core_id}: {usage}%")

            # 驗證核心數量
            assert len(cpu_percent) == psutil.cpu_count(), \
                "Number of CPU usage metrics doesn't match core count"

            # 驗證每個核心的狀態
            for core_id, usage in enumerate(cpu_percent):
                assert isinstance(usage, (int, float)), \
                    f"Core {core_id} is not reporting valid usage data"

            self.logger.info("CPU core status test completed successfully")

        except Exception as e:
            self.logger.error(f"Error checking CPU core status: {str(e)}")
            raise
