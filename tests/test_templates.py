# DayZ Server Monitor
# File: tests/test_templates.py
# Purpose: Unit test for template loader system

import os
from templates import TemplateLoader

def test_load_valid_template():
    loader = TemplateLoader("en_GB")
    template = loader.load_template("mod_new.txt")
    assert "added" in template

def test_format_template():
    loader = TemplateLoader("en_GB")
    result = loader.format_template("mod_new.txt", title="Example Mod")
    assert "Example Mod" in result
