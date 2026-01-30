class TodoFormatter:
    def parse(self, raw_text):
        """
        Parses markdown-like text into structured todo items.
        Supports:
        - # Headers
        - - [ ] Tasks
        - **Bold lines**
        """
        items = []
        for line in raw_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("#"):
                items.append({"type": "header", "text": line.lstrip("#").strip()})
            elif line.startswith("- [ ]") or line.startswith("* [ ]"):
                items.append({"type": "task", "text": line[5:].strip()})
            elif line.startswith("- [x]") or line.startswith("* [x]"):
                # Support checked tasks even if we print them empty
                items.append({"type": "task", "text": line[5:].strip()})
            elif line.startswith("**") and line.endswith("**"):
                items.append({"type": "bold", "text": line[2:-2].strip()})
            elif line.startswith("__") and line.endswith("__"):
                items.append({"type": "bold", "text": line[2:-2].strip()})
            elif line.startswith("-") or line.startswith("*"):
                # Treat single dashes/stars as tasks
                items.append({"type": "task", "text": line[1:].strip()})
            else:
                items.append({"type": "plain", "text": line})

        return items
