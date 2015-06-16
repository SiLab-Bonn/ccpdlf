/**
 * ------------------------------------------------------------
 * Copyright (c) All rights reserved 
 * SiLab , Physics Institute of Bonn University , All Right 
 * ------------------------------------------------------------
 *
 * SVN revision information:
 *  $Rev::                       $:
 *  $Author::                    $:
 *  $Date::                      $:
 */
 
`timescale 1ps / 1ps
`default_nettype none

module ccpdlf (
    
    input wire FCLK_IN, // 48MHz
    
    //full speed 
    inout wire [7:0] BUS_DATA,
    input wire [15:0] ADD,
    input wire RD_B,
    input wire WR_B,
    
    //high speed
    inout wire [7:0] FDATA,
    input wire FREAD,
    input wire FSTROBE,
    input wire FMODE,

    //debug ports
    //output wire [15:0] DEBUG_D,
    //output wire [10:0] MULTI_IO, // Pin 1-11, 12: not connected, 13, 15: DGND, 14, 16: VCC_3.3V
  
    //LED
    output wire [4:0] LED,
    
    //SRAM
    output wire [19:0] SRAM_A,
    inout wire [15:0] SRAM_IO,
    output wire SRAM_BHE_B,
    output wire SRAM_BLE_B,
    output wire SRAM_CE1_B,
    output wire SRAM_OE_B,
    output wire SRAM_WE_B,
    
    input wire [2:0] LEMO_RX,
    output wire [2:0] LEMO_TX, // TX[0] == RJ45 trigger clock output, TX[1] == RJ45 busy output
    input wire RJ45_RESET,
    input wire RJ45_TRIGGER,

    // CCPD
	 input wire CCPD_SOUT,       //DIN0
    output wire CCPD_SIN,       //DOUT1
    output wire CCPD_LDPIX,     //DOUT0
    output wire CCPD_CKCONF,    //DOUT2
    output wire CCPD_LDDAC,     //DOUT3
	 output wire CCPD_SR_EN,     //DOUT4
    output wire CCPD__RESET,    //DOUT5
	 output wire CCPD_THON,      //DOUT6
    input wire CCPD_TDC,        //DIN1
	 output wire CCPD_INJECTION, //INJ
    output wire CCPD_DEBUG,     //DEBUG DOUT9
    // I2C
    inout SDA,
    inout SCL
);


// assignments for SCC_HVCMOS2FE-I4B_V1.0 and SCC_HVCMOS2FE-I4B_V1.1
// CCPD

// Assignments
wire BUS_RST;
(* KEEP = "{TRUE}" *)
wire BUS_CLK;
(* KEEP = "{TRUE}" *)
wire SPI_CLK;
wire CLK_40;
wire RX_CLK;
wire RX_CLK2X;
wire CLK_LOCKED;

wire TDC_OUT, TDC_TRIG_OUT;

// TLU
wire TLU_BUSY; // busy signal to TLU to de-assert trigger
wire TLU_CLOCK;

// CMD
wire CMD_EXT_START_FLAG; // to CMD FSM
wire TRIGGER_ACCEPTED_FLAG; // from TLU FSM
wire INJ_CMD_EXT_START_FLAG;
assign CMD_EXT_START_FLAG = TRIGGER_ACCEPTED_FLAG | INJ_CMD_EXT_START_FLAG;
wire TRIGGER_ENABLE; // from CMD FSM
wire CMD_READY; // from CMD FSM
wire TRIGGER_ACKNOWLEDGE_FLAG; // to TLU FSM
reg CMD_READY_FF;
always @ (posedge CLK_40)
begin
    CMD_READY_FF <= CMD_READY;
end
assign TRIGGER_ACKNOWLEDGE_FLAG = CMD_READY & ~CMD_READY_FF;
wire CMD_START_FLAG; // sending FE command triggered by external devices

// LEMO Tx
assign LEMO_TX[0] = ~CMD_READY;
assign LEMO_TX[1] = TLU_BUSY;
assign LEMO_TX[2] = RJ45_TRIGGER;

// ------- RESRT/CLOCK  ------- //
reset_gen ireset_gen(.CLK(BUS_CLK), .RST(BUS_RST));

clk_gen iclkgen(
    .U1_CLKIN_IN(FCLK_IN),
    .U1_RST_IN(1'b0),
    .U1_CLKIN_IBUFG_OUT(),
    .U1_CLK0_OUT(BUS_CLK), // DCM1: 48MHz USB/SRAM clock
    .U1_STATUS_OUT(),
    .U2_CLKFX_OUT(CLK_40), // DCM2: 40MHz command clock
    .U2_CLKDV_OUT(), // DCM2: 16MHz SERDES clock
    .U2_CLK0_OUT(RX_CLK), // DCM2: 160MHz data clock
    .U2_CLK90_OUT(),
    .U2_CLK2X_OUT(RX_CLK2X), // DCM2: 320MHz data recovery clock
    .U2_LOCKED_OUT(CLK_LOCKED),
    .U2_STATUS_OUT()
);

// 1Hz CLK
wire CE_1HZ; // use for sequential logic
wire CLK_1HZ; // don't connect to clock input, only combinatorial logic
clock_divider #(
    .DIVISOR(40000000)
) i_clock_divisor_40MHz_to_1Hz (
    .CLK(CLK_40),
    .RESET(1'b0),
    .CE(CE_1HZ),
    .CLOCK(CLK_1HZ)
);

wire CLK_2HZ;
clock_divider #(
    .DIVISOR(13000000)
) i_clock_divisor_40MHz_to_2Hz (
    .CLK(CLK_40),
    .RESET(1'b0),
    .CE(),
    .CLOCK(CLK_2HZ)
);

// -------  MODULE ADREESSES  ------- //
localparam FIFO_BASEADDR = 16'h8100;
localparam FIFO_HIGHADDR = 16'h8200-1;

localparam TLU_BASEADDR = 16'h8200;
localparam TLU_HIGHADDR = 16'h8300-1;

localparam GPIO_RX_BASEADDR = 16'h8800;
localparam GPIO_RX_HIGHADDR = 16'h8900-1;

// CCPD
localparam CCPD_SPI_BASEADDR = 16'h8900;
localparam CCPD_SPI_HIGHADDR = 16'h8Aff;

localparam CCPD_SPI_RX_BASEADDR = 16'h8B00;
localparam CCPD_SPI_RX_HIGHADDR = 16'h8Bff;

localparam CCPD_GPIO_SW_BASEADDR = 16'h8c00;
localparam CCPD_GPIO_SW_HIGHADDR = 16'h8c1f;

localparam CCPD_TDC_BASEADDR = 16'h8c20;
localparam CCPD_TDC_HIGHADDR = 16'h8c3f;

localparam CCPD_PULSE_GATE_BASEADDR= 16'h8c40;
localparam CCPD_PULSE_GATE_HIGHADDR= 16'h8c4f;

localparam CCPD_PULSE_INJ_BASEADDR= 16'h8c50;
localparam CCPD_PULSE_INJ_HIGHADDR= 16'h8c5f;

localparam CCPD_PULSE_THON_BASEADDR= 16'h8c60;
localparam CCPD_PULSE_THON_HIGHADDR= 16'h8c6f;

// -------  BUS SYGNALING  ------- //
wire [15:0] BUS_ADD;
assign BUS_ADD = ADD - 16'h4000;
wire BUS_RD, BUS_WR;
assign BUS_RD = ~RD_B;
assign BUS_WR = ~WR_B;


// -------  USER MODULES  ------- //

wire FIFO_NOT_EMPTY; // raised, when SRAM FIFO is not empty
wire FIFO_FULL, FIFO_NEAR_FULL; // raised, when SRAM FIFO is full / near full
wire FIFO_READ_ERROR; // raised, when attempting to read from SRAM FIFO when it is empty


wire [4:0] NOT_CONNECTED_RX;
wire TLU_SEL, CCPD_TDC_SEL,CCPD_RX_SEL;
gpio 
#( 
    .BASEADDR(GPIO_RX_BASEADDR),
    .HIGHADDR(GPIO_RX_HIGHADDR),
    .IO_WIDTH(8),
    .IO_DIRECTION(8'hff)
) i_gpio_rx (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),
    .IO({NOT_CONNECTED_RX,CCPD_TDC_SEL,CCPD_RX_SEL,TLU_SEL})
);

wire TLU_FIFO_READ;
wire TLU_FIFO_EMPTY;
wire [31:0] TLU_FIFO_DATA;
wire TLU_FIFO_PEEMPT_REQ;
wire [31:0] TIMESTAMP;

tlu_controller #(
    .BASEADDR(TLU_BASEADDR),
    .HIGHADDR(TLU_HIGHADDR),
    .DIVISOR(8)
) i_tlu_controller (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),
    
    .TRIGGER_CLK(CLK_40),
    
    .FIFO_READ(TLU_FIFO_READ),
    .FIFO_EMPTY(TLU_FIFO_EMPTY),
    .FIFO_DATA(TLU_FIFO_DATA),
    
    .FIFO_PREEMPT_REQ(TLU_FIFO_PEEMPT_REQ),
    
    .TRIGGER({7'b0,TDC_TRIG_OUT}),
    .TRIGGER_VETO({7'b0,FIFO_FULL}),
	 
    .TRIGGER_ENABLE(TRIGGER_ENABLE),
    .TRIGGER_ACKNOWLEDGE(TRIGGER_ACKNOWLEDGE_FLAG),
    .TRIGGER_ACCEPTED_FLAG(TRIGGER_ACCEPTED_FLAG),
	 
    .TLU_TRIGGER(RJ45_TRIGGER),
    .TLU_RESET(RJ45_RESET),
    .TLU_BUSY(TLU_BUSY),
    .TLU_CLOCK(TLU_CLOCK),
    
    .TIMESTAMP(TIMESTAMP)
);

// CCPD
wire SPI_CLK_CE;
wire CCPD_GATE;
// fifo
wire CCPD_TDC_FIFO_READ,CCPD_TDC_FIFO_EMPTY;
wire [31:0] CCPD_TDC_FIFO_DATA;
wire CCPD_SPI_RX_FIFO_READ,CCPD_SPI_RX_FIFO_EMPTY;
wire [31:0] CCPD_SPI_RX_FIFO_DATA;

wire NOT_USED=1'b0;
//GPIO_SW
wire CCPD_SW_GATE_NEG,CCPD_SW_TEST_HIT,CCPD_SW_HIT, CCPD_SW_LDDAC, CCPD_SW_LDPIX;
wire CCPD_SW_THON_NEG;
wire [1:0] NC_CCPD_GPIO;

wire CCPD_SLD,CCPD_SCLK,CCPD_SEN;
wire CCPD_PULSE_THON,CCPD_PULSE_GATE,CCPD_GATE_EXT_START;

assign CCPD__RESET= 1;
assign CCPD_SR_EN = CCPD_SEN | ~((CCPD_GATE & CCPD_SW_HIT)| CCPD_SW_TEST_HIT); // TODO need to add a gate for external trigger.
assign CCPD_LDPIX = CCPD_SLD & CCPD_SW_LDPIX;
assign CCPD_LDDAC = CCPD_SLD & CCPD_SW_LDDAC;
assign CCPD_GATE_EXT_START = CCPD_SW_GATE_NEG ? ~TDC_TRIG_OUT : CCPD_SLD;
assign CCPD_CKCONF = CCPD_SCLK;

assign CCPD_DEBUG = CCPD_GATE;

assign CCPD_GATE = CCPD_SW_GATE_NEG ? ~CCPD_PULSE_GATE : CCPD_PULSE_GATE;
assign CCPD_THON = CCPD_SW_THON_NEG ? ~CCPD_PULSE_THON : CCPD_PULSE_THON;

clock_divider #(
    .DIVISOR(40) // 1MHz
) i_clock_divisor_40MHz_to_1kHz (
    .CLK(CLK_40),
    .RESET(1'b0),
    .CE(SPI_CLK_CE),
    .CLOCK(SPI_CLK)
);

tdc_s3
#(
    .BASEADDR(CCPD_TDC_BASEADDR),
    .HIGHADDR(CCPD_TDC_HIGHADDR),
    .CLKDV(4),
    .DATA_IDENTIFIER(4'b0101)
) i_ccpd_tdc (
    .CLK320(RX_CLK2X),
    .CLK160(RX_CLK),
    .DV_CLK(CLK_40),
    .TDC_IN(CCPD_TDC),
    .TDC_OUT(NOT_USED),
	 
    .TRIG_IN(LEMO_RX[0]),
    .TRIG_OUT(TDC_TRIG_OUT),

    .FIFO_READ(CCPD_TDC_FIFO_READ),
    .FIFO_EMPTY(CCPD_TDC_FIFO_EMPTY),
    .FIFO_DATA(CCPD_TDC_FIFO_DATA),

    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .ARM_TDC(CMD_START_FLAG), // arm TDC by sending commands

    .TIMESTAMP(TIMESTAMP[15:0]),
    .EXT_EN(CCPD_PULSE_GATE) 
);

spi // TODO add ext trigger
#(         
    .BASEADDR(CCPD_SPI_BASEADDR), 
    .HIGHADDR(CCPD_SPI_HIGHADDR),
    .MEM_BYTES(356) 
) i_ccpd_spi (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .SPI_CLK(SPI_CLK),
	 .EXT_START(CCPD_PULSE_GATE),

    .SCLK(CCPD_SCLK),
    .SDI(CCPD_SIN),
    .SDO(CCPD_SOUT),
    .SEN(CCPD_SEN),
    .SLD(CCPD_SLD)
);

fast_spi_rx
#(
        .BASEADDR(CCPD_SPI_RX_BASEADDR), 
        .HIGHADDR(CCPD_SPI_RX_HIGHADDR), 
        .IDENTYFIER(4'b0110)
) i_ccpd_fast_spi_rx
(
    .BUS_CLK(BUS_CLK),                     
    .BUS_RST(BUS_RST),                  
    .BUS_ADD(BUS_ADD),                    
    .BUS_DATA(BUS_DATA),                                       
    .BUS_WR(BUS_WR),                    
    .BUS_RD(BUS_RD),
      
    .SCLK(SPI_CLK),
    .SDI(CCPD_SOUT),
    .SEN(CCPD_SEN),

    .FIFO_READ(CCPD_SPI_RX_FIFO_READ),
    .FIFO_EMPTY(CCPD_SPI_RX_FIFO_EMPTY),
    .FIFO_DATA(CCPD_SPI_RX_FIFO_DATA)
);

gpio 
#( 
    .BASEADDR(CCPD_GPIO_SW_BASEADDR),
    .HIGHADDR(CCPD_GPIO_SW_HIGHADDR),
    .IO_WIDTH(8),
    .IO_DIRECTION(8'hff)
) i_gpio_ccpd_sw (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),
    .IO({NC_CCPD_GPIO,CCPD_SW_THON_NEG,CCPD_SW_GATE_NEG,
         CCPD_SW_TEST_HIT,CCPD_SW_HIT,CCPD_SW_LDDAC,CCPD_SW_LDPIX})
);

pulse_gen
#( 
    .BASEADDR(CCPD_PULSE_GATE_BASEADDR), 
    .HIGHADDR(CCPD_PULSE_GATE_HIGHADDR)
) i_pulse_gen_tdcgate (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .PULSE_CLK(SPI_CLK),
    .EXT_START(CCPD_GATE_EXT_START),
    .PULSE(CCPD_PULSE_GATE)

);

pulse_gen
#( 
    .BASEADDR(CCPD_PULSE_INJ_BASEADDR), 
    .HIGHADDR(CCPD_PULSE_INJ_HIGHADDR)
) i_pulse_gen_inj (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .PULSE_CLK(SPI_CLK),
    .EXT_START(CCPD_PULSE_GATE),
    .PULSE(CCPD_INJECTION)
);

 
pulse_gen
#( 
    .BASEADDR(CCPD_PULSE_THON_BASEADDR), 
    .HIGHADDR(CCPD_PULSE_THON_HIGHADDR)
) i_pulse_gen_thon (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .PULSE_CLK(SPI_CLK),
    .EXT_START(CCPD_PULSE_GATE),
    .PULSE(CCPD_PULSE_THON)
);


// Arbiter
wire ARB_READY_OUT, ARB_WRITE_OUT;
wire [31:0] ARB_DATA_OUT;
wire [2:0] READ_GRANT;


rrp_arbiter 
#( 
    .WIDTH(3)
) i_rrp_arbiter
(
    .RST(BUS_RST),
    .CLK(BUS_CLK),

    .WRITE_REQ({~CCPD_TDC_FIFO_EMPTY & CCPD_TDC_SEL, ~CCPD_SPI_RX_FIFO_EMPTY & CCPD_RX_SEL, ~TLU_FIFO_EMPTY & TLU_SEL}),
    .HOLD_REQ({2'b0, TLU_FIFO_PEEMPT_REQ}),
    .DATA_IN({CCPD_TDC_FIFO_DATA,  CCPD_SPI_RX_FIFO_DATA, TLU_FIFO_DATA}),
    .READ_GRANT(READ_GRANT),

    .READY_OUT(ARB_READY_OUT),
    .WRITE_OUT(ARB_WRITE_OUT),
    .DATA_OUT(ARB_DATA_OUT)
);

assign TLU_FIFO_READ = READ_GRANT[0];
assign CCPD_SPI_RX_FIFO_READ = READ_GRANT[1];
assign CCPD_TDC_FIFO_READ = READ_GRANT[2];

// SRAM
wire USB_READ;
assign USB_READ = FREAD & FSTROBE;

sram_fifo 
#(
    .BASEADDR(FIFO_BASEADDR),
    .HIGHADDR(FIFO_HIGHADDR)
) i_out_fifo (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR), 

    .SRAM_A(SRAM_A),
    .SRAM_IO(SRAM_IO),
    .SRAM_BHE_B(SRAM_BHE_B),
    .SRAM_BLE_B(SRAM_BLE_B),
    .SRAM_CE1_B(SRAM_CE1_B),
    .SRAM_OE_B(SRAM_OE_B),
    .SRAM_WE_B(SRAM_WE_B),

    .USB_READ(USB_READ),
    .USB_DATA(FDATA),

    .FIFO_READ_NEXT_OUT(ARB_READY_OUT),
    .FIFO_EMPTY_IN(!ARB_WRITE_OUT),
    .FIFO_DATA(ARB_DATA_OUT),

    .FIFO_NOT_EMPTY(FIFO_NOT_EMPTY),
    .FIFO_FULL(FIFO_FULL),
    .FIFO_NEAR_FULL(FIFO_NEAR_FULL),
    .FIFO_READ_ERROR(FIFO_READ_ERROR)
);
    
// ------- LEDs  ------- //
parameter VERSION = 5; // all on: 31
//wire SHOW_VERSION;
//
//SRLC16E # (
//    .INIT(16'hF000) // in seconds, MSB shifted first
//) SRLC16E_LED (
//    .Q(SHOW_VERSION),
//    .Q15(),
//    .A0(1'b1),
//    .A1(1'b1),
//    .A2(1'b1),
//    .A3(1'b1),
//    .CE(CE_1HZ),
//    .CLK(CLK_40),
//    .D(1'b0)
//);

// LED assignments
assign LED[0] = VERSION[0];
assign LED[1] = VERSION[1];
assign LED[2] = VERSION[2];
assign LED[3] = VERSION[3];
assign LED[4] = VERSION[4];
endmodule
