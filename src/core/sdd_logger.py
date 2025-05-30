"""
Centralized logging configuration for Specification-Driven Development (SDD) system.

This module provides structured logging with correlation IDs to trace generation requests
through their entire lifecycle from specification to output code.
"""

import json
import logging
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from threading import local

# Thread-local storage for correlation context
_context = local()


class CorrelationFilter(logging.Filter):
    """Logging filter that adds correlation ID and context to log records."""
    
    def filter(self, record):
        # Add correlation ID
        record.correlation_id = getattr(_context, 'correlation_id', 'no-correlation')
        
        # Add context information
        record.component = getattr(_context, 'component', 'unknown')
        record.operation = getattr(_context, 'operation', 'unknown')
        record.request_id = getattr(_context, 'request_id', 'no-request')
        
        return True


class SDDJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'component': getattr(record, 'component', 'unknown'),
            'operation': getattr(record, 'operation', 'unknown'),
            'correlation_id': getattr(record, 'correlation_id', 'no-correlation'),
            'request_id': getattr(record, 'request_id', 'no-request'),
            'message': record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry['data'] = record.extra_data
            
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
            
        if hasattr(record, 'quality_score'):
            log_entry['quality_score'] = record.quality_score
            
        if hasattr(record, 'iteration'):
            log_entry['iteration'] = record.iteration
            
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, default=str)


class SDDLogger:
    """Main logger class for SDD system with correlation tracking."""
    
    def __init__(self, name: str, log_level: str = "INFO", log_file: Optional[Path] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Add correlation filter
        correlation_filter = CorrelationFilter()
        
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(SDDJSONFormatter())
        console_handler.addFilter(correlation_filter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(SDDJSONFormatter())
            file_handler.addFilter(correlation_filter)
            self.logger.addHandler(file_handler)
    
    @contextmanager
    def correlation_context(self, correlation_id: Optional[str] = None, 
                           component: str = "unknown", 
                           operation: str = "unknown",
                           request_id: Optional[str] = None):
        """Context manager for correlation tracking."""
        old_correlation_id = getattr(_context, 'correlation_id', None)
        old_component = getattr(_context, 'component', None)
        old_operation = getattr(_context, 'operation', None)
        old_request_id = getattr(_context, 'request_id', None)
        
        _context.correlation_id = correlation_id or str(uuid.uuid4())
        _context.component = component
        _context.operation = operation
        _context.request_id = request_id or str(uuid.uuid4())
        
        try:
            yield _context.correlation_id
        finally:
            _context.correlation_id = old_correlation_id
            _context.component = old_component
            _context.operation = old_operation
            _context.request_id = old_request_id
    
    @contextmanager
    def timed_operation(self, operation_name: str, **extra_data):
        """Context manager for timing operations."""
        start_time = time.time()
        
        self.info(f"Starting {operation_name}", extra_data=extra_data)
        
        try:
            yield
            duration_ms = int((time.time() - start_time) * 1000)
            self.info(f"Completed {operation_name}", 
                     duration_ms=duration_ms, 
                     extra_data=extra_data)
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.error(f"Failed {operation_name}: {e}", 
                      duration_ms=duration_ms, 
                      extra_data=extra_data)
            raise
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional extra data."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional extra data."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional extra data."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional extra data."""
        self._log(logging.ERROR, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method that handles extra data."""
        extra = {}
        
        # Extract special logging fields
        if 'extra_data' in kwargs:
            extra['extra_data'] = kwargs.pop('extra_data')
        if 'duration_ms' in kwargs:
            extra['duration_ms'] = kwargs.pop('duration_ms')
        if 'quality_score' in kwargs:
            extra['quality_score'] = kwargs.pop('quality_score')
        if 'iteration' in kwargs:
            extra['iteration'] = kwargs.pop('iteration')
        
        # Any remaining kwargs go into extra_data
        if kwargs:
            extra['extra_data'] = {**(extra.get('extra_data', {})), **kwargs}
        
        self.logger.log(level, message, extra=extra)
    
    def log_mcp_call(self, server_name: str, tool_name: str, arguments: Dict[str, Any], 
                     result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Log MCP server tool calls."""
        call_data = {
            'server': server_name,
            'tool': tool_name,
            'arguments': arguments
        }
        
        if result:
            call_data['result_type'] = type(result).__name__
            call_data['result_keys'] = list(result.keys()) if isinstance(result, dict) else None
            self.debug(f"MCP call successful: {server_name}.{tool_name}", extra_data=call_data)
        elif error:
            call_data['error'] = error
            self.error(f"MCP call failed: {server_name}.{tool_name}", extra_data=call_data)
        else:
            self.debug(f"MCP call initiated: {server_name}.{tool_name}", extra_data=call_data)
    
    def log_iteration_start(self, iteration: int, max_iterations: int, target_quality: int):
        """Log start of iteration cycle."""
        self.info(f"Starting iteration {iteration}/{max_iterations}", 
                 iteration=iteration,
                 extra_data={
                     'max_iterations': max_iterations,
                     'target_quality_score': target_quality
                 })
    
    def log_iteration_complete(self, iteration: int, quality_score: int, 
                              improvements: list, issues_addressed: list):
        """Log completion of iteration cycle."""
        self.info(f"Completed iteration {iteration} with quality score {quality_score}",
                 iteration=iteration,
                 quality_score=quality_score,
                 extra_data={
                     'improvements': improvements,
                     'issues_addressed': issues_addressed
                 })
    
    def log_quality_metrics(self, component: str, metrics: Dict[str, Any]):
        """Log quality metrics."""
        self.info(f"Quality metrics for {component}",
                 extra_data={
                     'component': component,
                     'metrics': metrics
                 })
    
    def log_specification_loaded(self, spec_path: str, scenarios_count: int, 
                                constraints_count: int):
        """Log specification loading."""
        self.info(f"Loaded specification from {spec_path}",
                 extra_data={
                     'specification_path': spec_path,
                     'scenarios_count': scenarios_count,
                     'constraints_count': constraints_count
                 })
    
    def log_code_generation(self, framework: str, optimization_level: str, 
                           scenarios_count: int, lines_generated: int):
        """Log code generation completion."""
        self.info(f"Generated {lines_generated} lines of code",
                 extra_data={
                     'framework': framework,
                     'optimization_level': optimization_level,
                     'scenarios_count': scenarios_count,
                     'lines_generated': lines_generated
                 })
    
    def log_test_results(self, test_type: str, passed: int, failed: int, 
                        success_rate: float):
        """Log test execution results."""
        level = logging.INFO if success_rate >= 0.8 else logging.WARNING
        self.logger.log(level, f"Test results for {test_type}: {passed}/{passed+failed} passed",
                       extra={
                           'extra_data': {
                               'test_type': test_type,
                               'passed': passed,
                               'failed': failed,
                               'success_rate': success_rate
                           }
                       })
    
    def log_constraint_verification(self, constraint_type: str, status: str, 
                                   details: Dict[str, Any]):
        """Log constraint verification results."""
        level = logging.INFO if status == 'passed' else logging.WARNING
        self.logger.log(level, f"Constraint verification: {constraint_type} {status}",
                       extra={
                           'extra_data': {
                               'constraint_type': constraint_type,
                               'verification_status': status,
                               'details': details
                           }
                       })


# Global logger instances
_loggers: Dict[str, SDDLogger] = {}


def get_logger(name: str, log_level: str = "INFO", 
               log_file: Optional[Union[str, Path]] = None) -> SDDLogger:
    """Get or create a logger instance."""
    if name not in _loggers:
        log_file_path = Path(log_file) if log_file else None
        _loggers[name] = SDDLogger(name, log_level, log_file_path)
    return _loggers[name]


def configure_logging(log_level: str = "INFO", 
                     log_file: Optional[Union[str, Path]] = None):
    """Configure global logging settings."""
    # Clear existing loggers
    _loggers.clear()
    
    # Set up root logger
    root_logger = get_logger("sdd", log_level, log_file)
    
    return root_logger


# Convenience function for getting the main SDD logger
def get_sdd_logger() -> SDDLogger:
    """Get the main SDD logger."""
    return get_logger("sdd")