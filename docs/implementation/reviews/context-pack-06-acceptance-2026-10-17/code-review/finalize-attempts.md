The first metadata/cleanup finalizer invocation stopped before deletion because
`Path.stat()` encountered the long test-copy paths. The same Windows extended
path spelling already used by the relocation tests was applied to temporary
inventory/stat traversal. No candidate implementation changed and no test was
rerun for this packaging retry. Previously copied owned examples are reused.
