from typing import Dict, Any, List
from src.core.sdd_logger import get_logger


class ConstraintVerifier:
    """Verify and enforce constraints throughout the development process."""
    
    def __init__(self):
        self.logger = get_logger("sdd.constraint_verifier")
        self.verification_history = []
    
    def verify_constraints(self, implementation: Dict[str, Any], 
                          constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Verify implementation against all constraints."""
        
        with self.logger.correlation_context(component="constraint_verifier", 
                                           operation="verify_constraints"):
            self.logger.info("Starting constraint verification",
                           extra_data={
                               'constraint_types': list(constraints.keys()),
                               'constraint_count': sum(len(v) if isinstance(v, list) else 1 
                                                     for v in constraints.values())
                           })
            
            verification_result = {
                'overall_status': 'passed',
                'results_by_type': {},
                'failed_constraints': [],
                'warnings': [],
                'compliance_score': 0
            }
            
            total_constraints = 0
            passed_constraints = 0
            
            # Verify different constraint types
            for constraint_type, constraint_list in constraints.items():
                with self.logger.timed_operation(f"verify_{constraint_type}_constraints",
                                               constraint_type=constraint_type):
                    
                    type_result = self._verify_constraint_type(
                        implementation, constraint_type, constraint_list
                    )
                    
                    verification_result['results_by_type'][constraint_type] = type_result
                    
                    total_constraints += type_result['total']
                    passed_constraints += type_result['passed']
                    
                    if type_result['failed']:
                        verification_result['failed_constraints'].extend(type_result['failed'])
                    
                    if type_result['warnings']:
                        verification_result['warnings'].extend(type_result['warnings'])
                    
                    self.logger.log_constraint_verification(
                        constraint_type, 
                        'passed' if type_result['passed'] == type_result['total'] else 'failed',
                        type_result
                    )
            
            # Calculate compliance score
            verification_result['compliance_score'] = (
                (passed_constraints / total_constraints * 100) if total_constraints > 0 else 100
            )
            
            # Determine overall status
            if verification_result['failed_constraints']:
                verification_result['overall_status'] = 'failed'
            elif verification_result['warnings']:
                verification_result['overall_status'] = 'warning'
            
            self.logger.info(f"Constraint verification complete: {verification_result['overall_status']}",
                           extra_data={
                               'overall_status': verification_result['overall_status'],
                               'compliance_score': verification_result['compliance_score'],
                               'failed_count': len(verification_result['failed_constraints']),
                               'warning_count': len(verification_result['warnings'])
                           })
            
            self.verification_history.append(verification_result)
            return verification_result
    
    def _verify_constraint_type(self, implementation: Dict[str, Any], 
                               constraint_type: str, constraints: Any) -> Dict[str, Any]:
        """Verify constraints of a specific type."""
        
        result = {
            'type': constraint_type,
            'total': 0,
            'passed': 0,
            'failed': [],
            'warnings': []
        }
        
        if constraint_type == 'performance':
            return self._verify_performance_constraints(implementation, constraints, result)
        elif constraint_type == 'security':
            return self._verify_security_constraints(implementation, constraints, result)
        elif constraint_type == 'scalability':
            return self._verify_scalability_constraints(implementation, constraints, result)
        elif constraint_type == 'reliability':
            return self._verify_reliability_constraints(implementation, constraints, result)
        else:
            self.logger.warning(f"Unknown constraint type: {constraint_type}")
            return result
    
    def _verify_performance_constraints(self, implementation: Dict[str, Any], 
                                       constraints: List[Dict], result: Dict) -> Dict[str, Any]:
        """Verify performance constraints."""
        
        for constraint in constraints if isinstance(constraints, list) else [constraints]:
            result['total'] += 1
            
            constraint_name = constraint.get('name', 'unnamed')
            requirement = constraint.get('requirement', '')
            
            self.logger.debug(f"Verifying performance constraint: {constraint_name}",
                            extra_data={'constraint': constraint})
            
            # Simple heuristic-based verification for now
            if 'latency' in requirement.lower() or 'response time' in requirement.lower():
                if self._check_latency_constraint(implementation, constraint):
                    result['passed'] += 1
                else:
                    result['failed'].append({
                        'name': constraint_name,
                        'type': 'performance',
                        'requirement': requirement,
                        'reason': 'Latency requirement may not be met'
                    })
            elif 'throughput' in requirement.lower() or 'rps' in requirement.lower():
                if self._check_throughput_constraint(implementation, constraint):
                    result['passed'] += 1
                else:
                    result['failed'].append({
                        'name': constraint_name,
                        'type': 'performance',
                        'requirement': requirement,
                        'reason': 'Throughput requirement may not be met'
                    })
            else:
                result['warnings'].append(f"Cannot verify performance constraint: {constraint_name}")
        
        return result
    
    def _verify_security_constraints(self, implementation: Dict[str, Any], 
                                    constraints: List[Dict], result: Dict) -> Dict[str, Any]:
        """Verify security constraints."""
        
        for constraint in constraints if isinstance(constraints, list) else [constraints]:
            result['total'] += 1
            
            constraint_name = constraint.get('name', 'unnamed')
            requirement = constraint.get('requirement', '')
            
            self.logger.debug(f"Verifying security constraint: {constraint_name}",
                            extra_data={'constraint': constraint})
            
            if self._check_security_constraint(implementation, constraint):
                result['passed'] += 1
            else:
                result['failed'].append({
                    'name': constraint_name,
                    'type': 'security',
                    'requirement': requirement,
                    'reason': 'Security requirement may not be implemented'
                })
        
        return result
    
    def _verify_scalability_constraints(self, implementation: Dict[str, Any], 
                                       constraints: List[Dict], result: Dict) -> Dict[str, Any]:
        """Verify scalability constraints."""
        
        for constraint in constraints if isinstance(constraints, list) else [constraints]:
            result['total'] += 1
            
            constraint_name = constraint.get('name', 'unnamed')
            
            if self._check_scalability_constraint(implementation, constraint):
                result['passed'] += 1
            else:
                result['failed'].append({
                    'name': constraint_name,
                    'type': 'scalability',
                    'requirement': constraint.get('requirement', ''),
                    'reason': 'Scalability requirement may not be met'
                })
        
        return result
    
    def _verify_reliability_constraints(self, implementation: Dict[str, Any], 
                                       constraints: List[Dict], result: Dict) -> Dict[str, Any]:
        """Verify reliability constraints."""
        
        for constraint in constraints if isinstance(constraints, list) else [constraints]:
            result['total'] += 1
            
            constraint_name = constraint.get('name', 'unnamed')
            
            if self._check_reliability_constraint(implementation, constraint):
                result['passed'] += 1
            else:
                result['failed'].append({
                    'name': constraint_name,
                    'type': 'reliability',
                    'requirement': constraint.get('requirement', ''),
                    'reason': 'Reliability requirement may not be implemented'
                })
        
        return result
    
    def _check_latency_constraint(self, implementation: Dict[str, Any], constraint: Dict) -> bool:
        """Check if implementation likely meets latency constraints."""
        code = implementation.get('main_module', '')
        
        # Simple heuristics
        has_caching = 'cache' in code.lower()
        has_async = 'async' in code or 'await' in code
        has_db_optimization = 'index' in code.lower() or 'query' in code.lower()
        
        return has_async or has_caching or has_db_optimization
    
    def _check_throughput_constraint(self, implementation: Dict[str, Any], constraint: Dict) -> bool:
        """Check if implementation likely meets throughput constraints."""
        code = implementation.get('main_module', '')
        
        # Simple heuristics
        has_async = 'async' in code or 'await' in code
        has_connection_pooling = 'pool' in code.lower()
        has_load_balancing = 'balance' in code.lower()
        
        return has_async or has_connection_pooling or has_load_balancing
    
    def _check_security_constraint(self, implementation: Dict[str, Any], constraint: Dict) -> bool:
        """Check if implementation likely meets security constraints."""
        code = implementation.get('main_module', '')
        
        requirement = constraint.get('requirement', '').lower()
        
        if 'authentication' in requirement:
            return 'auth' in code.lower() or 'token' in code.lower()
        elif 'encryption' in requirement:
            return 'encrypt' in code.lower() or 'hash' in code.lower()
        elif 'input validation' in requirement:
            return 'validate' in code.lower() or 'sanitize' in code.lower()
        
        return True  # Default to pass for unknown security constraints
    
    def _check_scalability_constraint(self, implementation: Dict[str, Any], constraint: Dict) -> bool:
        """Check if implementation likely meets scalability constraints."""
        code = implementation.get('main_module', '')
        
        # Simple heuristics for scalability
        has_async = 'async' in code or 'await' in code
        has_microservice_patterns = 'fastapi' in code.lower() or 'flask' in code.lower()
        has_database_features = 'connection' in code.lower()
        
        return has_async or has_microservice_patterns or has_database_features
    
    def _check_reliability_constraint(self, implementation: Dict[str, Any], constraint: Dict) -> bool:
        """Check if implementation likely meets reliability constraints."""
        code = implementation.get('main_module', '')
        
        # Simple heuristics for reliability
        has_error_handling = 'try:' in code or 'except' in code
        has_logging = 'log' in code.lower()
        has_retry_logic = 'retry' in code.lower()
        
        return has_error_handling or has_logging or has_retry_logic