import re


class TodoFormatter:
    def parse(self, raw_text):
        """
        Parses markdown-like text into structured todo items.
        Supports:
        - # Big Header  ## Medium Header  ### Small Header
        - - [ ] / * [ ] checkbox tasks
        - 1. numbered list items
        - - / * bullet list items
        - **Bold lines** and inline **bold** markers
        """
        items = []
        for line in raw_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("###"):
                items.append({"type": "header3", "text": line.lstrip("#").strip()})
            elif line.startswith("##"):
                items.append({"type": "header2", "text": line.lstrip("#").strip()})
            elif line.startswith("#"):
                items.append({"type": "header", "text": line.lstrip("#").strip()})
            elif line.startswith("- [ ]") or line.startswith("* [ ]"):
                items.append({"type": "task", "text": self._strip_bold(line[5:].strip())})
            elif line.startswith("- [x]") or line.startswith("* [x]"):
                items.append({"type": "task", "text": self._strip_bold(line[5:].strip())})
            elif re.match(r"^\d+\.\s", line):
                text = re.sub(r"^\d+\.\s*", "", line)
                items.append({"type": "task", "text": self._strip_bold(text)})
            elif self._is_full_bold(line):
                text = line.strip("*").strip("_").strip()
                items.append({"type": "bold", "text": text})
            elif line.startswith("-") or line.startswith("*"):
                items.append({"type": "task", "text": self._strip_bold(line[1:].strip())})
            else:
                items.append({"type": "plain", "text": self._strip_bold(line)})

        return items

    def _is_full_bold(self, line):
        return (line.startswith("**") and line.endswith("**")) or \
               (line.startswith("__") and line.endswith("__"))

    def _strip_bold(self, text):
        return re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), text)
