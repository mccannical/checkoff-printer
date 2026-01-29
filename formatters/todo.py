class TodoFormatter:
    def parse(self, raw_text):
        """
        Splits text by newlines to create list items.
        Removes empty lines.
        """
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        return lines
