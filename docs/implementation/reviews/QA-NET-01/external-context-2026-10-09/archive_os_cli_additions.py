"""Append only new OS test trace batches; leave the first archive untouched."""
import archive_os_cli as archive

archive.LABELS = (
    "os-public-complete-seal-first-01", "os-public-complete-seal-green-01",
    "os-public-complete-seal-green-02", "os-public-automatic-recovery-red-01",
    "os-public-automatic-recovery-affected-green-01",
)
archive.NAMES.update({"seal-stdout.log", "seal-stderr.log"})

if __name__ == "__main__":
    archive.main()
