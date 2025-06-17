# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: templates.py
# Purpose: Load and format localized message templates from categorized folders
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

from pathlib import Path
import logging

class TemplateLoader:
    def __init__(self, locale, base_path="locales"):
        self.locale = locale
        self.base_path = Path(base_path)
        self.template_cache = {}

    def load_template(self, category, template_file):
        key = f"{category}/{template_file}"
        if key in self.template_cache:
            return self.template_cache[key]

        template_path = self.base_path / self.locale / category / template_file
        if not template_path.exists():
            logging.warning(f"[TemplateLoader] Missing template file: {template_path}")
            return f"[[ MISSING TEMPLATE: {category}/{template_file} ]]"

        try:
            with template_path.open("r", encoding="utf-8") as f:
                content = f.read().strip()
                self.template_cache[key] = content
                return content
        except Exception as e:
            logging.error(f"[TemplateLoader] Failed to read template {template_path}: {e}")
            return f"[[ ERROR LOADING TEMPLATE: {category}/{template_file} ]]"

    def format(self, category, template_file, **kwargs):
        template = self.load_template(category, template_file)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logging.error(f"[TemplateLoader] Missing placeholder {e} in {category}/{template_file}")
            return template
