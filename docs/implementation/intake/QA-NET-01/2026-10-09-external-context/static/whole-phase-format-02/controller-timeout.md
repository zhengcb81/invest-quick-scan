# Original format-02 controller outcome

The original exec session 97353 terminated with exit 1. isort returned 0 in
0.706 seconds. The controller raised subprocess.TimeoutExpired for the Black
child at its configured 180-second deadline. Before that deadline, a read-only
CIM check confirmed parent PID 14864 and child PID 42852 were still live; no
duplicate execution was started. The failed controller did not persist Black's
partial captured output, an after-source snapshot, or a process.json. Their
absence is an evidence limitation, not a passing result. This note is the
controller's retrospective record, not original subprocess stderr.

The sandbox denied the first CIM check. The runtime will be retried outside
the sandbox with the SAME stripped environment and Python audit guard, using a
new label. The guard, product scope and owner files are not relaxed. A controller
repair will preserve timeout output, execution code and terminal metadata for
future batches; the original before-source/isort artifacts remain unchanged.
