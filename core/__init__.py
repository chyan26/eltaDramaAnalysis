"""
Core analysis engine module for Elta Drama Analysis System
统一的核心分析引擎模組
"""

from .age_analysis_engine import AgeAnalysisEngine, AgeAnalysisConfig
from .visualization_engine import VisualizationEngine

__all__ = ['AgeAnalysisEngine', 'AgeAnalysisConfig', 'VisualizationEngine']
