"""
Optimization utilities for TCO model calculations.

This module provides performance optimizations and caching mechanisms
to improve calculation speed and efficiency for the TCO model.
"""

import functools
import time
import logging
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union, cast

import numpy as np
import pandas as pd

# Set up module logger
logger = logging.getLogger(__name__)

# Type variable for generic function annotations
T = TypeVar('T')
R = TypeVar('R')

class PerformanceMonitor:
    """
    A utility class for monitoring the performance of model calculations.
    
    Provides timing and profiling capabilities to identify bottlenecks.
    """
    
    def __init__(self):
        self.timings: Dict[str, float] = {}
        self.call_counts: Dict[str, int] = {}
    
    def reset(self) -> None:
        """Reset all performance metrics."""
        self.timings = {}
        self.call_counts = {}
    
    def get_report(self) -> Dict[str, Any]:
        """
        Get a report of all performance metrics.
        
        Returns:
            Dict containing timing and call count information
        """
        report = {
            'timings': {k: round(v, 4) for k, v in self.timings.items()},
            'call_counts': self.call_counts.copy(),
            'avg_times': {
                k: round(v / self.call_counts.get(k, 1), 4) 
                for k, v in self.timings.items()
            }
        }
        
        # Calculate total time and percentage breakdown
        total_time = sum(self.timings.values())
        if total_time > 0:
            report['total_time'] = round(total_time, 4)
            report['percentages'] = {
                k: round((v / total_time) * 100, 2) 
                for k, v in self.timings.items()
            }
        
        return report
    
    def print_report(self) -> None:
        """Print a formatted performance report to the console."""
        report = self.get_report()
        
        print("\n===== PERFORMANCE REPORT =====")
        print(f"Total execution time: {report.get('total_time', 0):.4f} seconds")
        print("\nBreakdown by function:")
        
        # Sort by total time spent (descending)
        sorted_funcs = sorted(
            self.timings.keys(), 
            key=lambda x: self.timings.get(x, 0), 
            reverse=True
        )
        
        for func in sorted_funcs:
            time_spent = self.timings.get(func, 0)
            calls = self.call_counts.get(func, 0)
            avg_time = time_spent / calls if calls > 0 else 0
            percentage = report.get('percentages', {}).get(func, 0)
            
            print(f"  {func}:")
            print(f"    Time: {time_spent:.4f}s ({percentage:.1f}%)")
            print(f"    Calls: {calls}")
            print(f"    Avg time: {avg_time:.6f}s")
        
        print("================================")


# Create a global instance for use across the application
performance_monitor = PerformanceMonitor()


def timed(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator that times the execution of a function and records metrics.
    
    Args:
        func: The function to be timed
        
    Returns:
        Wrapped function that performs the same operation with timing
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        # Record timing information
        func_name = func.__qualname__
        performance_monitor.timings[func_name] = (
            performance_monitor.timings.get(func_name, 0) + elapsed
        )
        performance_monitor.call_counts[func_name] = (
            performance_monitor.call_counts.get(func_name, 0) + 1
        )
        
        return result
    
    return wrapper


class ModelCache:
    """
    Cache utility for expensive model calculations.
    
    Manages a cache of calculation results and provides automatic invalidation
    based on dependencies.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize a new cache with specified maximum size.
        
        Args:
            max_size: Maximum number of items to store in the cache
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._max_size = max_size
        self._hit_count = 0
        self._miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value or None if not found
        """
        if key in self._cache:
            self._hit_count += 1
            # Return the value (index 0), not the timestamp
            return self._cache[key][0]
        
        self._miss_count += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
        """
        # If cache is full, remove oldest item
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        # Store value with current timestamp
        self._cache[key] = (value, time.time())
    
    def invalidate(self, key_prefix: str = "") -> int:
        """
        Invalidate cache entries that start with a specific prefix.
        
        Args:
            key_prefix: Prefix to match for invalidation
            
        Returns:
            Number of invalidated cache entries
        """
        keys_to_delete = [k for k in self._cache if k.startswith(key_prefix)]
        for key in keys_to_delete:
            del self._cache[key]
        
        return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_queries = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_queries * 100) if total_queries > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hits': self._hit_count,
            'misses': self._miss_count,
            'hit_rate_pct': round(hit_rate, 2)
        }


# Create a global cache instance for use across model calculations
model_cache = ModelCache(max_size=200)


def cached(key_format: str) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator that caches function results based on a key template.
    
    Args:
        key_format: String template for the cache key, can include parameter names
            in curly braces, e.g. "calculate_tco:{scenario.name}"
            
    Returns:
        Decorated function that uses caching
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Bind arguments to function parameters
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Create a context for string formatting
            format_context = {}
            for name, value in bound_args.arguments.items():
                # For simple types, use directly
                if isinstance(value, (str, int, float, bool)) or value is None:
                    format_context[name] = value
                # For objects, add attributes
                elif hasattr(value, '__dict__'):
                    format_context[name] = value
                    # Add common attributes like name, id, etc.
                    if hasattr(value, 'name'):
                        format_context[f"{name}_name"] = value.name
                    if hasattr(value, 'id'):
                        format_context[f"{name}_id"] = value.id
            
            try:
                # Format the cache key using the arguments
                cache_key = key_format.format(**format_context)
                
                # Check if result is in cache
                cached_result = model_cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__} with key '{cache_key}'")
                    return cached_result
                
                # If not in cache, compute and store
                logger.debug(f"Cache miss for {func.__name__} with key '{cache_key}'")
                result = func(*args, **kwargs)
                model_cache.set(cache_key, result)
                return result
                
            except Exception as e:
                # If key formatting or cache lookup fails, fall back to uncached call
                logger.warning(f"Cache error in {func.__name__}: {e}. Falling back to uncached.")
                return func(*args, **kwargs)
                
        return wrapper
    
    return decorator


def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize a DataFrame for memory usage and performance.
    
    Applies memory-saving techniques like downcast and category conversion.
    
    Args:
        df: DataFrame to optimize
        
    Returns:
        Optimized DataFrame with reduced memory footprint
    """
    result = df.copy()
    
    # Optimize numeric columns
    for col in result.select_dtypes(include=['int']).columns:
        result[col] = pd.to_numeric(result[col], downcast='integer')
        
    for col in result.select_dtypes(include=['float']).columns:
        result[col] = pd.to_numeric(result[col], downcast='float')
    
    # Convert object columns with few unique values to category
    for col in result.select_dtypes(include=['object']).columns:
        if result[col].nunique() / len(result) < 0.5:  # If less than 50% unique values
            result[col] = result[col].astype('category')
    
    return result


def batch_process(data: pd.DataFrame, func: Callable[[pd.DataFrame], pd.DataFrame], 
                 batch_size: int = 1000) -> pd.DataFrame:
    """
    Process a large DataFrame in batches to reduce memory pressure.
    
    Args:
        data: Input DataFrame to process
        func: Function to apply to each batch
        batch_size: Number of rows per batch
        
    Returns:
        Processed DataFrame
    """
    if len(data) <= batch_size:
        return func(data)
    
    results = []
    for start_idx in range(0, len(data), batch_size):
        end_idx = min(start_idx + batch_size, len(data))
        batch = data.iloc[start_idx:end_idx]
        results.append(func(batch))
    
    return pd.concat(results, ignore_index=True)


def vectorized_calculation(func: Callable[[float], float]) -> Callable[[np.ndarray], np.ndarray]:
    """
    Convert a scalar function to a vectorized one that can operate on arrays.
    
    Args:
        func: Function that operates on a single value
        
    Returns:
        Vectorized function that operates on arrays
    """
    return np.vectorize(func)