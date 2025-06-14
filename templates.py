# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import os
import logging

class TemplateLoader:
    def __init__(self, locale):
        self.locale = locale
        self.locale_path = os.path.join("locales", locale)

    def load_template(self, template_file):
        template_path = os.path.join(self.locale_path, template_file)
        if not os.path.exists(template_path):
            logging.warning(f"Missing template file: {template_path}")
            return f"[[ MISSING TEMPLATE: {template_file} ]]"
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def format_template(self, template_file, **kwargs):
        template = self.load_template(template_file)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logging.error(f"Missing placeholder {e} in template {template_file}")
            return template  # return unformatted template if problem