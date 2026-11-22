    .text
    .globl _start
_start:
    stp x29, x30, [sp, #-64]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #48]
    mov w24, #10
    ldr x8, [x0, #0x620]
    cbz x8, no
    ldr x19, [x8, #0x30]
    cbz x19, no
    ldr w9, [x19]
    cmp w9, w1
    b.le no
    mov w20, w1
    ldr x8, [x19, #0x10]
    ldr x0, [x8, w1, sxtw #3]
    cbz x0, no
    ldr x9, [x0]
    ldr x9, [x9, #0x248]
    blr x9
    udiv w21, w0, w24          // unit family = id / 10 (last digit is the rarity form)
    mov w22, #0
    mov w23, #0
loop:
    ldr w9, [x19]
    cmp w22, w9
    b.ge done
    ldr x8, [x19, #0x10]
    ldr x0, [x8, w22, sxtw #3]
    cbz x0, next
    ldr x9, [x0]
    ldr x9, [x9, #0x248]
    blr x9
    udiv w0, w0, w24
    cmp w0, w21
    b.ne next
    cmp w22, w20
    b.lt no
    add w23, w23, #1
next:
    add w22, w22, #1
    b loop
done:
    bl UUIL                    // count owned units (box and reserves) of the same family
    cbz x0, no
    ldr x19, [x0, #0x30]
    mov w22, #0
own:
    cbz x19, cmpit
    ldr x0, [x19, #0x108]
    ldr x20, [x19, #0x120]
    cbz x0, onext
    ldr x9, [x0]
    ldr x9, [x9, #0x248]
    blr x9
    udiv w0, w0, w24
    cmp w0, w21
    cinc w22, w22, eq
onext:
    mov x19, x20
    b own
cmpit:
    cmp w22, w23
    cset w0, le
    b out
no:
    mov w0, #0
out:
    ldp x23, x24, [sp, #48]
    ldp x21, x22, [sp, #32]
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #64
    ret
