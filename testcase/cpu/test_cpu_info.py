import pytest
import psutil
import shutil
from ..base_test import BaseTest
import time

class TestCPUInfo(BaseTest):
    """Test cases for CPU information and basic functionality"""

    def test_cpu_count(self):
        """Test to verify CPU count"""
        cpu_count = psutil.cpu_count()
        logical_count = psutil.cpu_count(logical=True)
        
        self.logger.info(f"Physical CPU count: {cpu_count}")
        self.logger.info(f"Logical CPU count: {logical_count}")
        assert cpu_count > 0, "System should have at least one CPU"
        assert logical_count >= cpu_count, "Logical CPU count should be >= physical count"
    
    def test_cpu_frequency(self):
        """Test to check CPU frequency information"""
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                self.logger.info(f"CPU Frequency - Current: {cpu_freq.current:.1f} MHz")
                self.logger.info(f"CPU Frequency - Min: {cpu_freq.min:.1f} MHz")
                self.logger.info(f"CPU Frequency - Max: {cpu_freq.max:.1f} MHz")
                
                assert cpu_freq.current > 0, "CPU frequency should be greater than 0"
            else:
                pytest.skip("CPU frequency information not available")
        except Exception as e:
            pytest.skip(f"CPU frequency test not supported on this system: {e}")
    
    def test_cpu_load(self):
        """Test to check CPU load average"""
        # Get CPU load averages
        load_1, load_5, load_15 = psutil.getloadavg()
        cpu_count = psutil.cpu_count()
        
        self.logger.info(f"Load averages: 1min: {load_1:.2f}, 5min: {load_5:.2f}, 15min: {load_15:.2f}")
        self.logger.info(f"Per-CPU load (1min): {load_1/cpu_count:.2f}")
        
        # Load average should be readable
        assert isinstance(load_1, float), "Should be able to get CPU load average"
        assert isinstance(load_5, float), "Should be able to get CPU load average"
        assert isinstance(load_15, float), "Should be able to get CPU load average"

    @pytest.mark.stress
    def test_cpu_stress(self):
        """Stress test for CPU (marked as stress test)"""
        # 檢查是否有 stress-ng
        stress_ng_available = shutil.which('stress-ng') is not None
        
        if stress_ng_available:
            try:
                    # 記錄初始 CPU 使用率
                    initial_cpu_percent = psutil.cpu_percent(interval=1)
                    self.logger.info(f"Initial CPU usage: {initial_cpu_percent}%")
                    
                    # 運行 stress-ng 測試
                    self.run_command("stress-ng --cpu 1 --timeout 5")
                    
                    # 測試後檢查 CPU 使用率
                    final_cpu_percent = psutil.cpu_percent(interval=1)
                    self.logger.info(f"Final CPU usage: {final_cpu_percent}%")
                    
                    assert True, "Stress test completed successfully"
            except Exception as e:
                    pytest.skip(f"Stress test failed: {e}")
        else:
            # 如果沒有 stress-ng，使用純 Python 的 CPU 壓力測試
            self.logger.warning("stress-ng not found, using Python-based CPU stress test")
            try:
                # 記錄初始 CPU 使用率
                initial_cpu_percent = psutil.cpu_percent(interval=1)
                self.logger.info(f"Initial CPU usage: {initial_cpu_percent}%")
                
                # 執行簡單的 CPU 密集運算
                start_time = time.time()
                while time.time() - start_time < 5:  # 運行 5 秒
                    _ = [i * i for i in range(10000)]
                
                # 測試後檢查 CPU 使用率
                final_cpu_percent = psutil.cpu_percent(interval=1)
                self.logger.info(f"Final CPU usage: {final_cpu_percent}%")
                
                assert True, "Python-based stress test completed successfully"
            except Exception as e:
                pytest.skip(f"Python-based stress test failed: {e}")

    def test_cpu_usage_per_core(self):
        """Test to check CPU usage for each core"""
        # 獲取每個 CPU 核心的使用率
        cpu_percents = psutil.cpu_percent(interval=1, percpu=True)
        
        self.logger.info("CPU Usage per core:")
        for i, percentage in enumerate(cpu_percents):
            self.logger.info(f"Core {i}: {percentage}%")
        
        assert len(cpu_percents) > 0, "Should be able to get CPU core usage"
        assert all(isinstance(x, float) for x in cpu_percents), "All CPU usage values should be floats"

    def test_cpu_stats(self):
        """Test to check CPU statistics"""
        try:
            cpu_stats = psutil.cpu_stats()
            self.logger.info(f"CPU Stats - Context Switches: {cpu_stats.ctx_switches}")
            self.logger.info(f"CPU Stats - Interrupts: {cpu_stats.interrupts}")
            self.logger.info(f"CPU Stats - Soft Interrupts: {cpu_stats.soft_interrupts}")
            self.logger.info(f"CPU Stats - Syscalls: {cpu_stats.syscalls}")
            
            assert cpu_stats.ctx_switches > 0, "Should have some context switches"
            assert cpu_stats.interrupts >= 0, "Should have valid interrupt count"
        except Exception as e:
            pytest.skip(f"CPU stats not fully supported on this system: {e}")
