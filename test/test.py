# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # 100 kHz clock (10 us period)
    clk = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clk.start())

    # ---------------------------
    # Reset and init
    # ---------------------------
    dut.ena.value = 1
    dut.ui_in.value = 0          # [1]=oe=0, [0]=load=0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    await Timer(1, units="ns")   # let non-blocking updates settle

    # ---------------------------
    # 1) Show plain up-counter (oe=1)
    # ---------------------------
    dut.ui_in.value = 0b00000010   # oe=1, load=0
    await ClockCycles(dut.clk, 1); await Timer(1, units="ns")

    a = int(dut.uio_out.value)
    await ClockCycles(dut.clk, 1); await Timer(1, units="ns")
    b = int(dut.uio_out.value)
    dut._log.info(f"Counter step while oe=1: {a:02X} -> {b:02X}")
    assert b == ((a + 1) & 0xFF), "Counter did not increment by 1 when oe=1"

    # ---------------------------
    # 2) Synchronous load while tri-stated (oe=0)
    # ---------------------------
    dut.ui_in.value = 0b00000000   # oe=0, load=0 (release bus)
    await ClockCycles(dut.clk, 1); await Timer(1, units="ns")

    load_val = 0xA5
    dut.uio_in.value = load_val    # external drives the bus

    # Pulse load for exactly one rising edge (with oe=0)
    dut.ui_in.value = 0b00000001   # load=1, oe=0
    await RisingEdge(dut.clk); await Timer(1, units="ns")   # capture happens here
    dut.ui_in.value = 0b00000000   # deassert load

    # Immediately re-enable outputs and observe BEFORE next clock
    dut.ui_in.value = 0b00000010   # oe=1, load=0
    await Timer(1, units="ns")
    seen = int(dut.uio_out.value)
    dut._log.info(f"Loaded value observed: {seen:02X}")
    assert seen == load_val, "Loaded value did not appear on UIO after enabling outputs"

    # Next clock should increment
    await ClockCycles(dut.clk, 1); await Timer(1, units="ns")
    inc = int(dut.uio_out.value)
    dut._log.info(f"After one tick: {inc:02X}")
    assert inc == ((load_val + 1) & 0xFF), "Counter did not increment after load"

    # ---------------------------
    # 3) Tri-state check (oe=0)
    # ---------------------------
    dut.ui_in.value = 0b00000000   # oe=0 again
    await ClockCycles(dut.clk, 1); await Timer(1, units="ns")
    assert int(dut.uio_oe.value) == 0, "uio_oe should be 0 when oe=0 (Hi-Z)"

    # Demonstrate bus is released
    dut.uio_in.value = 0x3C
    await ClockCycles(dut.clk, 1); await Timer(1, units="ns")

    dut._log.info("Test completed")
    await ClockCycles(dut.clk, 5)