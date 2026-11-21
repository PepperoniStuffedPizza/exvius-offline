    .text
    .globl _start
_start:
stub:
    stp x29, x30, [sp, #-48]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    str x21, [sp, #32]
    mov x19, x0
    mov w20, w1
    ldr x21, [x19, #0x430]
    movz w8, #0x42d0, lsl #16
    fmov s0, w8
    mov x0, x21
    adr x1, n1
    bl shift
    movz w8, #0x42d0, lsl #16
    fmov s0, w8
    mov x0, x21
    adr x1, n2
    bl shift
    movz w8, #0x42d0, lsl #16
    fmov s0, w8
    mov x0, x21
    adr x1, n3
    bl shift
    mov x0, x19
    mov w1, w20
    bl RANGE
    movz w8, #0xc2d0, lsl #16
    fmov s0, w8
    mov x0, x21
    adr x1, n1
    bl shift
    movz w8, #0xc2d0, lsl #16
    fmov s0, w8
    mov x0, x21
    adr x1, n2
    bl shift
    movz w8, #0xc2d0, lsl #16
    fmov s0, w8
    mov x0, x21
    adr x1, n3
    bl shift
    ldr x21, [sp, #32]
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #48
    ret
shift:
    stp x29, x30, [sp, #-64]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    str s8, [sp, #32]
    mov x19, x0
    fmov s8, s0
    add x0, sp, #40
    bl STRCTOR
    mov x0, x19
    add x1, sp, #40
    mov w2, #1
    bl GETOBJ
    mov x19, x0
    ldrb w8, [sp, #40]
    tbz w8, #0, 1f
    ldr x0, [sp, #56]
    bl DELETE
1:  cbz x19, 2f
    ldr s0, [x19, #0x28]
    fadd s0, s0, s8
    str s0, [x19, #0x28]
2:  ldr s8, [sp, #32]
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #64
    ret
n1: .asciz "filter_unit_range_title_bg"
n2: .asciz "filter_unit_range_title"
n3: .asciz "filter_unit_range_btn"
    .balign 4
