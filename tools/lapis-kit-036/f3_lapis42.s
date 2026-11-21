.text
.globl _start
_start:
    mov  x0, x19
    adrp x1, ZB
    add  x1, x1, :lo12:ZB
    adrp x2, ZT
    add  x2, x2, :lo12:ZT
    mov  x3, #-1
    bl DC
    cbz  x0, notb
    adrp x1, FL
    ldrb w2, [x1, #0x942]
    add  w2, w2, #1
    strb w2, [x1, #0x942]
    ldrb w3, [x1, #0x944]
    cbz  w3, lend
    mov  x0, x19
    adrp x1, ZB
    add  x1, x1, :lo12:ZB
    adrp x2, ZW
    add  x2, x2, :lo12:ZW
    mov  x3, #-1
    bl   DC
    cbz  x0, nowave
    ldr  w8, [x0, #0x5e4]
    cmp  w8, #0x41
    b.ne nowave
    bl   BS
    mov  w8, #0x7fff
    str  w8, [x0, #0xc0]
nowave:
    adrp x1, FL
    ldrb w4, [x1, #0x945]
    cbz  w4, go
    sub  w4, w4, #1
    strb w4, [x1, #0x945]
    b    lend
go:
    mov  w4, #90
    strb w4, [x1, #0x945]
    stp  x21, x22, [sp, #-0x20]!
    bl   BS
    bl   GE
    cbz  x0, done
    bl   CL
    cbz  x0, done
    ldr  x8, [x0, #0x30]
    ldr  x21, [x8]
    ldr  x22, [x8, #0x10]
loop:
    cmp  x21, #1
    b.lt done
    ldr  x0, [x22], #8
    sub  x21, x21, #1
    cbz  x0, loop
    mov  x20, x0
    ldr  w8, [x0, #0x310]
    cmp  w8, #0xd
    b.eq loop
    cmp  w8, #0xe
    b.eq loop
    mov  x0, x20
    mov  x1, xzr
    bl   SH
    mov  x0, x20
    mov  w1, #0xd
    mov  w2, wzr
    bl CS
    b    loop
done:
    ldp  x21, x22, [sp], #0x20
lend:
    adrp x9, FP
    b BK
notb:
    mov  x0, x19
    adrp x1, ZB
    add  x1, x1, :lo12:ZB
    adrp x2, ZG
    add  x2, x2, :lo12:ZG
    mov  x3, #-1
    bl   DC
    cbnz x0, on
    mov  x0, x19
    adrp x1, ZB
    add  x1, x1, :lo12:ZB
    adrp x2, ZR
    add  x2, x2, :lo12:ZR
    mov  x3, #-1
    bl   DC
    cbnz x0, on
    adrp x1, FL
    strb wzr, [x1, #0x940]
    b    lend
on:
    adrp x1, FL
    mov  w2, #7
    strb w2, [x1, #0x940]
    b    lend
