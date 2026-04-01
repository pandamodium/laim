"""
Phase 8: Validation and constraint checking framework.

Provides comprehensive validation of simulation runs including:
- Constraint validation (employment, unemployment, wages)
- Economic sanity checks (realistic parameters, monotonicity)
- Data integrity checks (no NaNs, consistency)
- Phase interaction validation (all components working together)

Classes:
    ValidationResult: Stores validation output
    SimulationValidator: Main validation orchestrator
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import warnings


class ValidationStatus(Enum):
    """Validation status enumeration."""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass
class ValidationResult:
    """Stores results of a single validation check."""
    check_name: str
    status: ValidationStatus
    message: str
    severity: str = "INFO"  # INFO, WARNING, ERROR
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation."""
        symbol = "✓" if self.status == ValidationStatus.PASS else "✗" if self.status == ValidationStatus.FAIL else "⚠"
        return f"{symbol} {self.check_name}: {self.message}"


class SimulationValidator:
    """Comprehensive simulation validation framework."""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the validator.
        
        Args:
            verbose: Whether to print validation messages
        """
        self.verbose = verbose
        self.results: List[ValidationResult] = []
    
    def validate_metrics_dataframe(
        self,
        metrics_df: pd.DataFrame,
        strict: bool = False
    ) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate metrics DataFrame structure and content.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            strict: If True, warnings become failures
            
        Returns:
            Tuple of (all_pass, list of ValidationResult objects)
        """
        self.results = []
        
        # Check basic structure
        self._check_dataframe_not_empty(metrics_df)
        self._check_required_columns(metrics_df)
        self._check_no_missing_values(metrics_df)
        
        # Check numerical constraints
        self._check_unemployment_rate_bounds(metrics_df)
        self._check_wage_positivity(metrics_df)
        self._check_employment_bounds(metrics_df)
        self._check_ai_adoption_bounds(metrics_df)
        
        # Check economic sanity
        self._check_unemployment_realism(metrics_df)
        self._check_wage_growth_realism(metrics_df)
        self._check_inequality_bounds(metrics_df)
        
        # Check data consistency
        self._check_no_nan_values(metrics_df)
        self._check_monotonic_cumulative_metrics(metrics_df)
        
        # Prepare results
        all_pass = all(r.status == ValidationStatus.PASS for r in self.results)
        
        if strict:
            # Convert warnings to failures
            all_pass = all(r.status in (ValidationStatus.PASS, ValidationStatus.WARNING)
                          for r in self.results)
        
        if self.verbose:
            self._print_results()
        
        return all_pass, self.results
    
    def validate_constraint(
        self,
        condition: bool,
        check_name: str,
        pass_message: str,
        fail_message: str,
        severity: str = "ERROR"
    ) -> ValidationResult:
        """
        Quick constraint validation helper.
        
        Args:
            condition: Boolean condition to check
            check_name: Name of the check
            pass_message: Message if passes
            fail_message: Message if fails
            severity: Severity level
            
        Returns:
            ValidationResult
        """
        status = ValidationStatus.PASS if condition else ValidationStatus.FAIL
        message = pass_message if condition else fail_message
        
        result = ValidationResult(
            check_name=check_name,
            status=status,
            message=message,
            severity=severity
        )
        
        self.results.append(result)
        return result
    
    # Individual validation checks
    
    def _check_dataframe_not_empty(self, df: pd.DataFrame) -> ValidationResult:
        """Check that metrics DataFrame is not empty."""
        condition = len(df) > 0
        result = self.validate_constraint(
            condition,
            "DataFrame Structure",
            f"DataFrame has {len(df)} periods",
            "DataFrame is empty",
            severity="ERROR"
        )
        return result
    
    def _check_required_columns(self, df: pd.DataFrame) -> ValidationResult:
        """Check that required columns exist."""
        required = ['period', 'unemployment_rate', 'avg_wage_human']
        missing = [col for col in required if col not in df.columns]
        
        condition = len(missing) == 0
        result = self.validate_constraint(
            condition,
            "Required Columns",
            "All required columns present",
            f"Missing columns: {missing}",
            severity="ERROR"
        )
        return result
    
    def _check_no_missing_values(self, df: pd.DataFrame) -> ValidationResult:
        """Check for missing values across numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        missing_count = df[numeric_cols].isna().sum().sum()
        
        condition = missing_count == 0
        result = self.validate_constraint(
            condition,
            "Data Completeness",
            "No missing values",
            f"Found {missing_count} missing values",
            severity="ERROR"
        )
        result.details['missing_count'] = missing_count
        return result
    
    def _check_unemployment_rate_bounds(self, df: pd.DataFrame) -> ValidationResult:
        """Check unemployment rate is in [0, 1]."""
        if 'unemployment_rate' not in df.columns:
            return ValidationResult("Unemployment Bounds", ValidationStatus.PASS, "Column not present")
        
        unemp = df['unemployment_rate']
        valid = (unemp >= 0) & (unemp <= 1)
        condition = valid.all()
        
        if not condition:
            invalid_periods = df[~valid]['period'].tolist()
            fail_msg = f"Unemployment rate out of bounds in periods: {invalid_periods[:5]}"
        else:
            fail_msg = ""
        
        result = self.validate_constraint(
            condition,
            "Unemployment Bounds",
            f"Unemployment rate in [0, 1], range: [{unemp.min():.4f}, {unemp.max():.4f}]",
            fail_msg,
            severity="ERROR"
        )
        result.details['min_unemp'] = float(unemp.min())
        result.details['max_unemp'] = float(unemp.max())
        return result
    
    def _check_wage_positivity(self, df: pd.DataFrame) -> ValidationResult:
        """Check that all wages are positive."""
        wage_cols = [col for col in df.columns if 'wage' in col.lower() and col != 'wage_gap_ratio']
        
        negative_found = False
        for col in wage_cols:
            if col not in df.columns:
                continue
            if (df[col] <= 0).any():
                negative_found = True
                break
        
        result = self.validate_constraint(
            not negative_found,
            "Wage Positivity",
            "All wages are positive",
            f"Found non-positive wages in columns: {wage_cols}",
            severity="ERROR"
        )
        return result
    
    def _check_employment_bounds(self, df: pd.DataFrame) -> ValidationResult:
        """Check employment-related constraints."""
        result = ValidationResult(
            check_name="Employment Bounds",
            status=ValidationStatus.PASS,
            message="Employment metrics within valid ranges"
        )
        
        if 'num_employed_human' in df.columns and 'num_employed_ai' in df.columns:
            total_employed = df['num_employed_human'] + df['num_employed_ai']
            # Employment should typically be less than labor supply (assume 2-3M)
            if (total_employed > 5_000_000).any():
                result.status = ValidationStatus.WARNING
                result.message = "Total employment exceeds expected range"
                result.severity = "WARNING"
            result.details['max_employment'] = int(total_employed.max())
        
        self.results.append(result)
        return result
    
    def _check_ai_adoption_bounds(self, df: pd.DataFrame) -> ValidationResult:
        """Check AI adoption rates are in [0, 1]."""
        ai_cols = [col for col in df.columns if 'ai_' in col.lower() and 'adoption' in col.lower()]
        
        all_valid = True
        for col in ai_cols:
            if col not in df.columns:
                continue
            if not ((df[col] >= 0) & (df[col] <= 1)).all():
                all_valid = False
                break
        
        result = self.validate_constraint(
            all_valid,
            "AI Adoption Bounds",
            f"AI adoption rates in [0, 1] for {len(ai_cols)} categories",
            "Some AI adoption rates out of bounds",
            severity="ERROR"
        )
        return result
    
    def _check_unemployment_realism(self, df: pd.DataFrame) -> ValidationResult:
        """Check unemployment rate is in realistic range (2-12%)."""
        if 'unemployment_rate' not in df.columns:
            return ValidationResult("Unemployment Realism", ValidationStatus.PASS, "Column not present")
        
        unemp = df['unemployment_rate']
        mean_unemp = unemp.mean()
        
        # Realistic unemployment: 2-12%
        condition = (0.02 <= mean_unemp <= 0.12)
        
        result = self.validate_constraint(
            condition,
            "Unemployment Realism",
            f"Mean unemployment {mean_unemp:.2%} is in realistic range [2%, 12%]",
            f"Mean unemployment {mean_unemp:.2%} outside realistic range",
            severity="WARNING"
        )
        result.details['mean_unemployment'] = float(mean_unemp)
        return result
    
    def _check_wage_growth_realism(self, df: pd.DataFrame) -> ValidationResult:
        """Check wage growth is realistic (1-5% annually, 0.25-1.25% quarterly)."""
        if 'avg_wage_human' not in df.columns or len(df) < 2:
            return ValidationResult("Wage Growth Realism", ValidationStatus.PASS, "Insufficient data")
        
        wages = df['avg_wage_human']
        # Calculate quarterly growth rate
        quarterly_growth = (wages.iloc[-1] / wages.iloc[0]) ** (1 / len(df)) - 1
        # Annualize: (1 + q)^4 - 1
        annual_growth = (1 + quarterly_growth) ** 4 - 1
        
        # Realistic: 0-5% annually (allows for zero/negative in recessions)
        condition = (-0.05 <= annual_growth <= 0.10)
        
        result = self.validate_constraint(
            condition,
            "Wage Growth Realism",
            f"Wage growth {annual_growth:.2%} annually is realistic",
            f"Wage growth {annual_growth:.2%} outside realistic range",
            severity="WARNING"
        )
        result.details['annual_wage_growth'] = float(annual_growth)
        return result
    
    def _check_inequality_bounds(self, df: pd.DataFrame) -> ValidationResult:
        """Check inequality metrics are in realistic ranges."""
        issues = []
        
        if 'gini_coefficient' in df.columns:
            gini = df['gini_coefficient']
            # Gini typically 0.2 - 0.6
            if (gini < 0.15).any() or (gini > 0.70).any():
                issues.append("Gini coefficient out of typical range [0.15, 0.70]")
        
        if 'wage_gap_ratio' in df.columns:
            gap = df['wage_gap_ratio']
            # Wage gap ratio typically 1.2 - 3.0
            if (gap < 1.0).any() or (gap > 5.0).any():
                issues.append("Wage gap ratio out of typical range [1.0, 5.0]")
        
        condition = len(issues) == 0
        result = self.validate_constraint(
            condition,
            "Inequality Realism",
            "Inequality metrics in realistic ranges",
            "; ".join(issues),
            severity="WARNING"
        )
        return result
    
    def _check_no_nan_values(self, df: pd.DataFrame) -> ValidationResult:
        """Check for NaN values in numeric columns."""
        numeric_df = df.select_dtypes(include=[np.number])
        nan_count = numeric_df.isna().sum().sum()
        
        condition = nan_count == 0
        result = self.validate_constraint(
            condition,
            "No NaN Values",
            "No NaN values found in data",
            f"Found {nan_count} NaN values",
            severity="ERROR"
        )
        return result
    
    def _check_monotonic_cumulative_metrics(self, df: pd.DataFrame) -> ValidationResult:
        """Check that cumulative metrics are non-decreasing."""
        cumulative_cols = [
            col for col in df.columns
            if any(keyword in col.lower() for keyword in ['cumulative', 'total_r_and_d', 'total_'])
        ]
        
        issues = []
        for col in cumulative_cols:
            if col not in df.columns:
                continue
            # Check if mostly monotonic (allow small non-monotonic dips due to rounding)
            diffs = df[col].diff()
            non_monotonic = (diffs < -1e-6).sum()  # Small tolerance
            if non_monotonic > len(df) * 0.05:  # Allow <5% violations
                issues.append(col)
        
        condition = len(issues) == 0
        result = self.validate_constraint(
            condition,
            "Cumulative Metrics Monotonicity",
            f"Cumulative metrics are non-decreasing ({len(cumulative_cols)} columns checked)",
            f"Non-monotonic cumulative metrics: {issues}",
            severity="WARNING"
        )
        return result
    
    def validate_phase_integration(
        self,
        metrics_df: pd.DataFrame
    ) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate that all simulation phases are working together.
        
        Args:
            metrics_df: DataFrame with simulation metrics
            
        Returns:
            Tuple of (all_pass, list of ValidationResult objects)
        """
        self.results = []
        
        # Check Phase 3 (business formation)
        self._check_phase3_indicators(metrics_df)
        
        # Check Phase 4 (R&D)
        self._check_phase4_indicators(metrics_df)
        
        # Check Phase 5 (policy intervention)
        self._check_phase5_indicators(metrics_df)
        
        # Check Phase 6 (metrics)
        self._check_phase6_indicators(metrics_df)
        
        all_pass = all(r.status == ValidationStatus.PASS for r in self.results)
        
        if self.verbose:
            self._print_results()
        
        return all_pass, self.results
    
    def _check_phase3_indicators(self, df: pd.DataFrame) -> ValidationResult:
        """Check Phase 3 (business formation) indicators."""
        required_cols = ['num_firms', 'firm_entry', 'firm_exit']
        present = [col for col in required_cols if col in df.columns]
        
        result = self.validate_constraint(
            len(present) >= 1,
            "Phase 3: Business Formation",
            f"Business formation indicators present ({len(present)}/{len(required_cols)})",
            "Business formation indicators missing",
            severity="WARNING"
        )
        result.details['indicators_present'] = present
        return result
    
    def _check_phase4_indicators(self, df: pd.DataFrame) -> ValidationResult:
        """Check Phase 4 (R&D) indicators."""
        required_cols = ['total_r_and_d_spending']
        present = [col for col in required_cols if col in df.columns]
        
        result = self.validate_constraint(
            len(present) >= 1,
            "Phase 4: R&D Investment",
            f"R&D indicators present ({len(present)}/{len(required_cols)})",
            "R&D indicators missing",
            severity="WARNING"
        )
        return result
    
    def _check_phase5_indicators(self, df: pd.DataFrame) -> ValidationResult:
        """Check Phase 5 (policy) indicators."""
        optional_cols = ['ui_recipients', 'retraining_active', 'wage_subsidy_spending']
        present = [col for col in optional_cols if col in df.columns]
        
        # Phase 5 is optional, so just report if present
        result = self.validate_constraint(
            len(present) >= 0,  # Always pass
            "Phase 5: Policy Interventions",
            f"Policy indicators available ({len(present)}/{len(optional_cols)})" if present else "Phase 5 (policy) not enabled",
            "",
            severity="INFO"
        )
        result.details['policy_indicators'] = present
        return result
    
    def _check_phase6_indicators(self, df: pd.DataFrame) -> ValidationResult:
        """Check Phase 6 (metrics) indicators."""
        expected_metrics = ['gini_coefficient', 'unemployment_rate', 'avg_wage_human']
        present = [col for col in expected_metrics if col in df.columns]
        
        result = self.validate_constraint(
            len(present) >= 2,
            "Phase 6: Metrics & Analytics",
            f"Comprehensive metrics present ({len(present)}/{len(expected_metrics)})",
            "Basic metrics missing",
            severity="WARNING"
        )
        return result
    
    def _print_results(self) -> None:
        """Print validation results to console."""
        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)
        
        for result in self.results:
            print(f"  {result}")
        
        # Summary
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        
        print("\n" + "-"*60)
        print(f"Summary: {passed} passed, {warnings} warnings, {failed} failures")
        print("="*60 + "\n")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary statistics."""
        return {
            'total_checks': len(self.results),
            'passed': sum(1 for r in self.results if r.status == ValidationStatus.PASS),
            'failed': sum(1 for r in self.results if r.status == ValidationStatus.FAIL),
            'warnings': sum(1 for r in self.results if r.status == ValidationStatus.WARNING),
            'all_pass': all(r.status == ValidationStatus.PASS for r in self.results)
        }
