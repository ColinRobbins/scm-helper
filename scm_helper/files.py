"""Read and process CSV Files."""
import ntpath


class Files:
    """General file handling."""

    def __init__(self):
        """Initiase."""
        self._filename = None
        self._scm = []
        self._error = {}

    def file_error(self, name, error, extra=None):
        """Log an error in the file."""
        if error in self._error:
            self._error[error].append([name, extra])
        else:
            self._error[error] = []
            self._error[error].append([name, extra])

    def print_errors(self):
        """Print errors."""
        fname = ntpath.basename(self._filename)
        output = ""

        for error in self._error:
            output += f"{error}:\n"
            for name, extra in sorted(self._error[error]):
                output += f"   {name}"
                if extra:
                    output += f" {extra}"
                output += "\n"

        if output == "":
            output = f"\nNo issues in {fname}\n"
        else:
            output = f"\nIssues in {fname}\n" + output

        return output
