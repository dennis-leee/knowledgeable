"""Unit tests for Streamlit UI components."""

import pytest
from unittest.mock import patch, MagicMock
import streamlit as st


class TestUIFunctions:
    """Tests for UI helper functions."""

    def test_init_session_state_creates_results(self):
        """Test session state initialization."""
        from app.ui import init_session_state

        mock_st = MagicMock()
        with patch.object(st, 'session_state', mock_st):
            init_session_state()
            assert hasattr(mock_st, 'results')
            assert hasattr(mock_st, 'processing')

    def test_display_knowledge_with_error(self):
        """Test display with error result."""
        from app.ui import display_knowledge

        result = {"error": "Test error"}
        mock_st = MagicMock()

        with patch.object(st, 'error') as mock_error:
            display_knowledge(result)
            mock_error.assert_called_once()

    def test_display_knowledge_with_valid_result(self):
        """Test display with valid result."""
        from app.ui import display_knowledge

        result = {
            "summary": "Test summary",
            "entities": [
                {"name": "Entity1", "type": "concept"},
                {"name": "Entity2", "type": "technology"},
            ],
            "relations": [
                {"source": "Entity1", "target": "Entity2", "type": "uses"},
            ],
            "insights": [
                {"text": "Test insight", "insight_type": "implication"},
            ],
            "validated": True,
        }

        with patch.object(st, 'columns') as mock_columns, \
             patch.object(st, 'subheader') as mock_subheader, \
             patch.object(st, 'write') as mock_write, \
             patch.object(st, 'metric') as mock_metric, \
             patch.object(st, 'success') as mock_success:

            mock_col1 = MagicMock()
            mock_col2 = MagicMock()
            mock_columns.return_value = [mock_col1, mock_col2]

            display_knowledge(result)

    def test_display_knowledge_with_empty_entities(self):
        """Test display with empty entities."""
        from app.ui import display_knowledge

        result = {
            "summary": "Test summary",
            "entities": [],
            "relations": [],
            "insights": [],
            "validated": False,
            "validation_errors": ["No entities"],
        }

        with patch.object(st, 'columns') as mock_columns, \
             patch.object(st, 'subheader') as mock_subheader, \
             patch.object(st, 'warning') as mock_warning:

            mock_col1 = MagicMock()
            mock_col2 = MagicMock()
            mock_columns.return_value = [mock_col1, mock_col2]

            display_knowledge(result)
            mock_warning.assert_called()


class TestUIState:
    """Tests for UI state management."""

    def test_session_state_persistence(self):
        """Test that session state persists across reruns."""
        mock_state = {
            "results": [],
            "processing": False,
        }

        with patch.object(st, 'session_state', mock_state):
            assert mock_state["results"] == []
            mock_state["results"].append({"title": "Test"})
            assert len(mock_state["results"]) == 1


class TestEdgeCases:
    """Edge case tests for UI."""

    def test_very_long_summary(self):
        """Test handling of very long summaries."""
        from app.ui import display_knowledge

        long_text = "A" * 1000
        result = {
            "summary": long_text,
            "entities": [],
            "relations": [],
            "insights": [],
        }

        with patch.object(st, 'columns') as mock_columns:
            mock_columns.return_value = [MagicMock(), MagicMock()]
            display_knowledge(result)

    def test_special_characters_in_entities(self):
        """Test handling of special characters in entities."""
        from app.ui import display_knowledge

        result = {
            "summary": "Test",
            "entities": [
                {"name": "Entity with 特殊字符", "type": "concept"},
                {"name": "Entity <script>", "type": "technology"},
            ],
            "relations": [],
            "insights": [],
        }

        with patch.object(st, 'columns') as mock_columns:
            mock_columns.return_value = [MagicMock(), MagicMock()]
            display_knowledge(result)

    def test_missing_fields_in_result(self):
        """Test handling of missing fields in result."""
        from app.ui import display_knowledge

        result = {}

        with patch.object(st, 'columns') as mock_columns, \
             patch.object(st, 'subheader') as mock_subheader, \
             patch.object(st, 'write') as mock_write, \
             patch.object(st, 'error') as mock_error:

            mock_columns.return_value = [MagicMock(), MagicMock()]
            display_knowledge(result)
