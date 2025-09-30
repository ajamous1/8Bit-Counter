/*
 * Copyright (c) 2025 Ahmad Jamous
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

//separate file for counter and use  an instance of it 

// Top must match info.yaml: top_module: tt_um_8bCounter_ajamous1
module tt_um_8bCounter_ajamous1 (
    // User pins
    input  wire [7:0] ui_in,    // [0]=load, [1]=oe, [7:2]=unused
    output wire [7:0] uo_out,   // Dedicated outputs (unused)
    input  wire [7:0] uio_in,   // IOs: Input path (used during load)
    output wire [7:0] uio_out,  // IOs: Output path (drives count when oe=1)
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input/Hi-Z, 1=output)

    // Harness pins (not listed in info.yaml)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // ---------------------------
  // Control decode (from ui_in)
  // ---------------------------
  wire load = ui_in[0];  // sync load strobe (captures UIO bus on rising clk)
  wire oe   = ui_in[1];  // 1 = drive count on UIO, 0 = release (Hi-Z)

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, ui_in[7:2], 1'b0};

  // ---------------------------
  // State
  // ---------------------------
  reg [7:0] count;

  // -----------------------------------------
  // Synchronous behavior: reset -> load -> inc
  // -----------------------------------------
  // At the rising edge of the clock, or falling edge of the reset
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 8'h00;               
    end else if (load && !oe) begin
      //take the input of the user if no output enable and load 
      count <= uio_in;              // capture external byte on UIO
    end else begin
      //otherwise, increment up by 1 each time
      count <= count + 8'd1;        
    end
  end

  // --------------------------------------------
  // All output pins must be assigned. If not used, assign to 0.
  // --------------------------------------------
  // Tri-state UIO bus: drive count when oe=1; otherwise Hi-Z so external can drive
  assign uio_out = count;            // value we would drive
  assign uio_oe  = {8{oe}};          // drive all 8 bits when oe=1, else Hi-Z

  // Dedicated outputs (never tri-stated) unused here
  assign uo_out  = 8'h00;

endmodule
