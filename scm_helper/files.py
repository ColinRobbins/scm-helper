"""Read and process CSV Files."""


class Files:
    """General file handling."""

    def __init__(self):
        """Initiase."""
        self._filename = None
        self._scm = []
        self._error = {}

    def file_error(self, name, error):
        """Log an error in the file."""
        if error in self._error:
            self._error[error].append(name)
        else:
            self._error[error] = []
            self._error[error].append(name)

    def print_errors(self):
        """Print errors."""
        output = ""
        output += f"\nErrors in {self._filename}"
        for error in self._error:
            output += f"{error}:"
            for name in sorted(self._error[error]):
                output += f"   {name}"

        return output
