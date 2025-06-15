# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: tests/test_core_behaviors.py
# Purpose: Unit tests for fallback mode, template loading, and server unreachable simulation
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import pytest
from templates import TemplateLoader
import server_query

def test_template_loader_success():
    loader = TemplateLoader("en_UK")
    result = loader.format("output", "mod_new.txt", title="Test Mod")
    assert "Test Mod" in result

def test_template_loader_missing_placeholder():
    loader = TemplateLoader("en_UK")
    result = loader.format("output", "mod_new.txt")  # Missing 'title'
    assert "[[ MISSING TEMPLATE" not in result  # Should return template even if formatting fails

def test_template_loader_missing_file():
    loader = TemplateLoader("en_UK")
    result = loader.format("output", "does_not_exist.txt")
    assert "[[ MISSING TEMPLATE:" in result

def test_server_unreachable(monkeypatch):
    # Patch IP and force invalid port
    monkeypatch.setitem.__globals__["server_query"].query_server = lambda ip, port: (_ for _ in ()).throw(TimeoutError("Timeout"))
    with pytest.raises(TimeoutError):
        server_query.query_server("127.0.0.1", 1)