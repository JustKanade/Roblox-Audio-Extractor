#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多进程处理工具模块 - 提供高性能多进程处理功能
Multiprocessing Utilities Module - Provides high-performance multiprocessing capabilities
作者/Author: JustKanade
"""

import os
import time
import multiprocessing
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Callable

# 简单的日志打印函数
def _log_info(message):
    print(f"[INFO] {message}")

def _log_error(message):
    print(f"[ERROR] {message}")


class MultiprocessingStats:
    """多进程统计信息管理"""
    
    def __init__(self, manager: Optional[multiprocessing.Manager] = None):
        """初始化多进程统计"""
        if manager is None:
            manager = multiprocessing.Manager()
        
        self.stats = manager.dict({
            'processed_files': 0,
            'duplicate_files': 0,
            'error_files': 0,
            'already_processed': 0,
            'start_time': time.time()
        })
        self._lock = manager.Lock()
    
    def increment(self, key: str, value: int = 1):
        """原子性地增加统计值"""
        with self._lock:
            if key in self.stats:
                self.stats[key] += value
            else:
                self.stats[key] = value
    
    def set(self, key: str, value: Any):
        """设置统计值"""
        with self._lock:
            self.stats[key] = value
    
    def get(self, key: str) -> Any:
        """获取统计值"""
        with self._lock:
            return self.stats.get(key, 0)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有统计值"""
        with self._lock:
            return dict(self.stats)


class ProcessingConfig:
    """多进程处理配置"""
    
    def __init__(self, 
                 base_dir: str,
                 output_dir: str,
                 classification_method: Any,
                 processed_hashes: Optional[List[str]] = None,
                 content_hashes: Optional[List[str]] = None,
                 scan_db: bool = True,
                 **kwargs):
        """初始化处理配置"""
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.classification_method = classification_method
        self.processed_hashes = set(processed_hashes or [])
        self.content_hashes = set(content_hashes or [])
        self.scan_db = scan_db
        self.extra_config = kwargs


def get_optimal_process_count(max_processes: Optional[int] = None, 
                            conservative: bool = True) -> int:
    """获取最优进程数量
    
    Args:
        max_processes: 最大进程数限制
        conservative: 是否使用保守策略 (cpu_count vs cpu_count + 1)
    
    Returns:
        优化的进程数量
    """
    cpu_count = multiprocessing.cpu_count()
    
    if conservative:
        # 保守策略：cpu_count 或 cpu_count + 1
        optimal_count = cpu_count + 1 if cpu_count <= 4 else cpu_count
    else:
        # 原有策略：min(32, cpu_count * 2)
        optimal_count = min(32, cpu_count * 2)
    
    if max_processes:
        optimal_count = min(optimal_count, max_processes)
    
    return max(1, optimal_count)


def chunk_list(items: List[Any], chunk_size: Optional[int] = None, 
               num_chunks: Optional[int] = None) -> List[List[Any]]:
    """将列表分割成多个块用于多进程处理
    
    Args:
        items: 要分割的列表
        chunk_size: 每个块的大小
        num_chunks: 总块数（与chunk_size互斥）
    
    Returns:
        分割后的块列表
    """
    if not items:
        return []
    
    if num_chunks is not None:
        chunk_size = max(1, len(items) // num_chunks)
        if len(items) % num_chunks:
            chunk_size += 1
    elif chunk_size is None:
        # 默认根据CPU数量分块
        num_processes = get_optimal_process_count()
        chunk_size = max(1, len(items) // num_processes)
    
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        if chunk:  # 确保不添加空块
            chunks.append(chunk)
    
    return chunks


class MultiprocessingManager:
    """多进程管理器 - 使用原生multiprocessing避免concurrent.futures的logging依赖"""
    
    def __init__(self, 
                 num_processes: Optional[int] = None,
                 conservative: bool = True,
                 progress_callback: Optional[Callable] = None,
                 cancel_check: Optional[Callable] = None):
        """初始化多进程管理器
        
        Args:
            num_processes: 进程数量
            conservative: 是否使用保守的进程数量策略
            progress_callback: 进度回调函数
            cancel_check: 取消检查函数
        """
        # 确保Windows上的多进程正确启动
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            # start_method 已经设置过了
            pass
            
        self.num_processes = num_processes or get_optimal_process_count(conservative=conservative)
        self.progress_callback = progress_callback
        self.cancel_check = cancel_check
        self.manager = multiprocessing.Manager()
        self.stats = MultiprocessingStats(self.manager)
        
        # 创建共享的取消标志
        self.cancelled = self.manager.Value('b', False)
        
        _log_info(f"初始化多进程管理器: {self.num_processes} 个进程")
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        if self.cancel_check and self.cancel_check():
            self.cancelled.value = True
        return self.cancelled.value
    
    def cancel(self):
        """取消处理"""
        self.cancelled.value = True
    
    def process_items(self, 
                     items: List[Any],
                     worker_func: Callable,
                     config: ProcessingConfig,
                     chunk_size: Optional[int] = None) -> Dict[str, Any]:
        """使用多进程处理项目列表 - 原生multiprocessing实现
        
        Args:
            items: 要处理的项目列表
            worker_func: 工作函数
            config: 处理配置
            chunk_size: 块大小
        
        Returns:
            处理结果统计和成功处理的哈希列表
        """
        if not items:
            return {'stats': self.stats.get_all(), 'processed_hashes': []}
        
        # 分割任务
        chunks = chunk_list(items, chunk_size=chunk_size, num_chunks=self.num_processes)
        total_chunks = len(chunks)
        
        _log_info(f"开始多进程处理: {len(items)} 个项目分成 {total_chunks} 个块")
        
        start_time = time.time()
        self.stats.set('start_time', start_time)
        completed_chunks = 0
        
        # 收集所有处理的哈希
        all_processed_hashes = []
        
        try:
            # 使用原生multiprocessing.Pool
            with multiprocessing.Pool(processes=self.num_processes) as pool:
                # 提交所有任务
                results = []
                for chunk_idx, chunk in enumerate(chunks):
                    result = pool.apply_async(worker_func, (chunk, config, self.cancelled))
                    results.append((chunk_idx, result))
                
                # 等待所有任务完成
                for chunk_idx, result in results:
                    if self.is_cancelled():
                        _log_info("检测到取消信号，正在停止处理...")
                        break
                    
                    try:
                        # 获取结果
                        chunk_result = result.get(timeout=60)  # 60秒超时
                        if chunk_result:
                            # 合并统计结果
                            chunk_stats = chunk_result.get('stats', {})
                            for key, value in chunk_stats.items():
                                if isinstance(value, (int, float)):
                                    self.stats.increment(key, value)
                            
                            # 收集处理的哈希
                            chunk_hashes = chunk_result.get('processed_hashes', [])
                            all_processed_hashes.extend(chunk_hashes)
                        
                        completed_chunks += 1
                        
                        # 调用进度回调（降低频率）
                        if self.progress_callback and completed_chunks % max(1, total_chunks // 10) == 0:
                            progress = completed_chunks / total_chunks
                            elapsed = time.time() - start_time
                            self.progress_callback(completed_chunks, total_chunks, elapsed, progress)
                    
                    except Exception as e:
                        _log_error(f"处理块 {chunk_idx} 时出错: {e}")
                        self.stats.increment('error_files', len(chunks[chunk_idx]))
        
        except Exception as e:
            _log_error(f"多进程处理出现严重错误: {e}")
        
        # 计算最终时间
        end_time = time.time()
        total_time = end_time - start_time
        
        final_stats = self.stats.get_all()
        final_stats['total_time'] = total_time
        
        if total_time > 0:
            items_per_second = len(items) / total_time
            _log_info(f"多进程处理完成: 用时 {total_time:.2f}秒, 处理速度 {items_per_second:.2f} 项/秒")
        
        return {'stats': final_stats, 'processed_hashes': all_processed_hashes}


def _multiprocessing_worker(items: List[Any], config: ProcessingConfig, cancelled) -> Dict[str, Any]:
    """多进程工作函数 - 必须在模块级别定义以支持pickle序列化
    
    Args:
        items: 要处理的项目列表（已经预处理去重）
        config: 处理配置
        cancelled: 共享的取消标志
    
    Returns:
        当前进程的统计结果和成功处理的哈希列表
    """
    stats = {
        'processed_files': 0,
        'duplicate_files': 0,
        'error_files': 0,
        'already_processed': 0
    }
    
    # 收集成功处理的哈希
    processed_hashes = []
    
    # 导入处理函数 - 必须在工作进程中导入
    try:
        from src.extractors.audio_extractor import _process_file_worker
    except ImportError:
        _log_error("无法导入 _process_file_worker")
        return {'stats': stats, 'processed_hashes': processed_hashes}
    
    for item in items:
        if cancelled.value:
            break
            
        try:
            result = _process_file_worker(item, config)
            
            if result['success'] is True:
                # 文件已经预处理去重，直接计为成功处理
                file_hash = result.get('file_hash')
                if file_hash:
                    processed_hashes.append(file_hash)
                
                stats['processed_files'] += 1
                    
            elif result['success'] is False:
                # 保存失败 - 应该计为错误文件
                stats['error_files'] += 1
                error_msg = result.get('error', '未知错误')
                _log_error(f"保存文件 {item} 失败: {error_msg}")
                
            elif result['success'] is None:
                if result.get('error'):
                    stats['error_files'] += 1
                else:
                    stats['already_processed'] += 1
                    
        except Exception as e:
            stats['error_files'] += 1
            _log_error(f"处理项目 {item} 时出错: {e}")
    
    return {'stats': stats, 'processed_hashes': processed_hashes}


def create_worker_function(process_func: Callable) -> Callable:
    """创建多进程工作函数包装器 - 返回模块级函数避免pickle问题
    
    Args:
        process_func: 实际的处理函数（当前未使用，直接使用硬编码的worker）
    
    Returns:
        适用于多进程的工作函数
    """
    return _multiprocessing_worker


# 便捷函数
def enable_multiprocessing_logging():
    """启用多进程安全的日志记录"""
    import multiprocessing
    
    # 确保日志在多进程环境中正常工作
    multiprocessing.set_start_method('spawn', force=True)
    
    # 使用简单的打印代替logging
    _log_info("多进程日志记录已启用")


def test_multiprocessing_performance():
    """测试多进程性能的简单函数"""
    import time
    import math
    
    def cpu_intensive_task(n):
        """CPU密集型任务用于测试"""
        result = 0
        for i in range(n):
            result += math.sqrt(i) * math.sin(i)
        return result
    
    def test_worker(items, config, cancelled):
        """测试工作函数"""
        results = []
        for item in items:
            if cancelled.value:
                break
            results.append(cpu_intensive_task(item))
        return {'processed': len(results)}
    
    # 测试数据
    test_items = [10000] * 20
    config = ProcessingConfig("", "", None)
    
    # 单进程测试
    start_time = time.time()
    for item in test_items:
        cpu_intensive_task(item)
    single_time = time.time() - start_time
    
    # 多进程测试
    manager = MultiprocessingManager(conservative=True)
    start_time = time.time()
    manager.process_items(test_items, test_worker, config)
    multi_time = time.time() - start_time
    
    print(f"单进程时间: {single_time:.2f}秒")
    print(f"多进程时间: {multi_time:.2f}秒")
    print(f"加速比: {single_time/multi_time:.2f}x")


if __name__ == "__main__":
    # 运行性能测试
    enable_multiprocessing_logging()
    test_multiprocessing_performance() 