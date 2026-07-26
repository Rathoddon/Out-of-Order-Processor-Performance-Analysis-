"""
Custom gem5 SE-mode config script.
Exposes --rob-size and --issue-width as command-line flags for X86O3CPU,
since the default se.py script does not expose these parameters directly.

Usage example:
    ./build/X86/gem5.opt --outdir=results/matmul_rob64_iw2 \
        configs/../rob_iw_config.py \
        --cmd=matmul.bin --rob-size=64 --issue-width=2
"""

import argparse
import m5
from m5.objects import *

# ---- Argument parsing ----
parser = argparse.ArgumentParser()
parser.add_argument("--cmd", required=True, help="Path to the workload binary")
parser.add_argument("--rob-size", type=int, default=192, help="Reorder buffer entries")
parser.add_argument("--issue-width", type=int, default=4, help="Issue width")
parser.add_argument("--l1i_size", type=str, default="32kB")
parser.add_argument("--l1d_size", type=str, default="64kB")
parser.add_argument("--l2_size", type=str, default="256kB")
args = parser.parse_args()

# ---- System setup ----
system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MB")]

# ---- CPU setup (Out-of-Order) ----
system.cpu = X86O3CPU()

# The parameters we actually care about for the sweep:
system.cpu.numROBEntries = args.rob_size
system.cpu.issueWidth = args.issue_width
system.cpu.fetchWidth = args.issue_width
system.cpu.decodeWidth = args.issue_width
system.cpu.renameWidth = args.issue_width
system.cpu.dispatchWidth = args.issue_width
system.cpu.commitWidth = args.issue_width

# ---- Memory bus ----
system.membus = SystemXBar()
system.system_port = system.membus.cpu_side_ports

# ---- L1 caches ----
system.cpu.icache = Cache(
    size=args.l1i_size, assoc=2, tag_latency=2, data_latency=2,
    response_latency=2, mshrs=4, tgts_per_mshr=20
)
system.cpu.dcache = Cache(
    size=args.l1d_size, assoc=2, tag_latency=2, data_latency=2,
    response_latency=2, mshrs=4, tgts_per_mshr=20
)
system.cpu.icache_port = system.cpu.icache.cpu_side
system.cpu.dcache_port = system.cpu.dcache.cpu_side

# ---- L2 bus + cache ----
system.l2bus = L2XBar()
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

system.l2cache = Cache(
    size=args.l2_size, assoc=8, tag_latency=20, data_latency=20,
    response_latency=20, mshrs=20, tgts_per_mshr=12
)
system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

# ---- Interrupts (x86 needs this) ----
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# ---- Memory controller ----
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# ---- Workload ----
process = Process()
process.cmd = [args.cmd]
system.cpu.workload = process
system.cpu.createThreads()

system.workload = SEWorkload.init_compatible(args.cmd)

root = Root(full_system=False, system=system)
m5.instantiate()

print(f"Running with ROB={args.rob_size}, issue_width={args.issue_width}")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
